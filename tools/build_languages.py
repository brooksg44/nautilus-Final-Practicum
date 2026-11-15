#!/usr/bin/env python3
"""Translate this project's assignment/IF/CASE ST subset to native LD/FBD.
Rejects unsupported statements. Branch decisions are captured before writes,
so LD/FBD preserve ST's sequential, one-branch-per-IF/CASE semantics.
"""
from pathlib import Path
import argparse
import re
cli=argparse.ArgumentParser(description=__doc__)
# lib/practicum_ld.ld and lib/practicum_fbd.fbd are hand-maintained now: the
# mechanical translation compiles but draws badly (hundreds of naut check
# structure warnings). Only ST is regenerated unless LD/FBD is asked for by
# name, which overwrites the hand-written diagram with the raw translation.
cli.add_argument('--language',choices=['ST','LD','FBD'],action='append',help='Implementation to regenerate (repeatable; default: ST only). LD and FBD overwrite the hand-maintained diagrams in lib/ with the raw mechanical translation')
selected_languages=cli.parse_args().language or ['ST']
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'control.st').read_text()
clean=re.sub(r'\(\*.*?\*\)', '', source, flags=re.S)
header,body=clean.rsplit('END_VAR',1)
header+='END_VAR\n'
body=body.rsplit('END_PROGRAM',1)[0]
# The ST implementation copies the body verbatim, comments included.
commented_body=source.rsplit('END_VAR',1)[1].rsplit('END_PROGRAM',1)[0]
# Comments are tokens so LD/FBD can carry them as diagram notes.
tokens=re.findall(r'\(\*.*?\*\)|:=|<>|>=|<=|[A-Za-z_]\w*|\d+\.\d+|\d+|[;,():+*/=<>-]',commented_body,flags=re.S)
# Do not silently drop unsupported syntax.
if re.sub(r'\s+','',commented_body) != re.sub(r'\s+','',''.join(tokens)):raise ValueError('unsupported token in ST body')
def is_comment(token):return token.startswith('(*')
def comment_text(token):return ' '.join(token[2:-2].split())
class Parser:
 def __init__(self): self.i=0
 def peek(self):return tokens[self.i] if self.i<len(tokens) else ''
 def take(self,w=None):
  t=self.peek()
  if w is not None and t!=w:raise ValueError(f'Expected {w}, got {t} at token {self.i}')
  self.i+=1;return t
 def until(self,end):
  expr=[]
  while self.peek()!=end:
   if not self.peek():raise ValueError('Unterminated expression')
   if is_comment(self.peek()):raise ValueError('Comments inside expressions are not supported')
   expr.append(self.take())
  self.take(end);return re.sub(r'\b(LIMIT)\s+\(', r'\1(', ' '.join(expr))
 def label(self):
  return bool(re.match(r'^\d+$',self.peek()))
 def block(self,ends=(),case=False):
  out=[]
  while self.peek() and self.peek() not in ends and not(case and self.label()):
   t=self.take()
   if is_comment(t):out.append(('comment',comment_text(t)))
   elif t=='IF':
    branches=[(self.until('THEN'),self.block(('ELSIF','ELSE','END_IF')))]
    while self.peek()=='ELSIF':
     self.take();branches.append((self.until('THEN'),self.block(('ELSIF','ELSE','END_IF'))))
    if self.peek()=='ELSE':self.take();branches.append((None,self.block(('END_IF',))))
    self.take('END_IF');self.take(';');out.append(('if',branches))
   elif t=='CASE':
    expr=self.until('OF');branches=[]
    while self.peek()!='END_CASE':
     labels=[self.take()]
     while self.peek()==',':self.take();labels.append(self.take())
     self.take(':');branches.append((labels,self.block(('END_CASE',),case=True)))
    self.take('END_CASE');self.take(';');out.append(('case',expr,branches))
   else:
    if not re.match(r'^[A-Za-z_]\w*$',t):raise ValueError(f'Unsupported statement {t}')
    self.take(':=');out.append(('assign',t,self.until(';')))
  return out
parser=Parser();tree=parser.block()
if parser.i!=len(tokens):raise ValueError('Unconsumed ST')
ops=[];temps={};serial=0
def temporary(typ,prefix):
 global serial
 serial+=1;name=f'{prefix}{serial:03d}';temps[name]=typ;return name
