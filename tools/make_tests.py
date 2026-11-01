#!/usr/bin/env python3
"""Generate virtual-time behavioral scenarios for the reviewed translation."""
import json, copy
from pathlib import Path
healthy=dict(EmergencyStop=True,EmergencyStop2=True,Stop=True,AtExit=True)
def step(g=None,n=1,e=None,t=None):
 d={}
 if g:d['given']=g
 d['advance' if t else 'scans']=t or n
 if e:d['expect']=e
 return d
def arm(mode='auto'):
 return [step({**healthy,'AutoSS':mode=='auto','ManualSS':mode=='manual'},e={'MainStep':2}),step({'Reset':True},e={'MainStep':3,'Mode':5 if mode=='auto' else 4}),step({'Reset':False})]
def running():
 return arm()+[step({'IncSpdX100':True,'Start':True}),step({'IncSpdX100':False,'Start':False},t='3.1s',e={'AutoStep':19,'RunningPL':True,'BeltSpeedRef':100})]
tests=[]
def add(name,steps):tests.append(dict(name=name,steps=steps))
add('startup and reset require healthy contacts and clear sensors',[
 step(e={'MainStep':1,'Mode':0,'BeltConveyor4mSpeed':0.0}),
 step(healthy,e={'MainStep':2}),step({'Reset':True,'ClassifyDefuseSensor':True},e={'MainStep':2}),
 step({'ClassifyDefuseSensor':False},e={'MainStep':3}),step({'EmergencyStop2':False},e={'MainStep':1,'Mode':0})])
add('three second warning precedes a half second emitter pulse',arm()+[
 step({'Start':True},e={'AutoStep':20,'Emitter':False}),
 step({'Start':False},t='2.8s',e={'AutoStep':20,'Emitter':False}),
 step(t='240ms',e={'AutoStep':19,'Emitter':True}),step(t='600ms',e={'Emitter':False})])
for name,code,state,counter,act in [('raw',1,24,'RawCounter','RawSorterBeltCW'),('raw green',4,24,'RawCounter','RawSorterBeltCW'),('base',3,27,'BaseCounter','BaseSorterBeltCW'),('base green',6,27,'BaseCounter','BaseSorterBeltCW'),('lid',2,28,'LidCounter','LidSorterBeltCW'),('lid green',5,28,'LidCounter','LidSorterBeltCW')]:
 add('sort '+name,running()+[
 step({'ClassifyDefuseSensor':True,'VisionSensor1':code},e={'AutoStep':22,'BeltSpeedRef':60}),
 step({'SendSortPB':True},e={'AutoStep':state,counter:1,act:True,'BeltSpeedRef':100}),
 step(n=5,e={counter:1}),step({'AtExit':False},e={act:False}),
 step({'AtExit':True,'ClassifyDefuseSensor':False,'SendSortPB':False}),
 step(t='600ms',e={'AutoStep':19,'Emitter':True,counter:1})])
for code in [7,8,9]:
 add('reject metal '+str(code),running()+[
 step({'ClassifyDefuseSensor':True,'VisionSensor1':code}),step(e={'AutoStep':25}),
 step({'RejectDiffuseSensor':True},e={'AutoStep':85,'RejectPusher':True,'BeltSpeedRef':0}),
 step({'RejPushFrontLimit':True},e={'AutoStep':86,'RejectPusher':False}),
 step({'RejPushFrontLimit':False,'RejPushBackLimit':False},n=20,e={'AutoStep':86}),
 step({'RejPushBackLimit':True},e={'AutoStep':19,'BeltSpeedRef':100})])
add('operator reject overrides sort and unknown vision waits',running()+[
 step({'ClassifyDefuseSensor':True,'VisionSensor1':0}),step({'SendSortPB':True},n=5,e={'AutoStep':22}),
 step({'VisionSensor1':1,'SendRejectPB':True},e={'AutoStep':25,'RawCounter':0})])
add('manual edge toggles exclude reverse direction and reset on mode exit',arm('manual')+[
 step({'RawSorterBeltCWManPB':True},e={'RawSorterBeltCW':True}),
 step(n=10,e={'RawSorterBeltCW':True}),
 step({'RawSorterBeltCCWManPB':True},e={'RawSorterBeltCCW':False,'RawSorterBeltCW':True}),
 step({'RawSorterBeltCWManPB':False}),step({'RawSorterBeltCWManPB':True},e={'RawSorterBeltCW':False}),
 step({'RawSorterBeltCCWManPB':False}),step({'RawSorterBeltCCWManPB':True},e={'RawSorterBeltCCW':True}),
 step({'ManualSS':False,'AutoSS':True},e={'RawSorterBeltCCW':False,'Mode':5})])
