"""Grafcet-Studio .grafcet -> Mermaid flowcharts (one per chart).

Topology is not stored explicitly; it is recovered from geometry:
nodes (steps, transitions, jumps) are vertical wire pieces at cx=left+16,
connection lines are wire segments, and touching pieces form nets.

Usage: python3 tools/grafcet2mermaid.py <input.grafcet> <output.md>
Note: the output overwrites the file, including any hand-written intro.
"""
import sys, re, xml.etree.ElementTree as ET
from collections import defaultdict

TOL = 3
STEP_TYPES = {'StepInitial', 'StepNormal', 'StepEnclosing'}


def load(path):
    src = open(path, encoding='utf-8-sig').read().replace('encoding="utf-16"', 'encoding="utf-8"')
    r = ET.fromstring(src)
    titles = [h.findtext('.//Title') for h in r.find('GrafcetsProperties')]
    charts = []
    for title, g in zip(titles, r.find('Grafcets')):
        items = []
        for i in g:
            m = i.find('Margin')
            items.append(dict(
                type=i.findtext('TypeEnum'), cap=(i.findtext('Caption') or '').strip(),
                x=float(m.findtext('Left')), y=float(m.findtext('Top')),
                w=float(i.findtext('Width')), h=float(i.findtext('Height')),
                trans=(i.findtext('TransitionStr') or '').strip(),
                act=(i.findtext('ActionStr') or '').strip(),
                cond=(i.findtext('ConditionStr') or '').strip(),
                hline=i.findtext('IsHorizontalLine') == 'true',
                src=i.findtext('IsSourceTransition') == 'true',
                fin=i.findtext('IsFinalTransition') == 'true',
                start=i.findtext('IsStartStep') == 'true',
                up=i.findtext('IsDirectionToTop') == 'true',
                id=i.findtext('Id')))
        charts.append((title, items))
    return charts


class UF:
    def __init__(s): s.p = {}
    def f(s, a):
        s.p.setdefault(a, a)
        while s.p[a] != a:
            s.p[a] = s.p[s.p[a]]; a = s.p[a]
        return a
    def u(s, a, b): s.p[s.f(a)] = s.f(b)


def analyse(items):
    nodes = [i for i in items if i['type'] in STEP_TYPES | {'Transition', 'Jump'}]
    for n in nodes:
        n['cx'] = n['x'] + 16
        n['bot'] = n['y'] + (32 if n['type'] != 'Transition' else n['h'])
        n['mid'] = (n['y'] + n['bot']) / 2
    vl = [i for i in items if i['type'] == 'ConnectionLine' and not i['hline']]
    hl = [i for i in items if i['type'] == 'ConnectionLine' and i['hline']]
    uf = UF()
    near = lambda a, b: abs(a - b) <= TOL

    def port_at(px, py):
        """Ports a point (px,py) touches: top/bottom lead of a node in that column."""
        out = []
        for k, n in enumerate(nodes):
            if not near(px, n['cx']): continue
            if n['type'] == 'Transition':
                if n['y'] - TOL <= py <= n['mid']: out.append(('t', k))
                elif n['mid'] < py <= n['bot'] + TOL: out.append(('b', k))
            else:
                if near(py, n['y']): out.append(('t', k))
                if near(py, n['bot']) and n['type'] != 'Jump': out.append(('b', k))
        return out

    # node-node abutting
    for a, n in enumerate(nodes):
        for b, m in enumerate(nodes):
            if a != b and near(n['cx'], m['cx']) and n['bot'] - 12 <= m['y'] <= n['bot'] + TOL and n['type'] != 'Jump':
                uf.u(('b', a), ('t', b))
    # vertical lines: endpoints
    for k, l in enumerate(vl):
        for py in (l['y'], l['y'] + l['h']):
            for p in port_at(l['x'], py): uf.u(('v', k), p)
    # horizontal lines: any node column crossing the line at its y
    for k, l in enumerate(hl):
        x1, x2, y = l['x'], l['x'] + l['w'], l['y']
        for n_i, n in enumerate(nodes):
            if x1 - TOL <= n['cx'] <= x2 + TOL:
                for p in port_at(n['cx'], y):
                    if p[1] == n_i: uf.u(('h', k), p)
        for j, v in enumerate(vl):  # T-junctions / corners with vertical lines
            if x1 - TOL <= v['x'] <= x2 + TOL and v['y'] - TOL <= y <= v['y'] + v['h'] + TOL:
                uf.u(('h', k), ('v', j))
    # collinear lines that touch or overlap
    for a, l in enumerate(hl):
        for b, m in enumerate(hl):
            if a < b and near(l['y'], m['y']) and l['x'] <= m['x'] + m['w'] + TOL and m['x'] <= l['x'] + l['w'] + TOL:
                uf.u(('h', a), ('h', b))
    for a, l in enumerate(vl):
        for b, m in enumerate(vl):
            if a < b and near(l['x'], m['x']) and l['y'] <= m['y'] + m['h'] + TOL and m['y'] <= l['y'] + l['h'] + TOL:
                uf.u(('v', a), ('v', b))
    net = lambda p: uf.f(p) if p in uf.p else None
    members = defaultdict(set)
    for k in range(len(nodes)):
        for side in 'tb':
            if (side, k) in uf.p: members[uf.f((side, k))].add((side, k))
    def step_outs(r):  # steps whose bottom (output) is on net r
        return {k for s_, k in members.get(r, ()) if s_ == 'b' and nodes[k]['type'] != 'Transition'}
    def step_ins(r):   # steps/jumps whose top (input) is on net r
        return {k for s_, k in members.get(r, ()) if s_ == 't' and nodes[k]['type'] != 'Transition'}
    edges = set()
    for k, n in enumerate(nodes):
        if n['type'] != 'Transition': continue
        top, bot = net(('t', k)), net(('b', k))
        # direction from what each end touches (the editor's IsDirectionToTop flag is unreliable)
        if len(step_outs(bot)) + len(step_ins(top)) > len(step_outs(top)) + len(step_ins(bot)):
            top, bot = bot, top
        edges |= {(a, k) for a in step_outs(top)} | {(k, b) for b in step_ins(bot)}
    return nodes, edges


