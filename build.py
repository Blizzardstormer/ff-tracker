"""Builds docs/index.html: every tracked Final Fantasy card with art and per-finish owned checkboxes (saved in the browser)."""
import html, json, os, urllib.parse, urllib.request

QUERY = ("e:fin or e:fca or e:pfin or e:tfin or e:rfin or e:fic or e:tfic or e:afic or e:afin or e:pss5 or e:wfin"
         " or (e:sch (cn:39 or cn:40 or cn:41))"
         " or (e:pw25 (cn:2 or cn:4 or cn:16))"
         " or (e:sld ((cn>=1858 cn<=1872) or (cn>=7001 cn<=7008)))")

HDR = {"User-Agent": "ff-tracker/1.0", "Accept": "application/json"}

def fetch_sets(codes):  # set names + icons, so tabs match Scryfall
    req = urllib.request.Request("https://api.scryfall.com/sets", headers=HDR)
    return {s["code"].upper(): {"n": s["name"], "i": s["icon_svg_uri"]}
            for s in json.load(urllib.request.urlopen(req))["data"] if s["code"].upper() in codes}

def fetch_cards():
    url = "https://api.scryfall.com/cards/search?unique=prints&include_extras=true&include_variations=true&order=set&q=" + urllib.parse.quote(QUERY)
    cards = []
    while url:
        req = urllib.request.Request(url, headers=HDR)
        data = json.load(urllib.request.urlopen(req))
        cards += data["data"]
        url = data.get("next_page")
    return cards

def img(c):
    u = c.get("image_uris") or (c.get("card_faces") or [{}])[0].get("image_uris") or {}
    return u.get("normal", "")  # a few extras have no image yet; don't crash the whole build

def tiles(cards):
    seen, out = {}, []
    for c in cards:
        k = f'{c["set"]}-{c["collector_number"]}'
        seen[k] = seen.get(k, 0) + 1  # variations can share a number; keep keys unique
        out.append({"k": k if seen[k] == 1 else f"{k}-v{seen[k]}", "n": c["name"], "s": c["set"].upper(),
                    "c": c["collector_number"], "fin": c.get("finishes") or ["nonfoil"], "i": img(c), "u": c["scryfall_uri"]})
    return out

def moxfield(cards):
    return "".join(f'1 {c["name"]} ({c["set"].upper()}) {c["collector_number"]}\n' for c in cards)

