#!/usr/bin/env python3
"""Render Nautilus's canonical ladder graph to a standalone printable HTML file."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
import textwrap

E = html.escape

def size(el):
    if el['kind'] == 'branch':
        sizes = [seqsize(leg) for leg in el['legs']]
        return max(w for w, h in sizes) + 48, sum(h for w, h in sizes)
    if el['kind'] == 'assign':
        lines = [line for part in el['text'].split(';') for line in textwrap.wrap(part.strip(), 44)]
        return 450, max(70, 26 * len(lines) + 24)
    return 195, 110 if el['kind'] == 'fn' else 88

def seqsize(els):
    sizes = [size(e) for e in els]
    return sum(w for w, h in sizes), max([h for w, h in sizes] or [88])

def wire(x1, y1, x2, y2):
    return f'<path d="M{x1},{y1} L{x2},{y2}" class="wire"/>'

def label(x, y, value, anchor='middle'):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}">{E(value)}</text>'

def draw(el, x, y):
    w, h = size(el)
    cy = y + h / 2
    k = el['kind']
    out = []
    if k == 'branch':
        yy = y
        for leg in el['legs']:
            lw, lh = seqsize(leg)
            ly = yy + lh / 2
            out += [wire(x, cy, x + 16, cy), wire(x + 16, cy, x + 16, ly), wire(x + 16, ly, x + 24, ly)]
            xx = x + 24
            for child in leg:
                cw, ch = size(child)
                out.append(draw(child, xx, ly - ch / 2))
                xx += cw
            out += [wire(xx, ly, x + w - 16, ly), wire(x + w - 16, ly, x + w - 16, cy), wire(x + w - 16, cy, x + w, cy)]
            yy += lh
    elif k in ('contact', 'coil'):
        cx = x + w / 2
        out += [wire(x, cy, cx - 16, cy), wire(cx + 16, cy, x + w, cy), label(cx, cy - 25, el['ref'])]
        if k == 'contact':
            out += [wire(cx - 12, cy - 14, cx - 12, cy + 14), wire(cx + 12, cy - 14, cx + 12, cy + 14)]
            if el.get('neg'): out.append(wire(cx - 18, cy + 18, cx + 18, cy - 18))
        else:
            out.append(f'<path d="M{cx-6},{cy-16} Q{cx-26},{cy} {cx-6},{cy+16} M{cx+6},{cy-16} Q{cx+26},{cy} {cx+6},{cy+16}" class="wire"/>')
            if el.get('mode'): out.append(label(cx, cy + 6, el['mode']))
    elif k in ('fn', 'assign'):
        lines = ([el['fn']] + el.get('args', '').split(', ')) if k == 'fn' else [line for part in el['text'].split(';') for line in textwrap.wrap(part.strip(), 44)]
        bh = 26 * len(lines) + 16
        out += [wire(x, cy, x+10, cy), wire(x+w-10, cy, x+w, cy), f'<rect x="{x+10}" y="{cy-bh/2}" width="{w-20}" height="{bh}"/>']
        for i, line in enumerate(lines): out.append(label(x+w/2, cy-bh/2+25+i*26, line))
    else:
        raise ValueError(f'Unsupported ladder element: {k}')
    return ''.join(out)

def render(rung, index, source_name):
    rows, row, width = [], [], 0
    for el in rung['elements'] + rung['coils']:
        ew, _ = size(el)
        if row and width + ew > 1320:
            rows.append(row)
            row, width = [], 0
        row.append(el)
        width += ew
    if row: rows.append(row)
    heights = [seqsize(row)[1] + 26 for row in rows]
    height = sum(heights) + 20
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 {height}" role="img" aria-label="{E(rung["name"])}">']
    yy = 10
    for n, (row, rh) in enumerate(zip(rows, heights)):
        cy = yy + rh/2
        parts += [wire(28, yy, 28, yy+rh), wire(1372, yy, 1372, yy+rh), wire(28, cy, 40, cy)]
        xx = 40
        for el in row:
            ew, eh = size(el)
            parts.append(draw(el, xx, cy-eh/2))
            xx += ew
        parts.append(wire(xx, cy, 1372, cy))
        if n: parts.append(label(48, yy+14, f'continue {index}.{n}', 'start'))
        if n < len(rows)-1: parts.append(label(1355, yy+rh-4, f'continue {index}.{n+1} →', 'end'))
        yy += rh
    parts.append('</svg>')
    return f'<section><h2>{index:02d} · {E(rung["name"])} <small>{E(source_name)}:{rung["line"]}</small></h2>'+''.join(parts)+'</section>'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', default='main.ld', help='LD file to print (default: main.ld)')
    parser.add_argument('-o', '--output', help='Output HTML path (default: <source>-print.html beside the input)')
    args = parser.parse_args()
    source = Path(args.source).expanduser()
    if not source.is_file():
        parser.error(f'Input file does not exist: {source}')
    output = Path(args.output).expanduser() if args.output else source.with_name(source.stem + '-print.html')
    if output.resolve() == source.resolve():
        parser.error('Output path must differ from the source file')
    graph = json.loads(subprocess.check_output(['naut', 'ld', 'graph', str(source)], text=True))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    body = ''.join(render(r, i, source.name) for i, r in enumerate(graph['rungs'], 1))
    title = E(graph.get('name') or source.stem)
    css = '''@page {size: landscape; margin: 12mm;} *{box-sizing:border-box} body{font:14px Arial,sans-serif;color:#111;background:#e9edf0;margin:0}main{max-width:1420px;margin:24px auto;background:white;padding:28px}h1{font-size:26px;margin:0 0 10px}p{line-height:1.5}h2{font-size:16px;margin:0;padding:10px 0;border-bottom:1px solid #bbb}small{float:right;font-weight:normal;color:#444}section{break-inside:avoid;page-break-inside:avoid;margin:20px 0;border-top:2px solid #333}svg{display:block;width:100%;height:auto}svg text{font:17px monospace;fill:#111}svg rect{fill:white;stroke:#111;stroke-width:1.6}.wire{fill:none;stroke:#111;stroke-width:2}button{padding:10px 18px;font-size:15px;cursor:pointer}@media print{body{background:white}main{max-width:none;margin:0;padding:0}button,.screen{display:none}h1{font-size:22px}section{margin:12px 0}h2{font-size:12px;padding:6px 0}small{font-size:10px}}'''
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title} — Ladder Diagram</title><style>{css}</style></head><body><main><button onclick="window.print()">Print / Save as PDF</button><h1>{title} · Ladder Diagram</h1><p>{len(graph['rungs'])} rungs · Source: {E(source.name)} · SHA-256: {digest}<br>Read top to bottom, left to right. Matching continuation labels join a wrapped rung in series.<br>—| |— TRUE contact · —|/|— FALSE contact · —( )— output coil · comparison boxes pass power when TRUE.<br>Assignment boxes execute with rung power and otherwise retain values. Parallel paths are OR; series elements are AND.</p><p class="screen">Print in landscape at 100% scale. Rungs stay together; browser pagination determines page count.</p>{body}<footer>Generated from Nautilus’s canonical ladder graph. Regenerate after editing {E(source.name)}.</footer></main></body></html>'''
    output.write_text(page)
    print(f'{output}: {len(graph["rungs"])} rungs')

if __name__ == '__main__':
    main()