def actions_for(items, nodes):
    acts = defaultdict(list)
    steps = [n for n in nodes if n['type'] in STEP_TYPES]
    for a in sorted((i for i in items if i['type'].startswith('Action')), key=lambda a: a['x']):
        acy = a['y'] + 32
        cand = [s for s in steps if abs(s['y'] + 16 - acy) <= 4 and s['x'] < a['x']]
        if cand:
            acts[id(max(cand, key=lambda s: s['x']))].append(a)
    return acts


def names_for(items, nodes):
    names = {}
    for c in items:
        if c['type'] != 'Comment' or not re.fullmatch(r'"[^"\n]+"', c['cap']): continue
        ccy = c['y'] + c['h'] / 2
        cand = [n for n in nodes if n['x'] > c['x'] and n['x'] - c['x'] < 200
                and abs(n['y'] + 16 - ccy) <= 20]
        if cand:
            n = min(cand, key=lambda n: (n['x'] - c['x']) + abs(n['y'] + 16 - ccy))
            names.setdefault(id(n), c['cap'].strip('"'))
    return names


def esc(s):
    return (s.replace('&', '#amp;').replace('"', '#quot;').replace('<', '#lt;')
            .replace('>', '#gt;').replace('\n', ' '))


def fmt_action(a):
    t, x, c = a['type'], a['act'], a['cond']
    if t == 'ActionNormal': return f'N {x}'
    if t == 'ActionConditional': return f'C {x} if {c}'
    if t == 'ActionActivation': return f'↑ {x}'
    if t == 'ActionEvent': return f'⚡ {x}' if c == '1' else f'⚡[{c}] {x}'
    return f'{t} {x}'


