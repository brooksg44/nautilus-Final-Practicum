#!/usr/bin/env python3
"""Exercise naut run against a local Modbus TCP test peer (no Factory I/O).
Checks real FC02/04 sensor reads and FC05/06 actuator writes, including scale.
"""
import argparse, csv, re, shutil, socket, struct, subprocess, tempfile, threading, time
from pathlib import Path
cli=argparse.ArgumentParser()
cli.add_argument('--language',type=int,choices=[1,2,3],default=1)
args=cli.parse_args()
ROOT=Path(__file__).resolve().parents[1]
rows={r['symbol']:r for r in csv.DictReader((ROOT/'io_map.csv').open())}
inputs={}; coils={}; holding={}; functions=set(); stop=threading.Event()
def sensor(name,value): inputs[int(rows[name]['pdu_address'])]=value
def exact(c,n):
 data=b''
 while len(data)<n:
  chunk=c.recv(n-len(data))
  if not chunk: raise EOFError
  data+=chunk
 return data
listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen();listener.settimeout(.1)
port=listener.getsockname()[1]
def serve():
 while not stop.is_set():
  try:c,_=listener.accept()
  except socket.timeout:continue
  c.settimeout(.2)
  with c:
   while not stop.is_set():
    try:
     hdr=exact(c,7);tid,proto,length,unit=struct.unpack('>HHHB',hdr)
     pdu=exact(c,length-1);fc=pdu[0];functions.add(fc)
     address,value=struct.unpack('>HH',pdu[1:5])
     if fc in (1,2):
      source=inputs if fc==2 else coils
      bits=bytearray((value+7)//8)
      for i in range(value):
       if source.get(address+i,False):bits[i//8]|=1<<(i%8)
      reply=bytes([fc,len(bits)])+bits
     elif fc in (3,4):
      vals=[holding.get(address+i,0) if fc==3 else 0 for i in range(value)]
      reply=bytes([fc,2*value])+struct.pack('>'+'H'*value,*vals)
     elif fc in (5,6):
      (coils if fc==5 else holding)[address]=bool(value) if fc==5 else value
      reply=pdu
     elif fc in (15,16):
      for i in range(value):
       if fc==15:coils[address+i]=bool(pdu[6+i//8] & (1<<(i%8)))
       else:holding[address+i]=struct.unpack('>H',pdu[6+2*i:8+2*i])[0]
      reply=pdu[:5]
     else:reply=bytes([fc|128,1])
     c.sendall(struct.pack('>HHHB',tid,proto,len(reply)+1,unit)+reply)
    except socket.timeout:continue
    except (EOFError,OSError):break
thread=threading.Thread(target=serve,daemon=True);thread.start()
def wait_for(pred,description):
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  if pred():return
  if proc.poll() is not None: raise AssertionError('naut exited: '+logpath.read_text())
  time.sleep(.02)
 raise AssertionError('Timed out: '+description+'\n'+logpath.read_text())
def reg(name):return holding.get(int(rows[name]['pdu_address']))
def coil(name):return coils.get(int(rows[name]['pdu_address']))
try:
 with tempfile.TemporaryDirectory(prefix='practicum-smoke-') as tmp:
  project=Path(tmp)
  for name in ['nautilus.yaml','main.st','control.st','tags','lib','modbus_manifest.yaml']:
   src=ROOT/name
   if src.is_dir():shutil.copytree(src,project/name)
   else:shutil.copy(src,project/name)
  p=project/'modbus_manifest.yaml';p.write_text(re.sub(r'host: [^,}]+', 'host: 127.0.0.1', re.sub(r'port: \d+', f'port: {port}', p.read_text())))
  p=project/'nautilus.yaml';p.write_text(p.read_text().replace('127.0.0.1:8080','127.0.0.1:0').replace('name: LanguageSelect, role: setpoint, type: INT, init: 1',f'name: LanguageSelect, role: setpoint, type: INT, init: {args.language}'))
  for name in ['EmergencyStop','EmergencyStop2','Stop','AtExit','ManualSS']:sensor(name,True)
  logpath=project/'run.log'
  with logpath.open('w') as log:
   proc=subprocess.Popen(['naut','run',str(project)],stdout=log,stderr=log)
   try:
    wait_for(lambda:2 in functions and 4 in functions,'sensor polling')
    sensor('Reset',True)
    wait_for(lambda:coil('ManualPL') is True,'reset enables manual mode')
    sensor('Reset',False);sensor('BeltConveyor4mManPB',True)
    wait_for(lambda:reg('BeltConveyor4mSpeed')==200 and reg('BeltConveyor4mSpeed2')==200,'60 cm/s maps to 2 V = 200 raw')
    sensor('RawSorterBeltCWManPB',True)
    wait_for(lambda:coil('RawSorterBeltCW') is True,'manual conveyor output')
    sensor('EmergencyStop2',False)
    wait_for(lambda:reg('BeltConveyor4mSpeed')==0 and coil('RawSorterBeltCW') is False,'emergency stop clears outputs')
    print(f'PASS language {args.language}: real Modbus TCP sensor reads, mapped coil writes, voltage scaling, emergency stop. FCs:',sorted(functions))
   finally:
    proc.terminate()
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()
finally:
 stop.set();thread.join(timeout=1);listener.close()
