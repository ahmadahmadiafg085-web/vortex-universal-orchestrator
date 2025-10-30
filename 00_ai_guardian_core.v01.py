import os,json,hashlib,asyncio,aiohttp,psutil,sqlite3,gzip,platform,websockets,time,pickle
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sklearn.ensemble import IsolationForest
import numpy as np
class GCore:
 def __init__(s,cfg="./config/guardian_config.json"):
  s.v="1.3.3";s.bt=datetime.utcnow().isoformat();s.cf=s._load(cfg);s.h=100;s.a=[];s.t={};s.url=s.cf.get("telemetry_api","https://api.vortexhub.app/guardian")
  s.db="./runtime/g_local.db";s.ex=ThreadPoolExecutor(max_workers=8);s.bh="./backups/h/";s.cl="./runtime/log.cmd";s.l=[];s.hi=s._host();s.ws=s.cf.get("websocket_uri","wss://ws.vortexhub.app/guardian");s.silent=s.cf.get("silent_guard",False)
  s.lat=0;os.makedirs(s.bh,exist_ok=True)
 def _load(s,p):
  try:return json.load(open(p,"r",encoding="utf-8"))
  except:return{"telemetry_api":"","watch_paths":["./runtime","./intelligence"],"auto_heal":True,"backup_sources":["https://cdn1.vortexhub.app/backups/","https://cdn2.vortexhub.net/backups/"],"websocket_uri":"wss://ws.vortexhub.app/guardian"}
 def _host(s):return{"os":platform.system(),"rel":platform.release(),"cpu":psutil.cpu_count(),"mem":round(psutil.virtual_memory().total/1073741824,2),"boot":datetime.fromtimestamp(psutil.boot_time()).isoformat(),"host":platform.node()}
 def _sql_init(s):
  c=sqlite3.connect(s.db);x=c.cursor();x.execute("CREATE TABLE IF NOT EXISTS telemetry(ts TEXT,json TEXT)");c.commit();c.close()
 def _log(s,c,r):
  if s.silent:return
  if os.path.exists(s.cl)and os.path.getsize(s.cl)>5*1024*1024:
   os.makedirs("./backups/logs/",exist_ok=True)
   os.rename(s.cl,f"./backups/logs/log_{int(time.time())}.cmd")
  open(s.cl,"a",encoding="utf-8").write(json.dumps({"t":datetime.utcnow().isoformat(),"c":c,"r":str(r)[:300]})+"\n")
 async def run(s):
  s._sql_init();await s.policy_sync();b=s.scan();s.save_baseline(b);await asyncio.sleep(0.5);t=s.verify(b)
  if t and s.cf.get("auto_heal"):await s.heal(t)
  await s.analyse();s.self_eval();s.meta();await s.tele(adaptive=True);await asyncio.gather(s.wslink(),s.hudlink())
 def scan(s):
  tb={}
  for p in s.cf.get("watch_paths",[]):
   for r,_,fs in os.walk(p):
    for f in fs:
     fp=os.path.join(r,f)
     try:
      with open(fp,"rb")as h:tb[fp]=hashlib.sha256(h.read()).hexdigest()
     except:pass
  s.t=tb;return tb
 def save_baseline(s,b):os.makedirs("./runtime",exist_ok=True);json.dump(b,open("./runtime/integrity_baseline.json","w"))
 def verify(s,b):
  t=[]
  base="./runtime/integrity_baseline.json"
  prev=json.load(open(base)) if os.path.exists(base) else {}
  for f,v in b.items():
   if not os.path.exists(f):t.append(f);continue
   nh=hashlib.sha256(open(f,"rb").read()).hexdigest()
   if nh!=v or prev.get(f)!=nh:t.append(f)
  return t
 async def heal(s,t):
  srcs=s.cf.get("backup_sources",[]);q=asyncio.Queue()
  for f in t:await q.put(f)
  async def w():
   async with aiohttp.ClientSession()as ss:
    while not q.empty():
     f=await q.get();rel=f.replace(os.getcwd(),"").lstrip("/")
     for src in srcs:
      try:
       async with ss.get(src+rel,timeout=10)as r:
        if r.status==200:
         d=await r.read();os.makedirs(os.path.dirname(f),exist_ok=True)
         open(f,"wb").write(d)
         print("[heal]",f,"sha512",hashlib.sha512(d).hexdigest()[:10]);break
      except:await asyncio.sleep(1)
  await asyncio.gather(*[asyncio.create_task(w())for _ in range(min(4,len(t)))])
 async def analyse(s):
  c=psutil.cpu_percent(1);m=psutil.virtual_memory().percent
  s.l.append((datetime.utcnow(),c,m))
  if len(s.l)>20:s.l.pop(0)
  d=np.array([[x[1],x[2]]for x in s.l]);thr=0.1
  if os.path.exists("./runtime/guardian_model.pkl"):
   try:md=pickle.load(open("./runtime/guardian_model.pkl","rb"));thr=md.get("thr",0.12)
   except:pass
  if len(d)>=6:
   try:
    iso=IsolationForest(contamination=thr);p=iso.fit_predict(d)
    if p[-1]==-1:s.a.append({"type":"ml","cpu":c,"mem":m})
   except:pass
  if c>85 or m>90:s.a.append({"type":"over","cpu":c,"mem":m})
  s.lat=round((psutil.net_io_counters().bytes_sent+psutil.net_io_counters().bytes_recv)/1024/1024,2)
  del d;del np
 def policy(s):return"esc"if len(s.a)>2 or s.h<70 else"ok"
 async def policy_sync(s):
  url="https://cdn1.vortexhub.app/policy/guardian_policy.json"
  try:
   async with aiohttp.ClientSession()as ss:async with ss.get(url,timeout=5)as r:
    if r.status==200:open("./config/guardian_policy.json","wb").write(await r.read())
  except:pass
 def self_eval(s):
  if not os.path.exists(s.cl):return
  try:
   l=open(s.cl).readlines()[-20:];s.h=max(60,100-len(l)//3)
  except:pass
 def meta(s):
  os.makedirs("./runtime",exist_ok=True)
  m={"v":s.v,"bt":s.bt,"h":s.h,"a":len(s.a),"hi":s.hi}
  json.dump(m,open("./runtime/m.json","w"))
  if not os.path.exists("./runtime/guardian_model.pkl"):
   pickle.dump({"ver":s.v,"thr":0.1},open("./runtime/guardian_model.pkl","wb"))
 async def tele(s,adaptive=False):
  gap=5
  if adaptive:
   load=(psutil.cpu_percent()+psutil.virtual_memory().percent)/2
   gap=10 if load<50 else 6 if load<70 else 3
  await asyncio.sleep(gap)
  pl={"t":datetime.utcnow().isoformat(),"v":s.v,"h":s.h,"a":s.a,"lat":s.lat}
  d=gzip.compress(json.dumps(pl).encode())
  async with aiohttp.ClientSession()as ss:
   try:await ss.post(s.url,data=d,headers={"Content-Encoding":"gzip"})
   except:pass
 async def wslink(s):
  try:
   async with websockets.connect(s.ws,max_size=2**20,ping_interval=None)as w:
    async def beat():
     while True:
      await asyncio.sleep(15)
      try:await w.ping()
      except:break
    asyncio.create_task(beat());await w.send(json.dumps({"boot":s.bt,"v":s.v}))
    async for msg in w:
     p=json.loads(msg)
     if p.get("cmd"):r=await s.cmd(p["cmd"]);await w.send(json.dumps(r))
  except Exception as e:print("[ws]",e)
 async def hudlink(s):
  uri="wss://ws.vortexhub.app/hud"
  try:
   async with websockets.connect(uri)as w:
    while True:
     await asyncio.sleep(4)
     await w.send(json.dumps({"type":"hud","health":s.h,"a":len(s.a),"t":datetime.utcnow().isoformat()}))
  except:pass
 async def cmd(s,i):
  c=i.lower();r={"st":"ignore"}
  if"scan"in c:r={"scan":len(s.scan())}
  elif"heal"in c:b=s.scan();t=s.verify(b);await s.heal(t);r={"heal":t}
  elif"policy"in c:r={"p":s.policy()}
  elif"tele"in c:await s.tele();r={"tele":"ok"}
  elif"analyze"in c:await s.analyse();r={"a":len(s.a)}
  s._log(i,r);return r
if __name__=="__main__":
 g=GCore();loop=asyncio.get_event_loop();loop.create_task(g.run());loop.run_forever()