def chart_mermaid(title, items, enclosed_by):
    nodes, edges = analyse(items)
    acts, names = actions_for(items, nodes), names_for(items, nodes)
    out = ['flowchart TD']
    nid = {}
    steps_by_num = {}
    for k, n in enumerate(nodes):
        if n['type'] in STEP_TYPES:
            nid[k] = f'S{n["cap"]}'
            steps_by_num[n['cap']] = k
    lines, classes, extra = [], defaultdict(list), []
    for k, n in enumerate(nodes):
        if n['type'] not in STEP_TYPES: continue
        head = n['cap'] + ('*' if n['start'] else '') + (f' · {names[id(n)]}' if id(n) in names else '')
        body = [head]
        if n['type'] == 'StepEnclosing' and enclosed_by.get(n['cap']):
            body.append('⊞ encloses: ' + ', '.join(enclosed_by[n['cap']]))
        body += [fmt_action(a) for a in acts[id(n)]]
        lab = '<br/>'.join(esc(b) for b in body)
        shape = f'[["{lab}"]]' if n['type'] == 'StepInitial' else f'["{lab}"]'
        lines.append(f'  {nid[k]}{shape}')
        if n['type'] == 'StepEnclosing': classes['enclosing'].append(nid[k])
        if n['type'] == 'StepInitial': classes['initial'].append(nid[k])

    def target(b, n):  # resolve jumps to their target steps
        if nodes[b]['type'] == 'Jump':
            num = nodes[b]['cap']
            if num in steps_by_num: return nid[steps_by_num[num]], True
            stub = f'J{num}'
            extra.append(f'  {stub}>"→ step {num}"]')
            return stub, True
        return nid[b], False

    succ, pred = defaultdict(list), defaultdict(list)
    for a, b in edges: succ[a].append(b); pred[b].append(a)
    warnings = []
    for k, t in enumerate(nodes):
        if t['type'] != 'Transition': continue
        cond = esc(t['trans'] or t['cond'])
        ins = [nid[a] for a in pred[k] if a in nid]
        outs = [target(b, nodes[b]) for b in succ[k]]
        if not ins and not t['src']: warnings.append(f'transition {t["trans"]!r} has no input step')
        if not outs and not t['fin']: warnings.append(f'transition {t["trans"]!r} has no output')
        if not ins:
            src = f'SRC{k}'; extra.append(f'  {src}(("start"))'); classes['term'].append(src); ins = [src]
        if not outs:
            fin = f'FIN{k}'; extra.append(f'  {fin}(("end"))'); classes['term'].append(fin); outs = [(fin, False)]
        if len(ins) == 1 and len(outs) == 1:
            o, jump = outs[0]
            lines.append(f'  {ins[0]} {"-.->" if jump else "-->"}|"{cond}"| {o}')
        else:  # synchronisation / simultaneous branches: explicit transition bar
            tn = f'T{k}'
            extra.append(f'  {tn}["{cond}"]'); classes['trans'].append(tn)
            for i in ins: lines.append(f'  {i} --- {tn}')
            for o, jump in outs: lines.append(f'  {tn} {"-.->" if jump else "-->"} {o}')
    out += sorted(set(extra)) + lines
    out += ['  classDef initial stroke-width:4px',
            '  classDef enclosing stroke-dasharray:6 3',
            '  classDef trans fill:#333,color:#fff,stroke:#333',
            '  classDef term fill:#fff,stroke:#888,color:#555']
    for c, ids in classes.items(): out.append(f'  class {",".join(ids)} {c}')
    return '\n'.join(out), warnings


def main():
    charts = load(sys.argv[1])
    enclosed_by = defaultdict(list)
    for title, items in charts:
        for i in items:
            if i['type'] == 'GroupBorder' and i['cap'] not in ('', '-') and title not in enclosed_by[i['cap']]:
                enclosed_by[i['cap']].append(title)
    md = [f'# {sys.argv[1].split("/")[-1]} — GRAFCET as Mermaid', '',
          'Generated from the Grafcet-Studio file. Solid arrows are transitions, dashed arrows are jumps, '
          'dashed boxes are enclosing steps, double boxes are initial steps, '
          '`*` marks a step activated when its enclosing step activates.', '',
          'Action notation: `N` continuous · `C … if cond` conditional · `↑` on step activation · '
          '`⚡` stored on event (event shown in brackets when set).', '']
    allwarn = []
    for title, items in charts:
        groups = [i['cap'] for i in items if i['type'] == 'GroupBorder' and i['cap'] not in ('', '-')]
        enc = f' (enclosed by step {groups[0]})' if groups else ''
        mer, warn = chart_mermaid(title, items, enclosed_by)
        allwarn += [f'{title}: {w}' for w in warn]
        md += [f'## {title}{enc}', '', '```mermaid', mer, '```', '']
    open(sys.argv[2], 'w').write('\n'.join(md))
    for w in allwarn: print('WARN', w, file=sys.stderr)


if __name__ == '__main__':
    main()