def emit(target,value,guard='TRUE',note=''):ops.append((target,value,guard,note))
# Source comments travel through the passes as note operations: target NOTE,
# value the text, note 'section' for a top-level comment.
NOTE='//'
def is_note(op):return op[0]==NOTE
def lower(nodes,parent='TRUE'):
 for node in nodes:
  if node[0]=='comment':emit(NOTE,node[1],'','section' if parent=='TRUE' else '')
  elif node[0]=='assign':emit(node[1],node[2],parent)
  elif node[0]=='if':
   guards=[]
   for condition,children in node[1]:
    guard=temporary('BOOL','Branch')
    remaining=' AND '.join(f'NOT {x}' for x,_ in guards) or 'TRUE'
    value=f'({parent}) AND ({remaining})'+(f' AND ({condition})' if condition else '')
    emit(guard,value,note='Capture IF decision before branch writes')
    guards.append((guard,children))
   for guard,children in guards:lower(children,guard)
  else:
   value=temporary('INT','CaseValue');emit(value,node[1],parent,'Snapshot CASE selector')
   for labels,children in node[2]:
    guard=temporary('BOOL','CaseBranch')
    cond=' OR '.join(f'({value} = {label})' for label in labels)
    emit(guard,f'({parent}) AND ({cond})',note='Select CASE branch')
    lower(children,guard)
lower(tree)

def inline_decisions(operations, variables):
 """Inline contacts only when their operands stay unchanged until every use.

 Exclude the last consuming operation's target: its RHS/guard is evaluated
 before its target is written. Process definitions in order so substitutions
 expose the remaining guards' real dependencies.
 """
 operations=list(operations);variables=dict(variables)
 for name in list(variables):
  if variables[name]!='BOOL':continue
  pattern=re.compile(r'\b'+re.escape(name)+r'\b')
  index=next(i for i,op in enumerate(operations) if op[0]==name)
  value=operations[index][1]
  uses=[i for i,(t,v,g,_) in enumerate(operations) if i>index and t!=NOTE and (pattern.search(v) or pattern.search(g))]
  dependencies=set(re.findall(r'[A-Za-z_]\w*',value))
  if uses and any(t in dependencies for t,_,_,_ in operations[index+1:max(uses)]):continue
  operations=[op if is_note(op) else (t,pattern.sub(lambda _:f'({value})',v),pattern.sub(lambda _:f'({value})',g),note)
              for i,op in enumerate(operations) if i!=index for t,v,g,note in [op]]
  del variables[name]
 return operations,variables

ld_ops,ld_temps=inline_decisions(ops,temps)
# These are the only decisions whose source operands change before their
# last use in this controller. Give the retained scan snapshots useful names.
snapshot_names={'Branch003':'MainWasEmergency', 'Branch005':'MainWasWaitingForReset',
                'CaseValue019':'AutoStepAtScanStart'}
for old in list(ld_temps):
 new=snapshot_names.get(old)
 if new is None:raise ValueError(f'Name the required ladder snapshot: {old}')
 pattern=re.compile(r'\b'+old+r'\b')
 ld_ops=[op if is_note(op) else (new if t==old else t,pattern.sub(new,v),pattern.sub(new,g),note) for op in ld_ops for t,v,g,note in [op]]
 ld_temps[new]=ld_temps.pop(old)
# Convert top-level Boolean operators to native LD contact function calls.
def strip(expr):
 expr=expr.strip()
 while expr.startswith('(') and expr.endswith(')'):
  depth=0;outer=True
  for i,c in enumerate(expr):
   depth+= (c=='(')-(c==')')
   if depth==0 and i<len(expr)-1:outer=False;break
  if not outer:break
  expr=expr[1:-1].strip()
 return expr
def contact(expr):
 expr=strip(expr)
 for operator,function in [(' OR ','OR'),(' AND ','AND'),(' <> ','NE'),(' >= ','GE'),(' <= ','LE'),(' = ','EQ'),(' > ','GT'),(' < ','LT')]:
  depth=0;i=0
  while i<len(expr):
   c=expr[i]
   if c=='(':depth+=1
   elif c==')':depth-=1
   if depth==0 and expr.startswith(operator,i):
    left,right=expr[:i],expr[i+len(operator):]
    if function in ('AND','OR'):
     left,right=contact(left),contact(right)
     identity,absorbing=('TRUE','FALSE') if function=='AND' else ('FALSE','TRUE')
     if absorbing in (left,right):return absorbing
     if left==identity:return right
     if right==identity or left==right:return left
     return f'{function}({left}, {right})'
    return f'{function}({contact(left)}, {contact(right)})'
   i+=1
 for operators in [[(' + ','ADD'),(' - ','SUB')],[(' * ','MUL'),(' / ','DIV')]]:
  depth=0;matches=[]
  for i,c in enumerate(expr):
   if c=='(':depth+=1
   elif c==')':depth-=1
   if depth==0:
    for operator,function in operators:
     if expr.startswith(operator,i):matches.append((i,operator,function))
  if matches:
   i,operator,function=matches[-1]
   return f'{function}({contact(expr[:i])}, {contact(expr[i+len(operator):])})'
 if expr.startswith('NOT '):return f'NOT({contact(expr[4:])})'
 return expr
