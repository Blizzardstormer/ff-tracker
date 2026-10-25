"""Builds docs/index.html: every tracked Final Fantasy card with art and per-finish owned checkboxes (saved in the browser)."""
import html, json, os, urllib.parse, urllib.request

QUERY = ("e:fin or e:fca or e:pfin or e:tfin or e:rfin or e:fic or e:tfic or e:afic or e:afin or e:pss5 or e:wfin"
         " or (e:pmei (" + " or ".join(f'cn:"{c}"' for c in ['2027-1', '2026-3', '2026-17', '2025-11', '2025-12', '2025-13', '2025-14', '2025-21', '2025-26']) + "))"
         " or (e:sch (cn:39 or cn:40 or cn:41))"
         " or (e:pw25 (cn:2 or cn:4 or cn:16))"
         " or (e:sld ((cn>=1858 cn<=1872) or (cn>=7001 cn<=7008)))")

HDR = {"User-Agent": "ff-tracker/1.0", "Accept": "application/json"}

def query():  # extra.txt (optional): more Scryfall searches, one per line; "#" lines are comments
    extra = [l.strip() for l in open("extra.txt", encoding="utf-8")] if os.path.exists("extra.txt") else []
    return QUERY + "".join(f" or ({l})" for l in extra if l and not l.startswith("#"))

def fetch_sets(codes):  # set names + icons, so tabs match Scryfall
    req = urllib.request.Request("https://api.scryfall.com/sets", headers=HDR)
    return {s["code"].upper(): {"n": s["name"], "i": s["icon_svg_uri"]}
            for s in json.load(urllib.request.urlopen(req))["data"] if s["code"].upper() in codes}

def fetch_cards():
    url = "https://api.scryfall.com/cards/search?unique=prints&include_extras=true&include_variations=true&order=set&q=" + urllib.parse.quote(query())
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

TOKEN_SETS = {"tfin", "tfic", "wfin"}
TOKEN_LAYOUTS = {"token", "double_faced_token", "emblem"}
SUSPECT_SETS = {"fin", "fic", "fca", "pfin"}  # surge foils live here; foil-only cards Scryfall didn't tag get listed for checking

def kind(c):  # Type filter: art cards, scene box, tokens (these have no rarity chip)
    if c["set"] == "afin" or c.get("layout") == "art_series":
        return "ar"
    if c["set"] == "afic":
        return "sb"
    if c["set"] in TOKEN_SETS or c.get("layout") in TOKEN_LAYOUTS:
        return "tk"
    return ""

def rarity(c):
    return "" if kind(c) else {"common": "c", "uncommon": "u", "rare": "r", "mythic": "m", "special": "s", "bonus": "b"}.get(c.get("rarity"), "")

def surge_override():  # surge.txt (optional): lines like "fin 580" force the Surge Foil label
    if not os.path.exists("surge.txt"):
        return set()
    return {tuple(l.lower().split()[:2]) for l in open("surge.txt", encoding="utf-8") if l.strip() and not l.startswith("#")}

def is_surge(c, ov):
    return "surgefoil" in (c.get("promo_types") or []) or (c["set"], c["collector_number"].lower()) in ov

def tiles(cards):
    seen, out, ov = {}, [], surge_override()
    for c in cards:
        k = f'{c["set"]}-{c["collector_number"]}'
        seen[k] = seen.get(k, 0) + 1  # variations can share a number; keep keys unique
        out.append({"k": k if seen[k] == 1 else f"{k}-v{seen[k]}", "n": c["name"], "s": c["set"].upper(),
                    "c": c["collector_number"], "fin": c.get("finishes") or ["nonfoil"], "i": img(c), "u": c["scryfall_uri"],
                    "ci": "".join(c.get("color_identity") or []),
                    "r": rarity(c), "ty": kind(c), "sg": int(is_surge(c, ov))})
    return out

def moxfield(cards):
    return "".join(f'1 {c["name"]} ({c["set"].upper()}) {c["collector_number"]}\n' for c in cards)

