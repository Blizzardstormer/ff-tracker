"""Builds docs/index.html: every Final Fantasy card, owned ones tucked away, missing ones up front."""
import html, json, os, re, urllib.parse, urllib.request

# Scryfall search for everything tracked (from sets_to_track.txt).
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

def owned_keys():
    # owned.txt is Moxfield format: "1 Cloud, Ex-SOLDIER (FIN) 123 *F*"
    keys = set()
    for line in open("owned.txt", encoding="utf-8"):
        m = re.search(r"\((\w+)\)\s+(\S+)", line)
        if m:
            keys.add((m[1].lower(), m[2].lower()))
    return keys

def img(c):
    return (c.get("image_uris") or c["card_faces"][0]["image_uris"])["small"]

def tile(c):
    return (f'<a class="c" href="{c["scryfall_uri"]}" target="_blank"><img loading="lazy" src="{img(c)}">'
            f'<div>{html.escape(c["name"])}<br><small>{c["set"].upper()} {c["collector_number"]}</small></div></a>')

def render(cards, owned):
    have = [c for c in cards if (c["set"], c["collector_number"].lower()) in owned]
    need = [c for c in cards if c not in have]
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>FF tracker</title><style>body{{font:14px sans-serif;margin:1em}}.g{{display:flex;flex-wrap:wrap;gap:8px}}
.c{{width:146px;color:inherit;text-decoration:none;text-align:center}}.c img{{width:100%;border-radius:6px}}</style>
<h1>Missing {len(need)} / {len(cards)}</h1><div class=g>{''.join(map(tile, need))}</div>
<details><summary>Owned ({len(have)})</summary><div class=g>{''.join(map(tile, have))}</div></details>"""

def moxfield(cards):
    return "".join(f'1 {c["name"]} ({c["set"].upper()}) {c["collector_number"]}\n' for c in cards)

if __name__ == "__main__":
    cards = fetch_cards()
    os.makedirs("docs", exist_ok=True)
    open("docs/index.html", "w", encoding="utf-8").write(render(cards, owned_keys()))
    open("docs/cardlist.txt", "w", encoding="utf-8").write(moxfield(cards))  # review/import the full tracked list
