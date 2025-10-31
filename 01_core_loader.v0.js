/* VHub Unified Core v1.0.6 | Dr.Sadat | MultiProject Sync + AIAdaptive + SecureEmbed + AutoHealer */
;(async()=>{const C={v:"1.0.6",ts:Date.now(),
env:(h=>h.includes("gitlab.io")?"GitLab":h.includes("vortexhub.app")?"Prod":"Local")(location.hostname),
mods:{b:"00_init_boot.v01.js",w:"00_watchdog_monitor.v01.json"},
pths:{r:"./",intel:"./intelligence/",cfg:"./config/"},
partners:[
 "https://vortex-universal-orchestrator-e73281.gitlab.io/",
 "https://panel.vortexhub.app/",
 "https://neonfield-command.vortexhub.app/",
 "https://lifeguard.vortexhub.app/",
 "https://cdn.vortexhub.app/"
],
api:"https://api.vortexhub.app/client-sync",
tele:"https://api.vortexhub.app/telemetry",
authed:!1};
console.log(`[VHub ${C.v}] ${C.env}`);

/* ---- Integrity & Boot Check ---- */
async function chk(f){try{let r=await fetch(C.pths.r+f,{method:"HEAD"});if(!r.ok)throw 0;console.log("OK",f);}catch{console.warn("Missing",f);selfHeal(f);}}
await chk(C.mods.b);await chk(C.mods.w);
(()=>{let s=document.createElement("script");s.src=C.pths.r+C.mods.b;s.defer=!0;document.body.appendChild(s);})();

/* ---- AI Adaptive ClientMesh Sync ---- */
(async()=>{const K="vh_sync_queue",I=2e4;let adapt=I;
async function push(d){let q=JSON.parse(localStorage.getItem(K)||"[]");q.push({...d,ts:Date.now()});if(q.length>8)q.shift();localStorage.setItem(K,JSON.stringify(q));}
async function send(){let q=JSON.parse(localStorage.getItem(K)||"[]");if(!q.length)return;
try{let r=await fetch(C.api,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({batch:q,env:C.env,partners:C.partners})});
if(r.ok){localStorage.setItem(K,"[]");tele({ok:!0,count:q.length});adapt=Math.max(1e4,adapt*0.9);}else adapt=Math.min(6e4,adapt*1.2);}
catch(e){console.warn("SyncRetry",e.message);adapt=Math.min(6e4,adapt*1.4);}}
function loop(){navigator.onLine?send():0;setTimeout(loop,adapt+(Math.random()*2e3));}
window.addEventListener("beforeunload",()=>push({ev:"exit"}));
document.addEventListener("click",()=>push({ev:"click"}));
console.log("[VHubSync] Mesh adaptive loop",adapt);loop();})();

/* ---- Telemetry SmartPing ---- */
function tele(p){try{const d={v:C.v,env:C.env,ts:Date.now(),...p};
navigator.sendBeacon?navigator.sendBeacon(C.tele,JSON.stringify(d)):fetch(C.tele,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)});}
catch(e){console.warn("TeleErr",e.message);}}

/* ---- Self-Heal Across Partner Projects ---- */
async function selfHeal(f){for(const p of C.partners){try{let R=await fetch(p+f);if(R.ok){console.log("[Heal]",p);return true;}}catch{}}
console.warn("HealFail",f);return false;}

/* ---- Region Routing Autoswitch ---- */
(async()=>{try{let r=await fetch(C.pths.cfg+"region-routing.json");if(!r.ok)return;
let j=await r.json();if(j.preferred&&j.map[j.preferred]){C.region=j.preferred;console.log("[Region]",j.preferred,j.map[j.preferred].length);}}
catch(e){console.warn("RegionErr",e.message);}})();

/* ---- SecureEmbed Proxy ---- */
const VEmbed=(()=>{const D={manifest:"/public/manifest.json",region:"/config/region-routing.json",timeout:15e3,allowEval:!1,verbose:!1};
async function j(u){try{let r=await fetch(u);return await r.json();}catch{return{}}}
async function l(o={}){const m=await j(D.manifest),r=await j(D.region);let s=m.sources||[m.bundle];for(const u of s){try{let R=await fetch(u);if(!R.ok)continue;let t=await R.text();
if(D.allowEval)try{new Function(t)();}catch(e){console.warn("EvalErr",e.message);}
else{let sc=document.createElement("script");sc.src=u;sc.defer=!0;document.head.appendChild(sc);}
console.log("[VEmbed]OK",u);tele({event:"embed_load",src:u});return;}
catch(e){console.warn("EmbedFail",u,e.message);}}
tele({event:"embed_fail",src:s});}}
return{load:l}})();window.VEmbed=VEmbed;
})();