PAGE = """<!doctype html><meta charset=utf-8><meta name=robots content="noindex,nofollow"><meta name=viewport content="width=device-width,initial-scale=1">
<title>FF tracker</title><style>
:root{--bg:#f5f6f8;--sf:#fff;--fg:#1c1e21;--mu:#6b7280;--bd:#e3e5ea;--ac:#4f46e5;--ok:#16a34a;--ic:none;--w:150;--gold:#d9a400;color-scheme:light}
:root[data-t=dark]{--bg:#0f1115;--sf:#181b21;--fg:#e7e9ee;--mu:#9aa1ad;--bd:#2a2f38;--ac:#6366f1;--ok:#4ade80;--ic:invert(1);--gold:#facc15;color-scheme:dark}
*{box-sizing:border-box}
body{font:14px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;background:var(--bg);color:var(--fg)}
main{max-width:1400px;margin:0 auto;padding:0 16px 40px}
#ss{font-size:12px;color:var(--mu)}.ro .v{cursor:default}
.hd{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:18px 0 8px}h1{font-size:20px;margin:0}
.bars{display:flex;gap:16px}.bb{flex:1;min-width:0}
.bt{display:flex;justify-content:space-between;gap:8px;font-size:13px;color:var(--mu);margin-bottom:4px;white-space:nowrap}.bt b{font-weight:400;color:var(--fg)}
.pb{height:6px;border-radius:3px;background:var(--bd);overflow:hidden}.pb i{display:block;height:100%;width:0;background:var(--ok);transition:width .3s}.pb.gm i{background:var(--gold)}
#qr{display:flex;gap:6px;position:relative}#q{flex:1;min-width:0}
#fb{display:inline-flex;align-items:center;gap:6px;padding:7px 9px}#fi{display:inline-flex}
#fc{background:var(--ac);color:#fff;border-radius:999px;font-size:11px;min-width:18px;padding:0 5px;text-align:center}
#fp{position:absolute;top:calc(100% + 6px);left:0;z-index:5;width:300px;max-width:92vw;background:var(--sf);border:1px solid var(--bd);border-radius:12px;padding:12px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.fl{font-size:12px;color:var(--mu);margin:8px 0 6px}.fr{display:flex;flex-wrap:wrap;gap:6px}
.ch{padding:6px 10px;border-radius:999px;display:inline-flex;align-items:center}.ch img{width:18px;height:18px}
.ch.on{background:var(--ac);border-color:var(--ac);color:#fff}#fx{margin-top:12px}
#bar{position:sticky;top:0;z-index:2;background:var(--bg);padding:10px 0;margin-top:8px;border-bottom:1px solid var(--bd);display:flex;flex-wrap:wrap;gap:8px;align-items:center}
#cnt{color:var(--mu);font-weight:500}
select,input:not([type=range]),button,textarea{font:inherit;color:var(--fg);background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:7px 10px}
button{cursor:pointer}button:hover,select:hover{border-color:var(--ac)}
input:focus,select:focus,button:focus-visible{outline:2px solid var(--ac);outline-offset:1px}
input[type=range]{width:120px;padding:0;accent-color:var(--ac)}#vw,#th{display:inline-flex;align-items:center;padding:7px 9px}
#tabs{display:flex;flex-wrap:wrap;gap:6px;width:100%}
.t{font:600 12px ui-monospace,Consolas,monospace;padding:7px 11px;border-radius:999px;display:inline-flex;align-items:center;gap:6px}.t svg{width:16px;height:16px;fill:currentColor}
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
.c.part{border-color:var(--ok);box-shadow:0 0 0 1px var(--ok)}
.ok{display:none}
.c.own>.ok{display:block;position:absolute;left:50%;top:calc(8px + 100cqw*.697);transform:translate(-50%,-50%);width:var(--b);height:var(--b);border-radius:50%;border:2px solid rgba(255,255,255,.85);background:rgba(15,17,21,.6) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 12.5l4 4 8-9'/%3E%3C/svg%3E") center/55% no-repeat;backdrop-filter:blur(6px);pointer-events:none}
.vs{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.v{flex:1 1 40%;position:relative;text-align:center;white-space:nowrap;cursor:pointer;padding:6px 2px;border:1px solid var(--bd);border-radius:8px;background:var(--sf);font-size:clamp(9px,7.5cqw,13px);font-weight:600}
.v input{position:absolute;opacity:0;width:0;height:0}.v:focus-within{outline:2px solid var(--ac)}
.v-foil{background:linear-gradient(120deg,#ff9aa2,#ffdf93,#b5ead7,#9ad0f5,#cdb4f6);color:#1c1e21;border-color:transparent}
.v-surge{background:linear-gradient(120deg,#00e5ff,#5b8cff,#c04bff,#ff3df2);color:#fff;border-color:transparent;text-shadow:0 1px 2px rgba(0,0,0,.45);box-shadow:0 0 8px rgba(0,229,255,.55)}
.v-etched{background:linear-gradient(120deg,#e5e7eb,#9ca3af);color:#1c1e21;border-color:transparent}
.v.on{background:var(--ok);border-color:var(--ok);color:#fff;opacity:.5;text-shadow:none;box-shadow:none}.v.on::before{content:"✓ "}
.c details{font-size:12px;margin-top:4px;text-align:left}.c summary{cursor:pointer;color:var(--ac)}.c details a{display:block;padding:2px 0;color:var(--ac)}
.g.list{display:flex;flex-direction:column;gap:6px}
.list .c{display:flex;align-items:center;gap:14px;text-align:left;padding:6px 10px}
.list .c img{width:36px}.list .c>a{flex:none}.list .c>.nm{flex:1}.list .c .n{min-height:0;-webkit-line-clamp:1}
.list .vs{margin:0;width:230px;flex:none}.list .c.own>.ok{position:static;transform:none;width:24px;height:24px;flex:none}.list .c:hover{transform:none;box-shadow:none}.list .c.part{box-shadow:none;border-left:4px solid var(--ok)}
.io{margin-top:24px}.io textarea{width:100%;max-width:520px}
.g.m{grid-template-columns:repeat(var(--n,3),1fr)}
#sk,#ctl{display:contents}#qr,#vw,#th,#sz{order:1}
.ro .c details{display:none}
@media(max-width:700px){
#bar{display:contents}
#sk{position:sticky;top:0;z-index:2;display:flex;flex-direction:column;gap:6px;background:var(--bg);padding:8px 0;margin-top:8px;border-bottom:1px solid var(--bd)}
#tabs{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}#tabs::-webkit-scrollbar{display:none}
.t{padding:6px 9px;flex:none}#qr{width:100%;order:0}#q{padding:6px 10px}.cn{display:none}#fp{right:0;width:auto}
#ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 0}#qr,#vw,#th,#sz{order:0}
input[type=range]{width:160px}}
#rs{font-size:12px;color:var(--mu)}
#up{position:fixed;right:16px;bottom:16px;z-index:3;width:44px;height:44px;padding:0;border-radius:50%;display:grid;place-items:center;box-shadow:0 4px 14px rgba(0,0,0,.3)}
.wl{position:absolute;top:12px;right:12px;z-index:1;display:grid;place-items:center;width:30px;height:30px;padding:0;border-radius:50%;border:1px solid rgba(255,255,255,.5);background:rgba(15,17,21,.55);color:#fff;backdrop-filter:blur(4px);cursor:pointer}
.c.w .wl{color:#facc15}.c.w .wl svg{fill:currentColor}.ro .c:not(.w) .wl{display:none}.ro .wl{pointer-events:none}
.list .wl{position:static;width:24px;height:24px;flex:none}#mp{text-align:center;margin:18px 0}
.hide{display:none!important}
</style>
<main><div class=hd><h1>Final Fantasy Collection</h1><span id=ss></span></div>
<div class=bars><div class=bb title="Every card number, either finish"><div class=bt><span>Master set</span><span id=mt></span></div><div class=pb><i id=mb></i></div></div>
<div class=bb title="Every foil and non-foil version"><div class=bt><span>Grandmaster</span><span id=gt></span></div><div class="pb gm"><i id=gb></i></div></div></div>
<div id=bar><div id=sk><div id=tabs></div><div id=qr><input id=q placeholder="Search name"><button id=fb title="Filter"><i id=fi></i><span id=fc class=hide></span></button>
<div id=fp hidden><div class=fl>Colour identity</div><div class=fr><button class=ch data-c=W title=White><img alt=W src="https://svgs.scryfall.io/card-symbols/W.svg"></button><button class=ch data-c=U title=Blue><img alt=U src="https://svgs.scryfall.io/card-symbols/U.svg"></button><button class=ch data-c=B title=Black><img alt=B src="https://svgs.scryfall.io/card-symbols/B.svg"></button><button class=ch data-c=R title=Red><img alt=R src="https://svgs.scryfall.io/card-symbols/R.svg"></button><button class=ch data-c=G title=Green><img alt=G src="https://svgs.scryfall.io/card-symbols/G.svg"></button><button class=ch data-c=C title=Colourless><img alt=C src="https://svgs.scryfall.io/card-symbols/C.svg"></button></div>
<div class=fl>Rarity</div><div class=fr><button class=ch data-r=c>Common</button><button class=ch data-r=u>Uncommon</button><button class=ch data-r=r>Rare</button><button class=ch data-r=m>Mythic</button><button class=ch data-r=s>Special</button><button class=ch data-r=b>Bonus</button></div>
<div class=fl>Finish</div><div class=fr><button class=ch data-f=n>Non-Foil</button><button class=ch data-f=f>Foil</button><button class=ch data-f=s>Surge Foil</button></div>
<div class=fl>Type</div><div class=fr><button class=ch data-y=tk>Tokens</button><button class=ch data-y=ar>Art cards</button><button class=ch data-y=sb>Scene Box</button></div>
<button id=fx>Clear</button></div></div></div>
<div id=ctl><b id=cnt></b>
<select id=st><option value="">All</option><option value=n>Needed</option><option value=p>Have one finish</option><option value=b>Both finishes</option></select>
<select id=so><option value=n>Number ↑</option><option value=d>Number ↓</option><option value=a>Name A–Z</option></select>
<button id=vw></button><button id=th></button><input type=range id=sz min=110 max=300 step=5 title="Card size"></div></div>
<div class=g id=g></div>
<p id=mp hidden><button id=more>Show everything I'm still missing</button></p>
<details class=io id=io><summary>Import / export (Moxfield text)</summary><textarea id=t rows=8></textarea><br>
<button id=ex>Export owned</button> <button id=im>Import pasted text</button> <input type=file id=fl accept=".csv,.txt"><p id=rs>Import adds to what you own; it never removes anything. Accepts a ManaBox CSV or Moxfield text.</p>
<hr><button id=rs0>Reset collection to 0 (debug)</button></details>
<p><button id=lk></button></p><button id=up class=hide title="Back to top"></button></main>
<script>
const D=__DATA__,SI=__SETS__;
let own=new Set,want=new Set;
const $=id=>document.getElementById(id),g=$("g"),esc=s=>s.replace(/[&<>"]/g,c=>"&#"+c.charCodeAt(0)+";");
const svg=p=>`<svg viewBox="0 0 24 24" width=18 height=18 fill=none stroke=currentColor stroke-width=2 stroke-linecap=round stroke-linejoin=round>${p}</svg>`,
IC={sun:svg('<circle cx=12 cy=12 r=4></circle><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"></path>'),
moon:svg('<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"></path>'),
list:svg('<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"></path>'),
star:svg('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>'),
up:svg('<path d="M12 19V5M5 12l7-7 7 7"></path>'),
filter:svg('<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>'),
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
const take=j=>{if(Array.isArray(j))own=new Set(j);else{own=new Set(j.o||[]);want=new Set(j.w||[])}};
async function load(){
 try{
  if(owner){const r=await fetch(API,{headers:hdr(),cache:"no-store"});
   if(r.ok){const j=await r.json();sha=j.sha;take(JSON.parse(atob(j.content.replace(/\\s/g,""))));return draw()}
   if(r.status==404){sha="";return draw()}
   owner=false;try{localStorage.removeItem("ff-token")}catch(e){}say("Owner login expired")}
  const r=await fetch("owned.json?"+Date.now());if(r.ok)take(await r.json())
 }catch(e){say("Couldn't load progress")}
 if(!owner&&want.size)cur="*";draw()}
async function flush(){say("Saving…");
 for(let i=0;i<2;i++){try{
  const r=await fetch(API,{method:"PUT",headers:hdr(),body:JSON.stringify({message:"progress",content:btoa(JSON.stringify({o:[...own].sort(),w:[...want].sort()})),sha:sha||undefined})});
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
const ORDER=["FIN","FCA","PFIN","TFIN","RFIN","FIC","TFIC","AFIC","AFIN","PSS5","WFIN","PMEI","SCH","PW25","SLD"],have=new Set(D.map(d=>d.s)),
sets=[...ORDER.filter(s=>have.has(s)),...[...have].filter(s=>!ORDER.includes(s))],rank=Object.fromEntries(sets.map((s,i)=>[s,i]));let cur="";
$("tabs").innerHTML=["","*",...sets].map(s=>`<button class=t data-s="${s}" title="${s=="*"?"Cards I'm looking for":esc((SI[s]||{n:s}).n)}">${s=="*"?IC.star+" Wishlist":`${(SI[s]||{}).i?`<img class=ic alt="" src="${SI[s].i}"> `:""}${s||"All"}`}</button>`).join("");
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
const FN={nonfoil:"Non-Foil",foil:"Foil",etched:"Etched"},fc=new Set,fr=new Set,ff=new Set,fy=new Set;
g.innerHTML=D.map(d=>`<div class=c><a href="${d.u}" target=_blank><img loading=lazy decoding=async alt="" src="${d.i}"></a><div class=nm><div class=n>${esc(d.n)}</div><small>${d.s} ${d.c}</small></div><div class=vs>${d.fin.map(f=>`<label class="v v-${f}${d.sg&&f=="foil"?" v-surge":""}"><input type=checkbox data-f=${f}><span>${d.sg&&f=="foil"?"Surge Foil":FN[f]||f}</span></label>`).join("")}</div>${menu(d)}<i class=ok></i><button class=wl title="Wishlist">${IC.star}</button></div>`).join("");
const els=[...g.children];
function draw(){$("io").hidden=!owner;$("im").hidden=$("fl").hidden=!owner;$("lk").textContent=owner?"Log out of owner mode":"Owner login";g.classList.toggle("ro",!owner);let m=0,gm=0,v=0;const s=cur,st=$("st").value,q=$("q").value.toLowerCase();
els.forEach((e,i)=>{const d=D[i];let c0=0;
e.querySelectorAll("input").forEach(x=>{x.disabled=!owner;const h=own.has(d.k+"-"+x.dataset.f);x.checked=h;x.parentNode.classList.toggle("on",h);c0+=h});
const all=c0==d.fin.length,part=c0>0&&!all;m+=c0>0;gm+=c0;
e.classList.toggle("own",all);e.classList.toggle("part",part);e.classList.toggle("w",want.has(d.k));e.querySelector("details").classList.toggle("hide",all);
const mine=ff.size?d.fin.filter(f=>f=="nonfoil"?ff.has("n"):f=="foil"?ff.has(d.sg?"s":"f"):0):d.fin,
stOk=!st||(st=="n"&&mine.some(f=>!own.has(d.k+"-"+f)))||(st=="p"&&part)||(st=="b"&&all),
fOk=(!fc.size||(fc.has("C")&&!d.ci)||[...fc].some(x=>d.ci.includes(x)))&&(!fr.size||fr.has(d.r))&&(!ff.size||mine.length>0)&&(!fy.size||fy.has(d.ty)),
show=(!s||(s=="*"?want.has(d.k)&&(owner||!all):d.s==s))&&stOk&&fOk&&d.n.toLowerCase().includes(q);
e.classList.toggle("hide",!show);v+=show});
[...$("tabs").children].forEach(b=>b.classList.toggle("on",b.dataset.s==cur));
const wt=$("tabs").children[1];if(wt)wt.hidden=!owner&&!want.size;$("mp").hidden=!(cur=="*"&&!owner);
const T=D.length,N=D.reduce((a,d)=>a+d.fin.length,0),bar=(b,t,x,n)=>{const p=(100*x/n).toFixed(1);$(b).style.width=p+"%";$(t).innerHTML=`<b>${p}%</b><span class=cn> · ${x.toLocaleString()} / ${n.toLocaleString()}</span>`};
bar("mb","mt",m,T);bar("gb","gt",gm,N);
const n=fc.size+fr.size+ff.size+fy.size;$("fc").textContent=n;$("fc").classList.toggle("hide",!n);
$("cnt").textContent=`Showing ${v} cards`}
g.onclick=e=>{const w=e.target.closest(".wl");
 if(w){if(owner){const k=D[els.indexOf(w.closest(".c"))].k;want.has(k)?want.delete(k):want.add(k);queue();draw()}return}
 const c=e.target.dataset.c;if(c)try{navigator.clipboard.writeText(c)}catch(x){}};
$("more").onclick=()=>{cur="";$("st").value="n";draw();scrollTo(0,0)};
$("fi").innerHTML=IC.filter;$("fb").onclick=()=>{$("fp").hidden=!$("fp").hidden};
document.addEventListener("click",e=>{if(!$("qr").contains(e.target))$("fp").hidden=true});
$("fp").onclick=e=>{const b=e.target.closest(".ch,#fx");if(!b)return;const S={c:fc,r:fr,f:ff,y:fy};
 if(b.id=="fx")Object.values(S).forEach(t=>t.clear());else{const a=Object.keys(S).find(k=>b.dataset[k]!==undefined),k=b.dataset[a];S[a].has(k)?S[a].delete(k):S[a].add(k)}
 $("fp").querySelectorAll(".ch").forEach(x=>x.classList.toggle("on",Object.entries(S).some(([a,t])=>x.dataset[a]!==undefined&&t.has(x.dataset[a]))));draw()};
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
const idx=new Map;D.forEach(d=>{const k=d.s.toLowerCase()+"|"+d.c.toLowerCase();if(!idx.has(k))idx.set(k,d)});
const csv=t=>{const R=[];let r=[],f="",q=0;for(let i=0;i<t.length;i++){const c=t[i];
 if(q){if(c=='"'){if(t[i+1]=='"'){f+='"';i++}else q=0}else f+=c}
 else if(c=='"')q=1;else if(c==","){r.push(f);f=""}
 else if(c=="\\n"||c=="\\r"){if(c=="\\r"&&t[i+1]=="\\n")i++;r.push(f);f="";R.push(r);r=[]}else f+=c}
 if(f||r.length){r.push(f);R.push(r)}return R};
function doImport(txt){if(!owner)return;const before=own.size;let rows=0,skip=0;
 const add=(set,cn,w)=>{const d=idx.get(String(set).trim().toLowerCase()+"|"+String(cn).trim().toLowerCase());if(!d){skip++;return}const alt=w=="etched"?"foil":"etched";own.add(d.k+"-"+(d.fin.includes(w)?w:d.fin.includes(alt)?alt:d.fin[0]));rows++};
 const first=txt.split(/\\r?\\n/).find(l=>l.trim())||"";
 if(/set code|collector number/i.test(first)){ // ManaBox CSV; rows from wishlists ("list" binder type) don't count as owned
  const R=csv(txt),H=R.shift().map(h=>h.trim().toLowerCase()),c=n=>H.indexOf(n),
  iS=c("set code"),iN=c("collector number"),iF=c("foil"),iQ=c("quantity"),iT=H.findIndex(h=>/binder.?type/.test(h));
  if(iS<0||iN<0)return $("rs").textContent="That CSV needs 'Set code' and 'Collector number' columns.";
  R.forEach(r=>{if(r.length<2||(iQ>=0&&!(+r[iQ]>0))||(iT>=0&&/list|wish/i.test(r[iT]||"")))return;
   const f=(r[iF]||"").trim().toLowerCase();add(r[iS],r[iN],["foil","true","yes","1"].includes(f)?"foil":f=="etched"?"etched":"nonfoil")})
 }else txt.split(/\\r?\\n/).forEach(l=>{const m=l.match(/\\((\\w+)\\)\\s+(\\S+)(.*)$/);if(!m)return;
  add(m[1],m[2],/\\*F\\*/.test(m[3])?"foil":/\\*E\\*/.test(m[3])?"etched":"nonfoil")});
 queue();draw();
 $("rs").textContent=`Matched ${rows} rows (${own.size-before} newly owned versions). Skipped ${skip} rows that aren't in the tracked sets.`}
$("im").onclick=()=>doImport($("t").value);
$("fl").onchange=()=>{const f=$("fl").files[0];if(f)f.text().then(doImport);$("fl").value=""};
$("rs0").onclick=()=>{if(!owner||prompt("This clears ALL your progress. Export first if unsure. Type RESET to continue")!=="RESET")return;own.clear();queue();draw();$("rs").textContent="Collection reset to 0."};
$("st").value=owner?"":"n";$("up").innerHTML=IC.up;$("up").onclick=()=>scrollTo({top:0,behavior:"smooth"});
addEventListener("scroll",()=>$("up").classList.toggle("hide",scrollY<600),{passive:true});
sort();draw();load();
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
    ov = surge_override()
    tagged = [c for c in cards if is_surge(c, ov)]
    suspects = [c for c in cards if c["set"] in SUSPECT_SETS and (c.get("finishes") or []) == ["foil"] and not is_surge(c, ov)]
    open("docs/surgefoil.txt", "w", encoding="utf-8").write(moxfield(tagged))
    open("docs/surgefoil-check.txt", "w", encoding="utf-8").write(moxfield(suspects))
    print("surge foil tagged:", {k: sum(c["set"] == k for c in tagged) for k in sorted({c["set"] for c in tagged})}, "| foil-only untagged to check:", len(suspects))
    open("docs/cardlist.txt", "w", encoding="utf-8").write(moxfield(cards))
