"""Builds docs/index.html: every tracked Final Fantasy card with art and per-finish owned checkboxes (saved in the browser)."""
import html, json, os, urllib.parse, urllib.request

QUERY = ("e:fin or e:fca or e:tfin or e:rfin or e:fic or e:tfic or e:afic or e:afin or e:pss5 or e:wfin"
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
    return (c.get("image_uris") or c["card_faces"][0]["image_uris"])["small"]

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
:root{--bg:#fff;--fg:#111;--tab:#f6f1dc;--tb:#c9c3a5;--ln:#eee;--on:#b3202c;--ic:none;color-scheme:light}
:root[data-t=dark]{--bg:#17171a;--fg:#e8e8e8;--tab:#2a2a2f;--tb:#47474f;--ln:#2e2e33;--on:#e05561;--ic:invert(1);color-scheme:dark}
body{font:14px sans-serif;margin:1em;background:var(--bg);color:var(--fg)}
#bar{position:sticky;top:0;background:var(--bg);padding:6px 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center;z-index:1}
.g{display:flex;flex-wrap:wrap;gap:8px}.c{width:146px;text-align:center}.c img{width:100%;border-radius:6px}
.c.own img{opacity:.3}#tabs{display:flex;gap:6px;width:100%;overflow-x:auto;padding-bottom:4px}
.t{font:12px monospace;text-transform:uppercase;padding:9px 14px;border:1px solid var(--tb);border-radius:10px;background:var(--tab);color:var(--fg);cursor:pointer;white-space:nowrap}.t.on{border-color:var(--on)}.ic{width:16px;height:16px;vertical-align:-3px;filter:var(--ic)}
.g.list{flex-direction:column;gap:2px}.list .c{width:auto;display:flex;align-items:center;gap:12px;text-align:left;border-bottom:1px solid var(--ln)}
.list .c img{width:36px}.list .c>a{flex:none}.list .c>div{flex:1}.list .c label{display:inline}.c details{font-size:12px}.c details a{display:block}.c a{color:inherit;text-decoration:none}.c label{display:block;cursor:pointer}.hide{display:none}
</style>
<div id=bar><div id=tabs></div><b id=cnt></b>
<select id=st><option value="">All</option><option value=m>Missing a version</option><option value=o>Complete</option></select>
<select id=so><option value=n>Number ↑</option><option value=d>Number ↓</option><option value=a>Name A–Z</option></select>
<input id=q placeholder="Search name"><button id=vw>List view</button><button id=th></button></div>
<div class=g id=g></div>
<details><summary>Import / export (Moxfield text)</summary><textarea id=t rows=8 cols=50></textarea><br>
<button id=ex>Export owned</button> <button id=im>Import (adds to owned)</button></details>
<script>
const D=__DATA__,SI=__SETS__;
let own=new Set;try{own=new Set(JSON.parse(localStorage.getItem("ff-owned")||"[]"))}catch(e){}
const $=id=>document.getElementById(id),g=$("g"),esc=s=>s.replace(/[&<>"]/g,c=>"&#"+c.charCodeAt(0)+";");
let th="";try{th=localStorage.getItem("ff-theme")||""}catch(e){}
th=th||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");
const setT=t=>{th=t;document.documentElement.dataset.t=t;$("th").textContent=t=="dark"?"Light mode":"Dark mode"};
$("th").onclick=()=>{setT(th=="dark"?"light":"dark");try{localStorage.setItem("ff-theme",th)}catch(e){}};setT(th);
const save=()=>{try{localStorage.setItem("ff-owned",JSON.stringify([...own]))}catch(e){}};
const ORDER=["FIN","FCA","TFIN","RFIN","FIC","TFIC","AFIC","AFIN","PSS5","WFIN","SCH","PW25","SLD"],have=new Set(D.map(d=>d.s)),
sets=[...ORDER.filter(s=>have.has(s)),...[...have].filter(s=>!ORDER.includes(s))],rank=Object.fromEntries(sets.map((s,i)=>[s,i]));let cur="";
$("tabs").innerHTML=["",...sets].map(s=>`<button class=t data-s="${s}">${s?`${(SI[s]||{}).i?`<img class=ic alt="" src="${SI[s].i}"> `:""}${esc((SI[s]||{n:s}).n)}`:"All"} <small>${s?D.filter(d=>d.s==s).length:D.length}</small></button>`).join("");
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
const FN={nonfoil:"Non-foil",foil:"Foil",etched:"Etched"},N=D.reduce((a,d)=>a+d.fin.length,0);
g.innerHTML=D.map(d=>`<div class=c><a href="${d.u}" target=_blank><img loading=lazy alt="" src="${d.i}"></a><div>${esc(d.n)}<br><small>${d.s} ${d.c}</small></div>${d.fin.map(f=>`<label><input type=checkbox data-f=${f}> ${FN[f]||f}</label>`).join("")}${menu(d)}</div>`).join("");
const els=[...g.children];
function draw(){let o=0,v=0;const s=cur,st=$("st").value,q=$("q").value.toLowerCase();
els.forEach((e,i)=>{const d=D[i];let all=true;
e.querySelectorAll("input").forEach(x=>{const h=own.has(d.k+"-"+x.dataset.f);x.checked=h;o+=h;all=all&&h});
e.classList.toggle("own",all);e.querySelector("details").classList.toggle("hide",all);
const show=(!s||d.s==s)&&(!st||(st=="o")==all)&&d.n.toLowerCase().includes(q);e.classList.toggle("hide",!show);v+=show});
[...$("tabs").children].forEach(b=>b.classList.toggle("on",b.dataset.s==cur));
$("cnt").textContent=`Owned ${o}/${N} versions · showing ${v} cards`}
g.onclick=e=>{const c=e.target.dataset.c;if(c)try{navigator.clipboard.writeText(c)}catch(x){}};
g.onchange=e=>{const k=D[els.indexOf(e.target.closest(".c"))].k+"-"+e.target.dataset.f;e.target.checked?own.add(k):own.delete(k);save();draw()};
$("st").onchange=draw;$("q").oninput=draw;
const num=(a,b)=>a.c.localeCompare(b.c,undefined,{numeric:true}),
by={n:(a,b)=>rank[a.s]-rank[b.s]||num(a,b),d:(a,b)=>rank[a.s]-rank[b.s]||num(b,a),a:(a,b)=>a.n.localeCompare(b.n)||rank[a.s]-rank[b.s]||num(a,b)};
const sort=()=>g.append(...D.map((_,i)=>i).sort((i,j)=>by[$("so").value](D[i],D[j])).map(i=>els[i]));
$("so").onchange=sort;
$("vw").onclick=()=>{g.classList.toggle("list");$("vw").textContent=g.classList.contains("list")?"Grid view":"List view"};
$("ex").onclick=()=>$("t").value=D.flatMap(d=>d.fin.filter(f=>own.has(d.k+"-"+f)).map(f=>`1 ${d.n} (${d.s}) ${d.c}${f=="foil"?" *F*":f=="etched"?" *E*":""}`)).join("\\n");
$("im").onclick=()=>{$("t").value.split("\\n").forEach(l=>{const m=l.match(/\\((\\w+)\\)\\s+(\\S+)(.*)$/);if(!m)return;
const w=/\\*F\\*/.test(m[3])?"foil":/\\*E\\*/.test(m[3])?"etched":"nonfoil";
const d=D.find(d=>d.s.toLowerCase()==m[1].toLowerCase()&&d.c.toLowerCase()==m[2].toLowerCase());if(d)own.add(d.k+"-"+(d.fin.includes(w)?w:d.fin[0]))});save();draw()};
sort();draw();
</script>"""

if __name__ == "__main__":
    cards = fetch_cards()
    os.makedirs("docs", exist_ok=True)
    t = tiles(cards)
    dump = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    page = PAGE.replace("__DATA__", dump(t)).replace("__SETS__", dump(fetch_sets({x["s"] for x in t})))
    open("docs/index.html", "w", encoding="utf-8").write(page)
    open("docs/cardlist.txt", "w", encoding="utf-8").write(moxfield(cards))
