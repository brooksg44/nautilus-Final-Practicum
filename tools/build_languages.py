#!/usr/bin/env python3
"""Translate this project's assignment/IF/CASE ST subset to native LD/FBD.
Rejects unsupported statements. Branch decisions are captured before writes,
so LD/FBD preserve ST's sequential, one-branch-per-IF/CASE semantics.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'control.st').read_text()
clean=re.sub(r'\(\*.*?\*\)', '', source, flags=re.S)
header,body=clean.rsplit('END_VAR',1)
header+='END_VAR\n'
body=body.rsplit('END_PROGRAM',1)[0]
tokens=re.findall(r':=|<>|>=|<=|[A-Za-z_]\w*|\d+\.\d+|\d+|[;,():+*/=<>-]',body)
# Do not silently drop unsupported syntax.
if re.sub(r'\s+','',body) != ''.join(tokens):raise ValueError('unsupported token in ST body')
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
   expr.append(self.take())
  self.take(end);return re.sub(r'\b(LIMIT)\s+\(', r'\1(', ' '.join(expr))
 def label(self):
  return bool(re.match(r'^\d+$',self.peek()))
 def block(self,ends=(),case=False):
  out=[]
  while self.peek() and self.peek() not in ends and not(case and self.label()):
   t=self.take()
   if t=='IF':
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
def lower(nodes,parent='TRUE'):
 for node in nodes:
  if node[0]=='assign':emit(node[1],node[2],parent)
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
    if function in ('AND','OR'):return f'{function}({contact(left)}, {contact(right)})'
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
# Reset each implementation's private locals; shared counters are never reset here.
locals_text=header.split('END_VAR',1)[1]
locals_types={m.group(1):m.group(2) for m in re.finditer(r'(\w+)\s*:\s*(BOOL|REAL|INT)\s*;',locals_text)}
alltypes={m.group(1):m.group(2) for m in re.finditer(r'(\w+)\s*:\s*(BOOL|REAL|INT)\s*;',header)}
reset_ops=[(name,'FALSE' if typ=='BOOL' else '0.0' if typ=='REAL' else '0','ResetState','Reset private state') for name,typ in locals_types.items()]
for language in ['ST','LD','FBD']:
 name='Practicum'+language
 h=header.replace('PROGRAM FinalPracticum','FUNCTION_BLOCK '+name,1)
 h+='VAR_INPUT\n    ResetState : BOOL;\nEND_VAR\n'
 if language=='ST':
  resets='\n'.join(f'    {target} := {value};' for target,value,_,_ in reset_ops)
  result=h+'IF ResetState THEN\n'+resets+'\nELSE\n'+body+'END_IF;\nEND_FUNCTION_BLOCK\n'
 else:
  h+='VAR\n'+''.join(f'    {n} : {t};\n' for n,t in temps.items())+'END_VAR\n'
  lines=[h,language]
  for n,(target,value,guard,note) in enumerate(reset_ops+[(t,v,f'NOT ResetState AND ({g})',note) for t,v,g,note in ops],1):
   value=strip(value)
   if language=='LD':
    lines.append(f'  RUNG r{n:03d}_{target}'+(f' (* {note} *)' if note else ''))
    if alltypes.get(target,temps.get(target))=='BOOL':
     # SEL preserves the previous coil value when the branch has no power.
     lines.append(f'    SEL({contact(guard)}, {target}, {contact(value)}) ( {target} )')
    else:
     lines.append(f'    '+('ResetState' if guard=='ResetState' else contact(guard))+f' {{ {target} := {value} }}')
   else:
    if note:lines.append(f"  NETWORK '{n:03d} {note}: {target}'")
    lines.append(f'  {target} := SEL({contact(guard)}, {target}, ({contact(value)}))')
  lines += ['END_'+language,'END_FUNCTION_BLOCK','']
  result='\n'.join(lines)
 (ROOT/'lib'/f'practicum_{language.lower()}.{language.lower()}').write_text('(* Generated by tools/build_languages.py from control.st. *)\n'+result)
print(f'Generated ST/LD/FBD function blocks: {len(ops)} operations, {len(temps)} branch temporaries.')