PAGE = """<!doctype html><meta charset=utf-8><meta name=robots content="noindex,nofollow"><meta name=viewport content="width=device-width,initial-scale=1">
<title>FF tracker</title><style>
:root{--bg:#f5f6f8;--sf:#fff;--fg:#1c1e21;--mu:#6b7280;--bd:#e3e5ea;--ac:#4f46e5;--ok:#16a34a;--ic:none;--w:150;color-scheme:light}
:root[data-t=dark]{--bg:#0f1115;--sf:#181b21;--fg:#e7e9ee;--mu:#9aa1ad;--bd:#2a2f38;--ac:#6366f1;--ok:#4ade80;--ic:invert(1);color-scheme:dark}
*{box-sizing:border-box}
body{font:14px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;background:var(--bg);color:var(--fg)}
main{max-width:1400px;margin:0 auto;padding:0 16px 40px}
.hr{display:flex;gap:12px;align-items:baseline}#ss{font-size:12px;color:var(--mu)}.ro .v{cursor:default}
.hd{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:18px 0 8px}h1{font-size:20px;margin:0}
#pc{font-size:15px;font-weight:400;color:var(--mu);font-variant-numeric:tabular-nums}
#pb{height:6px;border-radius:3px;background:var(--bd);overflow:hidden}#pb i{display:block;height:100%;width:0;background:var(--ok);transition:width .3s}
#bar{position:sticky;top:0;z-index:2;background:var(--bg);padding:10px 0;margin-top:8px;border-bottom:1px solid var(--bd);display:flex;flex-wrap:wrap;gap:8px;align-items:center}
#cnt{color:var(--mu);font-weight:500}
select,input:not([type=range]),button,textarea{font:inherit;color:var(--fg);background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:7px 10px}
button{cursor:pointer}button:hover,select:hover{border-color:var(--ac)}
input:focus,select:focus,button:focus-visible{outline:2px solid var(--ac);outline-offset:1px}
input[type=range]{width:120px;padding:0;accent-color:var(--ac)}#vw,#th{display:inline-flex;align-items:center;padding:7px 9px}
#tabs{display:flex;flex-wrap:wrap;gap:6px;width:100%}
.t{font:600 12px ui-monospace,Consolas,monospace;padding:7px 11px;border-radius:999px}
.t.on{background:var(--ac);border-color:var(--ac);color:#fff}
.ic{width:16px;height:16px;vertical-align:-3px;filter:var(--ic)}.t.on .ic{filter:invert(1)}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(calc(var(--w)*1px),1fr));gap:12px;margin-top:14px}
.c{background:var(--sf);border:1px solid var(--bd);border-radius:12px;padding:8px;text-align:center;position:relative;transition:transform .15s,box-shadow .15s}
.c:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.14)}
.c img{width:100%;aspect-ratio:488/680;border-radius:8px;display:block}
.c .n{font-weight:600;margin-top:6px;min-height:2.8em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.c small{color:var(--mu)}.c a{color:inherit;text-decoration:none}
.c{--b:clamp(36px,40cqw,90px);container-type:inline-size;content-visibility:auto;contain-intrinsic-block-size:auto 340px}
.c.own>:not(.ok){opacity:.55;filter:grayscale(1)}
.ok{display:none}
.c.own>.ok{display:block;position:absolute;left:50%;top:calc(8px + 100cqw*.697);transform:translate(-50%,-50%);width:var(--b);height:var(--b);border-radius:50%;border:2px solid rgba(255,255,255,.85);background:rgba(15,17,21,.6) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 12.5l4 4 8-9'/%3E%3C/svg%3E") center/55% no-repeat;backdrop-filter:blur(6px);pointer-events:none}
.vs{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.v{flex:1 1 40%;position:relative;text-align:center;white-space:nowrap;cursor:pointer;padding:6px 2px;border:1px solid var(--bd);border-radius:8px;background:var(--sf);font-size:clamp(9px,7.5cqw,13px);font-weight:600}
.v input{position:absolute;opacity:0;width:0;height:0}.v:focus-within{outline:2px solid var(--ac)}
.v-foil{background:linear-gradient(120deg,#ff9aa2,#ffdf93,#b5ead7,#9ad0f5,#cdb4f6);color:#1c1e21;border-color:transparent}
.v-etched{background:linear-gradient(120deg,#e5e7eb,#9ca3af);color:#1c1e21;border-color:transparent}
.v.on{background:var(--ok);border-color:var(--ok);color:#fff;opacity:.5}.v.on::before{content:"✓ "}
.c details{font-size:12px;margin-top:4px;text-align:left}.c summary{cursor:pointer;color:var(--ac)}.c details a{display:block;padding:2px 0;color:var(--ac)}
.g.list{display:flex;flex-direction:column;gap:6px}
.list .c{display:flex;align-items:center;gap:14px;text-align:left;padding:6px 10px}
.list .c img{width:36px}.list .c>a{flex:none}.list .c>.nm{flex:1}.list .c .n{min-height:0;-webkit-line-clamp:1}
.list .vs{margin:0;width:230px;flex:none}.list .c.own>.ok{position:static;transform:none;width:24px;height:24px;flex:none}.list .c:hover{transform:none;box-shadow:none}
.io{margin-top:24px}.io textarea{width:100%;max-width:520px}
.g.m{grid-template-columns:repeat(var(--n,3),1fr)}
@media(max-width:700px){#bar{position:static}input[type=range]{width:160px}}
.hide{display:none!important}
</style>
<main><div class=hd><h1>Final Fantasy Collection</h1><div class=hr><span id=ss></span><span id=pc></span></div></div><div id=pb><i></i></div>
<div id=bar><div id=tabs></div><b id=cnt></b>
<select id=st><option value="">All</option><option value=m>Missing a version</option><option value=o>Complete</option></select>
<select id=so><option value=n>Number ↑</option><option value=d>Number ↓</option><option value=a>Name A–Z</option></select>
<input id=q placeholder="Search name"><button id=vw></button><button id=th></button><input type=range id=sz min=110 max=300 step=5 title="Card size"></div>
<div class=g id=g></div>
<details class=io><summary>Import / export (Moxfield text)</summary><textarea id=t rows=8></textarea><br>
<button id=ex>Export owned</button> <button id=im>Import (adds to owned)</button></details>
<p><button id=lk></button></p></main>
<script>
const D=__DATA__,SI=__SETS__;
let own=new Set;
const $=id=>document.getElementById(id),g=$("g"),esc=s=>s.replace(/[&<>"]/g,c=>"&#"+c.charCodeAt(0)+";");
const svg=p=>`<svg viewBox="0 0 24 24" width=18 height=18 fill=none stroke=currentColor stroke-width=2 stroke-linecap=round stroke-linejoin=round>${p}</svg>`,
IC={sun:svg('<circle cx=12 cy=12 r=4></circle><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"></path>'),
moon:svg('<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"></path>'),
list:svg('<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"></path>'),
grid:svg('<rect x=3 y=3 width=7 height=7></rect><rect x=14 y=3 width=7 height=7></rect><rect x=14 y=14 width=7 height=7></rect><rect x=3 y=14 width=7 height=7></rect>')};
let th="";try{th=localStorage.getItem("ff-theme")||""}catch(e){}
th=th||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");
const setT=t=>{th=t;document.documentElement.dataset.t=t;$("th").innerHTML=t=="dark"?IC.sun:IC.moon;$("th").title=t=="dark"?"Switch to light mode":"Switch to dark mode"};
$("th").onclick=()=>{setT(th=="dark"?"light":"dark");try{localStorage.setItem("ff-theme",th)}catch(e){}};setT(th);
// Progress lives in docs/owned.json in the repo: everyone can read it, only a browser holding the owner's token can write it.
const REPO="__REPO__",API="https://api.github.com/repos/"+REPO+"/contents/docs/owned.json";
let tok="";try{tok=localStorage.getItem("ff-token")||""}catch(e){}
let owner=!!tok&&!!REPO,sha="",timer=0,busy=0,again=0;
const hdr=()=>({Authorization:"Bearer "+tok,Accept:"application/vnd.github+json"}),say=t=>$("ss").textContent=t;
async function load(){
 try{
  if(owner){const r=await fetch(API,{headers:hdr(),cache:"no-store"});
   if(r.ok){const j=await r.json();sha=j.sha;own=new Set(JSON.parse(atob(j.content.replace(/\\s/g,""))));return draw()}
   if(r.status==404){sha="";return draw()}
   owner=false;try{localStorage.removeItem("ff-token")}catch(e){}say("Owner login expired")}
  const r=await fetch("owned.json?"+Date.now());if(r.ok)own=new Set(await r.json())
 }catch(e){say("Couldn't load progress")}
 draw()}
async function flush(){say("Saving…");
 for(let i=0;i<2;i++){try{
  const r=await fetch(API,{method:"PUT",headers:hdr(),body:JSON.stringify({message:"progress",content:btoa(JSON.stringify([...own].sort())),sha:sha||undefined})});
  if(r.ok){sha=(await r.json()).content.sha;return say("Saved")}
  if(r.status!=409&&r.status!=422)return say("Save failed ("+r.status+")");
  const q=await fetch(API,{headers:hdr(),cache:"no-store"});sha=q.ok?(await q.json()).sha:""
 }catch(e){return say("Save failed – offline?")}}
 say("Save failed – conflict")}
const queue=()=>{say("Unsaved…");clearTimeout(timer);timer=setTimeout(async()=>{if(busy){again=1;return}busy=1;await flush();busy=0;if(again){again=0;queue()}},1500)};
$("lk").onclick=async()=>{
 if(owner){try{localStorage.removeItem("ff-token")}catch(e){}return location.reload()}
 const t=(prompt("Paste your GitHub token (only on your own devices)")||"").trim();if(!t)return;
 const r=await fetch("https://api.github.com/repos/"+REPO,{headers:{Authorization:"Bearer "+t}});
 if(!r.ok)return alert("That token doesn't work for this repo.");
 try{localStorage.setItem("ff-token",t)}catch(e){return alert("This browser can't save the login.")}
 location.reload()};
const ORDER=["FIN","FCA","PFIN","TFIN","RFIN","FIC","TFIC","AFIC","AFIN","PSS5","WFIN","SCH","PW25","SLD"],have=new Set(D.map(d=>d.s)),
sets=[...ORDER.filter(s=>have.has(s)),...[...have].filter(s=>!ORDER.includes(s))],rank=Object.fromEntries(sets.map((s,i)=>[s,i]));let cur="";
$("tabs").innerHTML=["",...sets].map(s=>`<button class=t data-s="${s}" title="${esc((SI[s]||{n:s}).n)}">${(SI[s]||{}).i?`<img class=ic alt="" src="${SI[s].i}"> `:""}${s||"All"}</button>`).join("");
$("tabs").onclick=e=>{const b=e.target.closest(".t");if(b){cur=b.dataset.s;draw()}};
const ST=[["Agora","https://agorahobby.com/store/search?category=mtg&searchfield={q}&search=GO"],
["Hideout","https://hideoutcg.com/search?page=1&q=%2A{q}%2A"],["Cards Citadel","https://cardscitadel.com/search?q=%2A{q}%2A"],
["Arcane Sanctum","https://arcanesanctumtcg.com/search?q={q}&type=product"],
["Mana Pro","https://sg-manapro.com/search?type=product&options%5Bprefix%5D=last&q={q}"],
["Games Haven","https://www.gameshaventcg.com/search?page=1&q=%2A{q}%2A"],
["Hideyoshi","https://hideyoshitcg.com/search?type=product&options%5Bprefix%5D=last&q={q}"],
["OneMTG","https://onemtg.com.sg/search?type=product&options%5Bprefix%5D=last&q={q}"],
["MTGAsia (copies name)","https://mtg-asia.com/"],["TCG Marketplace (copies name)","https://thetcgmarketplace.com/"]];
// shortcut: searches the first face's full name; stores whose search URL can't take a term just open and copy the name
const menu=d=>{const t=d.n.split(" // ")[0];return `<details><summary>Check price</summary>${ST.map(([s,u])=>`<a target=_blank href="${esc(u.replace("{q}",encodeURIComponent(t)))}"${u.includes("{q}")?"":` data-c="${esc(t)}"`}>${s}</a>`).join("")}</details>`};
const FN={nonfoil:"Non-Foil",foil:"Foil",etched:"Etched"},N=D.reduce((a,d)=>a+d.fin.length,0);
g.innerHTML=D.map(d=>`<div class=c><a href="${d.u}" target=_blank><img loading=lazy decoding=async alt="" src="${d.i}"></a><div class=nm><div class=n>${esc(d.n)}</div><small>${d.s} ${d.c}</small></div><div class=vs>${d.fin.map(f=>`<label class="v v-${f}"><input type=checkbox data-f=${f}><span>${FN[f]||f}</span></label>`).join("")}</div>${menu(d)}<i class=ok></i></div>`).join("");
const els=[...g.children];
function draw(){$("im").hidden=!owner;$("lk").textContent=owner?"Log out of owner mode":"Owner login";g.classList.toggle("ro",!owner);let o=0,v=0;const s=cur,st=$("st").value,q=$("q").value.toLowerCase();
els.forEach((e,i)=>{const d=D[i];let all=true;
e.querySelectorAll("input").forEach(x=>{x.disabled=!owner;const h=own.has(d.k+"-"+x.dataset.f);x.checked=h;x.parentNode.classList.toggle("on",h);o+=h;all=all&&h});
e.classList.toggle("own",all);e.querySelector("details").classList.toggle("hide",all);
const show=(!s||d.s==s)&&(!st||(st=="o")==all)&&d.n.toLowerCase().includes(q);e.classList.toggle("hide",!show);v+=show});
[...$("tabs").children].forEach(b=>b.classList.toggle("on",b.dataset.s==cur));
$("pb").firstChild.style.width=100*o/N+"%";$("pc").textContent=(100*o/N).toFixed(1)+"% complete";
$("cnt").textContent=`Owned ${o}/${N} versions · showing ${v} cards`}
g.onclick=e=>{const c=e.target.dataset.c;if(c)try{navigator.clipboard.writeText(c)}catch(x){}};
g.onchange=e=>{if(!owner)return;const k=D[els.indexOf(e.target.closest(".c"))].k+"-"+e.target.dataset.f;e.target.checked?own.add(k):own.delete(k);queue();draw()};
$("st").onchange=draw;$("q").oninput=draw;
const num=(a,b)=>a.c.localeCompare(b.c,undefined,{numeric:true}),
by={n:(a,b)=>rank[a.s]-rank[b.s]||num(a,b),d:(a,b)=>rank[a.s]-rank[b.s]||num(b,a),a:(a,b)=>a.n.localeCompare(b.n)||rank[a.s]-rank[b.s]||num(a,b)};
const sort=()=>g.append(...D.map((_,i)=>i).sort((i,j)=>by[$("so").value](D[i],D[j])).map(i=>els[i]));
$("so").onchange=sort;
const setV=()=>{const l=g.classList.contains("list");$("vw").innerHTML=l?IC.grid:IC.list;$("vw").title=l?"Grid view":"List view";$("sz").hidden=l};
$("vw").onclick=()=>{g.classList.toggle("list");setV()};setV();
const mq=matchMedia("(max-width:700px)"),zk=()=>mq.matches?"ff-cols":"ff-size";
const setZ=()=>{const v=$("sz").value;g.style.setProperty(mq.matches?"--n":"--w",mq.matches?4-v:v)};
function initZ(){const m=mq.matches;g.classList.toggle("m",m);$("sz").min=m?1:110;$("sz").max=m?3:300;$("sz").step=m?1:5;
let v;try{v=localStorage.getItem(zk())}catch(e){}$("sz").value=v||(m?1:150);setZ()}
mq.addEventListener("change",initZ);initZ();
let rz=0;$("sz").oninput=()=>{rz=rz||requestAnimationFrame(()=>{rz=0;setZ()})};
$("sz").onchange=()=>{try{localStorage.setItem(zk(),$("sz").value)}catch(e){}};
$("ex").onclick=()=>$("t").value=D.flatMap(d=>d.fin.filter(f=>own.has(d.k+"-"+f)).map(f=>`1 ${d.n} (${d.s}) ${d.c}${f=="foil"?" *F*":f=="etched"?" *E*":""}`)).join("\\n");
$("im").onclick=()=>{if(!owner)return;$("t").value.split("\\n").forEach(l=>{const m=l.match(/\\((\\w+)\\)\\s+(\\S+)(.*)$/);if(!m)return;
const w=/\\*F\\*/.test(m[3])?"foil":/\\*E\\*/.test(m[3])?"etched":"nonfoil";
const d=D.find(d=>d.s.toLowerCase()==m[1].toLowerCase()&&d.c.toLowerCase()==m[2].toLowerCase());if(d)own.add(d.k+"-"+(d.fin.includes(w)?w:d.fin[0]))});queue();draw()};
$("st").value=owner?"":"m";sort();draw();load();
</script>"""

if __name__ == "__main__":
    cards = fetch_cards()
    os.makedirs("docs", exist_ok=True)
    t = tiles(cards)
    dump = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    page = PAGE.replace("__REPO__", os.environ.get("GITHUB_REPOSITORY", "")).replace("__DATA__", dump(t)).replace("__SETS__", dump(fetch_sets({x["s"] for x in t})))
    open("docs/index.html", "w", encoding="utf-8").write(page)
    if not os.path.exists("docs/owned.json"):
        open("docs/owned.json", "w").write("[]")
    open("docs/cardlist.txt", "w", encoding="utf-8").write(moxfield(cards))
