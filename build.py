"""Builds docs/index.html: every tracked Final Fantasy card with art and per-finish owned checkboxes (saved in the browser)."""
import html, json, os, urllib.parse, urllib.request

QUERY = ("e:fin or e:fca or e:tfin or e:rfin or e:fic or e:tfic or e:afic or e:afin or e:pss5 or e:wfin"
         " or (e:sch (cn:39 or cn:40 or cn:41))"
         " or (e:pw25 (cn:2 or cn:4 or cn:16))"
         " or (e:sld ((cn>=1858 cn<=1872) or (cn>=7001 cn<=7008)))")

def fetch_cards():
    url = "https://api.scryfall.com/cards/search?unique=prints&order=set&q=" + urllib.parse.quote(QUERY)
    cards = []
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": "ff-tracker/1.0", "Accept": "application/json"})
        data = json.load(urllib.request.urlopen(req))
        cards += data["data"]
        url = data.get("next_page")
    return cards

def img(c):
    return (c.get("image_uris") or c["card_faces"][0]["image_uris"])["small"]

def tiles(cards):
    return [{"k": f'{c["set"]}-{c["collector_number"]}', "n": c["name"], "s": c["set"].upper(),
             "c": c["collector_number"], "fin": c.get("finishes") or ["nonfoil"], "i": img(c), "u": c["scryfall_uri"]}
            for c in cards]

def moxfield(cards):
    return "".join(f'1 {c["name"]} ({c["set"].upper()}) {c["collector_number"]}\n' for c in cards)

PAGE = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>FF tracker</title><style>
body{font:14px sans-serif;margin:1em}
#bar{position:sticky;top:0;background:#fff;padding:6px 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center;z-index:1}
.g{display:flex;flex-wrap:wrap;gap:8px}.c{width:146px;text-align:center}.c img{width:100%;border-radius:6px}
.c.own img{opacity:.3}.c details{font-size:12px}.c details a{display:block}.c a{color:inherit;text-decoration:none}.c label{display:block;cursor:pointer}.hide{display:none}
</style>
<div id=bar><b id=cnt></b><select id=set><option value="">All sets</option></select>
<select id=st><option value="">All</option><option value=m>Missing a version</option><option value=o>Complete</option></select>
<input id=q placeholder="Search name"></div>
<div class=g id=g></div>
<details><summary>Import / export (Moxfield text)</summary><textarea id=t rows=8 cols=50></textarea><br>
<button id=ex>Export owned</button> <button id=im>Import (adds to owned)</button></details>
<script>
const D=__DATA__;
let own=new Set;try{own=new Set(JSON.parse(localStorage.getItem("ff-owned")||"[]"))}catch(e){}
const $=id=>document.getElementById(id),g=$("g"),esc=s=>s.replace(/[&<>"]/g,c=>"&#"+c.charCodeAt(0)+";");
const save=()=>{try{localStorage.setItem("ff-owned",JSON.stringify([...own]))}catch(e){}};
[...new Set(D.map(d=>d.s))].forEach(s=>$("set").add(new Option(s,s)));
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
function draw(){let o=0,v=0;const s=$("set").value,st=$("st").value,q=$("q").value.toLowerCase();
els.forEach((e,i)=>{const d=D[i];let all=true;
e.querySelectorAll("input").forEach(x=>{const h=own.has(d.k+"-"+x.dataset.f);x.checked=h;o+=h;all=all&&h});
e.classList.toggle("own",all);e.querySelector("details").classList.toggle("hide",all);
const show=(!s||d.s==s)&&(!st||(st=="o")==all)&&d.n.toLowerCase().includes(q);e.classList.toggle("hide",!show);v+=show});
$("cnt").textContent=`Owned ${o}/${N} versions · showing ${v} cards`}
g.onclick=e=>{const c=e.target.dataset.c;if(c)try{navigator.clipboard.writeText(c)}catch(x){}};
g.onchange=e=>{const k=D[els.indexOf(e.target.closest(".c"))].k+"-"+e.target.dataset.f;e.target.checked?own.add(k):own.delete(k);save();draw()};
["set","st"].forEach(i=>$(i).onchange=draw);$("q").oninput=draw;
$("ex").onclick=()=>$("t").value=D.flatMap(d=>d.fin.filter(f=>own.has(d.k+"-"+f)).map(f=>`1 ${d.n} (${d.s}) ${d.c}${f=="foil"?" *F*":f=="etched"?" *E*":""}`)).join("\\n");
$("im").onclick=()=>{$("t").value.split("\\n").forEach(l=>{const m=l.match(/\\((\\w+)\\)\\s+(\\S+)(.*)$/);if(!m)return;
const w=/\\*F\\*/.test(m[3])?"foil":/\\*E\\*/.test(m[3])?"etched":"nonfoil";
const d=D.find(d=>d.s.toLowerCase()==m[1].toLowerCase()&&d.c.toLowerCase()==m[2].toLowerCase());if(d)own.add(d.k+"-"+(d.fin.includes(w)?w:d.fin[0]))});save();draw()};
draw();
</script>"""

if __name__ == "__main__":
    cards = fetch_cards()
    os.makedirs("docs", exist_ok=True)
    data = json.dumps(tiles(cards), ensure_ascii=False).replace("</", "<\\/")
    open("docs/index.html", "w", encoding="utf-8").write(PAGE.replace("__DATA__", data))
    open("docs/cardlist.txt", "w", encoding="utf-8").write(moxfield(cards))