def ladder_logic(expr):
 """Simplify Boolean contacts without changing comparison/arithmetic evaluation."""
 def parse(text):
  match=re.fullmatch(r'(AND|OR|NOT)\((.*)\)',text)
  if not match:return text
  op,body=match.groups();args=[];start=depth=0
  for i,c in enumerate(body):
   depth+=(c=='(')-(c==')')
   if c==',' and depth==0:args.append(parse(body[start:i].strip()));start=i+1
  args.append(parse(body[start:].strip()))
  return (op,tuple(args))
 def neg(node):
  if node=='TRUE':return 'FALSE'
  if node=='FALSE':return 'TRUE'
  if isinstance(node,tuple) and node[0]=='NOT':return node[1][0]
  # De Morgan, so a known-false series (or parallel) group is recognised
  # in the negated form a sibling branch spells it.
  if isinstance(node,tuple):return ('OR' if node[0]=='AND' else 'AND',tuple(neg(a) for a in node[1]))
  return ('NOT',(node,))
 def simplify(node,known=frozenset()):
  if node in known:return 'TRUE'
  if neg(node) in known:return 'FALSE'
  if isinstance(node,str):return node
  op,args=node
  if op=='NOT':
   child=simplify(args[0],known)
   if isinstance(child,tuple) and child[0] in ('AND','OR'):
    return simplify(('OR' if child[0]=='AND' else 'AND',tuple(neg(a) for a in child[1])),known)
   return neg(child)
  identity,zero=('TRUE','FALSE') if op=='AND' else ('FALSE','TRUE')
  flat=[]
  for arg in args:
   arg=simplify(arg,known)
   for item in arg[1] if isinstance(arg,tuple) and arg[0]==op else (arg,):
    if item==zero:return zero
    if item!=identity and item not in flat:flat.append(item)
  if any(neg(a) in flat for a in flat):return zero
  # Other series contacts are known true; other parallel legs are known false.
  for i,arg in enumerate(flat):
   facts=frozenset(a if op=='AND' else neg(a) for j,a in enumerate(flat) if i!=j)
   reduced=simplify(arg,known|facts)
   if reduced!=arg:
    return simplify((op,tuple(flat[:i]+[reduced]+flat[i+1:])),known)
  return identity if not flat else flat[0] if len(flat)==1 else (op,tuple(flat))
 def emit(node):
  if isinstance(node,str):return node
  op,args=node
  if op=='NOT':return '/'+emit(args[0])
  if op=='AND':return ' '.join(emit(arg) for arg in args)
  return '[ '+' | '.join(emit(arg) for arg in args)+' ]'
 return emit(simplify(parse(expr)))

def combine_ladder_outputs(lines):
 """Fan out adjacent independent outputs with identical rung power.

 Coils combine with coils and assignments with assignments (coils must end
 the rung). The compiler evaluates shared power once, so never combine when
 an earlier output writes an operand read by that condition or by a later
 assignment's expression.
 """
 result=[];previous=None
 shapes={'coil':re.compile(r'    (.*?) (\( (?:[SR] )?(\w+) \))'),
         'assign':re.compile(r'    (.*?) (\{ (\w+) := (.*) \})')}
 def reads(text,targets):return any(re.search(r'\b'+re.escape(t)+r'\b',text) for t in targets)
 for line in lines:
  if line.startswith('  RUNG '):
   pending=line
   continue
  kind,match=next(((k,m) for k,p in shapes.items() if (m:=p.fullmatch(line))),(None,None))
  if match and previous and previous[0]==kind and len(previous[2])<3 and match[1]==previous[1] \
     and not reads(match[1],previous[2]) and not (kind=='assign' and reads(match[4],previous[2])):
   result[-1]+=' '+match[2]
   previous[2].append(match[3])
  else:
   if line.startswith('    '):result.append(pending)
   result.append(line)
   previous=(kind,match[1],[match[3]]) if match else None
 return result