add('speed increments edges clamp and scale to volts',arm('manual')+[
 step({'BeltConveyor4mManPB':True},e={'BeltSpeedRef':60,'BeltConveyor4mSpeed':2.0}),
 step({'IncSpdX100':True},e={'BeltSpeedRef':160}),step(n=5,e={'BeltSpeedRef':160}),
 step({'IncSpdX100':False}),step({'IncSpdX100':True}),step({'IncSpdX100':False}),
 step({'IncSpdX100':True},e={'BeltSpeedRef':300,'BeltConveyor4mSpeed':10.0}),
 step({'Stop':False},e={'MainStep':2,'Mode':0,'BeltConveyor4mSpeed':0.0})])
add('manual counter reset requires five continuous seconds',arm('manual')+[
 step({'RawCounter':3,'BaseCounter':4,'LidCounter':5,'Reset':True},t='4s',e={'RawCounter':3}),
 step({'Reset':False}),step({'Reset':True},t='4s',e={'BaseCounter':4}),
 step(t='1.1s',e={'RawCounter':0,'BaseCounter':0,'LidCounter':0})])
for contact in ['Stop','EmergencyStop','EmergencyStop2']:
 add(contact+' removes active motion and requires reset',running()+[
 step({'ClassifyDefuseSensor':True,'VisionSensor1':1}),step({'SendSortPB':True},e={'RawSorterBeltCW':True}),
 step({contact:False},e={'Mode':0,'RawSorterBeltCW':False,'Emitter':False,'BeltConveyor4mSpeed':0.0}),
 step({contact:True,'Reset':False},n=5,e={'MainStep':2,'Mode':0})])
add('conflicting selectors disable motion',arm('manual')+[
 step({'RejectPusherManPB':True,'BeltConveyor4mManPB':True},e={'RejectPusher':True}),
 step({'AutoSS':True},e={'Mode':0,'RejectPusher':False,'BeltConveyor4mSpeed':0.0})])
# Execute every behavioral scenario through Main in each language.
base=tests;tests=[]
for language,label in [(1,'ST'),(2,'LD'),(3,'FBD')]:
 for scenario in base:
  scenario=copy.deepcopy(scenario)
  scenario['name']=label+': '+scenario['name']
  scenario['given']={'LanguageSelect':language}
  tests.append(scenario)
for old,new in [(1,2),(2,3),(3,1)]:
 add(f'switch {old} to {new} clears motion, preserves totals and requires reset',[
  step({'LanguageSelect':old,**healthy,'ManualSS':True},e={'MainStep':2}),
  step({'Reset':True},e={'Mode':4}),step({'Reset':False}),
  step({'RawCounter':12,'BaseCounter':13,'LidCounter':14,'BeltConveyor4mManPB':True,'RawSorterBeltCWManPB':True},
       e={'BeltConveyor4mSpeed':2.0,'RawSorterBeltCW':True}),
  step({'LanguageSelect':new},e={'ActiveLanguage':new,'MainStep':1,'Mode':0,'RawSorterBeltCW':False,
       'BeltConveyor4mSpeed':0.0,'RawCounter':12,'BaseCounter':13,'LidCounter':14}),
  step({'BeltConveyor4mManPB':False,'RawSorterBeltCWManPB':False},n=5,e={'MainStep':2,'Mode':0}),
  step({'Reset':True},e={'Mode':4,'BeltConveyor4mSpeed':0.0,'RawSorterBeltCW':False}),
 ])
add('invalid language disables all implementations and can recover',arm('manual')+[
 step({'BeltConveyor4mManPB':True,'RejectPusherManPB':True},e={'BeltConveyor4mSpeed':2.0,'RejectPusher':True}),
 step({'LanguageSelect':99},n=5,e={'LanguageValid':False,'ActiveLanguage':0,'MainStep':1,
      'RejectPusher':False,'BeltConveyor4mSpeed':0.0}),
 step({'LanguageSelect':3},e={'LanguageValid':True,'ActiveLanguage':3,'MainStep':1,'RejectPusher':False}),
 step({'RejectPusherManPB':False,'BeltConveyor4mManPB':False},e={'MainStep':2}),
 step({'Reset':True},e={'Mode':4,'RejectPusher':False}),
])
Path(__file__).resolve().parents[1].joinpath('practicum_test.yaml').write_text(json.dumps({'tolerance':0.001,'tests':tests},indent=2)+'\n')
print(f'Generated {len(tests)} acceptance scenarios.')