# Reset each implementation's private locals; shared counters are never reset here.
locals_text=header.split('END_VAR',1)[1]
locals_types={m.group(1):m.group(2) for m in re.finditer(r'(\w+)\s*:\s*(BOOL|REAL|INT)\s*;',locals_text)}
alltypes={m.group(1):m.group(2) for m in re.finditer(r'(\w+)\s*:\s*(BOOL|REAL|INT)\s*;',header)}
reset_ops=[(name,'FALSE' if typ=='BOOL' else '0.0' if typ=='REAL' else '0','ResetState','') for name,typ in locals_types.items()]
reset_note=(NOTE,'Reset private state while ResetState is TRUE; shared totals are kept.','','section')
def note_lines(text,indent):
 """Wrap a source comment into full-line // diagram notes."""
 words=text.split();rows=[];row=''
 for word in words:
  if row and len(row)+1+len(word)>72:rows.append(row);row=word
  else:row=f'{row} {word}'.strip()
 return [f'{indent}// {r}' for r in rows+[row] if r]
def renumber_rungs(lines):
 count=0
 def number(match):
  nonlocal count
  count+=1;return f'  RUNG r{count:03d}_'
 return [re.sub(r'^  RUNG r\d+_',number,line) for line in lines]
for language in selected_languages:
 name='Practicum'+language
 h=header.replace('PROGRAM FinalPracticum','FUNCTION_BLOCK '+name,1)
 h+='VAR_INPUT\n    ResetState : BOOL;\nEND_VAR\n'
 if language=='ST':
  resets='\n'.join(f'    {target} := {value};' for target,value,_,_ in reset_ops)
  result=h+'IF ResetState THEN\n'+resets+'\nELSE\n'+commented_body+'END_IF;\nEND_FUNCTION_BLOCK\n'
 else:
  diagram_ops,diagram_temps=(ld_ops,ld_temps) if language=='LD' else (ops,temps)
  h+='VAR\n'+''.join(f'    {n} : {t};\n' for n,t in diagram_temps.items())+'END_VAR\n'
  lines=[h,language]
  body_ops=[op if is_note(op) else (op[0],op[1],f'NOT ResetState AND ({op[2]})',op[3]) for op in diagram_ops]
  for n,(target,value,guard,note) in enumerate([reset_note]+reset_ops+body_ops,1):
   if target==NOTE:
    # Top-level comments title FBD networks; every comment is a diagram note.
    if language=='FBD' and note=='section':
     title=value.split('.')[0].split(':')[0].strip().replace("'",'')
     lines.append(f"  NETWORK '{title}'")
    lines+=note_lines(value,'  ')
    continue
   value=strip(value)
   if language=='LD':
    lines.append(f'  RUNG r{n:03d}_{target}'+(f' (* {note} *)' if note else ''))
    if alltypes.get(target,diagram_temps.get(target))=='BOOL':
     if value in ('TRUE','FALSE'):
      mode='S' if value=='TRUE' else 'R'
      lines.append(f'    {ladder_logic(contact(guard))} ( {mode} {target} )')
     elif target in diagram_temps:
      lines.append(f'    {ladder_logic(contact(guard+" AND ("+value+")"))} ( {target} )')
     else:
      # A parallel holding path retains the coil when its assignment is disabled.
      power=contact(guard);new_value=contact(value)
      logic=f'OR(AND({power}, {new_value}), AND(NOT({power}), {target}))'
      lines.append(f'    {ladder_logic(logic)} ( {target} )')
    else:
     lines.append(f'    '+ladder_logic(contact(guard))+f' {{ {target} := {value} }}')
   else:
    # BranchNNN names already say what an IF capture is; keep CASE notes.
    if note and not target.startswith('Branch'):lines.append(f'  // {note}')
    lines.append(f'  {target} := SEL({contact(guard)}, {target}, {contact(value)})')
  if language=='LD':lines=renumber_rungs(combine_ladder_outputs(lines))
  lines += ['END_'+language,'END_FUNCTION_BLOCK','']
  result='\n'.join(lines)
 (ROOT/'lib'/f'practicum_{language.lower()}.{language.lower()}').write_text('(* Generated by tools/build_languages.py from control.st. *)\n'+result)
print(f'Generated {", ".join(selected_languages)}: LD has {len(ld_ops)} operations and {len(ld_temps)} named snapshots; FBD has {len(ops)} operations and {len(temps)} temporaries.')
