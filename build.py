#!/usr/bin/env python3
"""ByeBulky static site builder (stdlib only).
Usage: python3 build.py            -> writes ./site/
Data:  data/cities/<slug>.json      -> /<slug>/
       data/guides/<slug>.json      -> /<city>/<guide-slug>/  (item guides that reuse city listings)
"""
import json, html, shutil, datetime, re, os
from ytembed import embed as yt_embed, video_ld, VIDEOS
import privacy
YT_CHANNEL = "https://www.youtube.com/@ByeBulkyGuide"
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"
CFG = json.loads((ROOT / "site.json").read_text())
NS = "Not stated, check with them"
TYPES = ["city bulk pickup", "charity pickup", "drop-off", "furniture bank", "paid hauler", "retailer haul-away"]
REQUIRED = ["id", "name", "type", "items_accepted", "condition_rules", "stairs_inside", "lead_time", "cost",
            "service_area", "source_urls", "last_verified"]

e = lambda s: html.escape(str(s), quote=True)

# Links are relative so the site works both at https://yairsz.github.io/byebulky/ and at a custom-domain root.
# PREFIX is set per page ("" for /, "../" for /boston/, "../../" for /boston/mattress/).
PREFIX = ""
def set_page(path):
    global PREFIX
    depth = len([p for p in path.strip("/").split("/") if p])
    PREFIX = "../" * depth
def U(target):
    """Relative URL to a site-root path like '/boston/'."""
    t = target.lstrip("/")
    return (PREFIX + t) or "./"

def val(s):
    s = s if s else NS
    if s.strip().startswith(NS):
        return f'<span class="ns">{e(s)}</span>'
    return e(s)

def base_url():
    return os.environ.get("SITE_BASE_URL", CFG["base_url"]).rstrip("/")

def ga_snippet():
    gid = (CFG.get("ga_measurement_id") or "").strip()
    if not gid:
        return ""
    return f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={e(gid)}"></script>
<script>window.dataLayer = window.dataLayer || [];function gtag(){{dataLayer.push(arguments);}}gtag('js', new Date());gtag('config', '{e(gid)}');</script>"""

META = {}  # path -> (title, description); feeds llms.txt
# path -> YYYY-MM-DD the page's content was last verified/changed. Filled in main() from the data files
# (never "today" by default), and used for WebPage dateModified JSON-LD, visible dates and sitemap lastmod.
MODIFIED = {}
ABOUT_UPDATED = "2026-10-24"     # bump when /about/ text changes
PRIVACY_UPDATED = "2026-10-23"   # matches privacy.EFFECTIVE

def org_ld():
    return {"@type": "Organization", "@id": base_url() + "/#org", "name": CFG["site_name"], "url": base_url() + "/",
            "sameAs": [YT_CHANNEL]}

def webpage_ld(title, desc, path):
    if path not in MODIFIED:
        return None
    return {"@context": "https://schema.org", "@type": "AboutPage" if path == "/about/" else "WebPage",
            "@id": base_url() + path, "url": base_url() + path, "name": title, "description": desc,
            "dateModified": MODIFIED[path], "inLanguage": "en-US",
            "isPartOf": {"@type": "WebSite", "@id": base_url() + "/#website", "name": CFG["site_name"],
                         "url": base_url() + "/", "publisher": org_ld()},
            "publisher": {"@id": base_url() + "/#org"}}

# Hand-written complete meta descriptions for pages whose long description would otherwise be cut mid-sentence.
# Reworded only from the page's own description; no new facts. Keep <= 158 chars.
META_DESC = {'/boston/mattress/': "Mattresses are banned from Massachusetts trash. Book Boston's curbside mattress pickup (6 units or fewer) or use a hauler in 7+ unit buildings.", '/boston/': 'Every verified way to get rid of a couch, mattress, furniture or appliance in Boston: City pickup, ReStore, furniture banks and haulers, with sources.', '/boston/couch/': "Boston lets you put furniture out with regular trash. Here's how it works, which charities take sofas, and paid pickup options, with sources.", '/': 'Verified, city-by-city ways to get rid of couches, mattresses, furniture and appliances: city pickup, donation pickup, drop-off and haulers.'}

def fit_meta(title, desc, suffix=None):
    """Keep SERP snippets readable: titles <= 70 chars (keep the brand suffix unless longer; drop the site-name suffix if needed),
    descriptions <= 158 chars (cut at the last full sentence, else the last word + ellipsis).
    Only shortens; never adds wording."""
    if suffix and title.endswith(suffix) and len(title) > 70:
        title = title[: -len(suffix)]
    if len(desc) > 158:
        cut = desc[:158]
        ends = [cut.rfind(p) for p in (". ", "? ", "! ")]
        end = max(ends)
        if end >= 90:
            desc = cut[: end + 1]
        else:
            desc = cut[: cut.rfind(" ")].rstrip(",;:-–—(") + "…"
    return title, desc

def page(title, desc, path, body, jsonld=None):
    desc = META_DESC.get(path, desc)
    title, desc = fit_meta(title, desc)
    url = base_url() + path
    META[path] = (title, desc)
    lds = [x for x in ((jsonld if isinstance(jsonld, list) else [jsonld]) + [video_ld(path), webpage_ld(title, desc, path)]) if x]
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x)}</script>' for x in lds)
    year = datetime.date.today().year
    return f"""<!doctype html>
<html lang="en"><head>{ga_snippet()}
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="msvalidate.01" content="45CDFD465C8824EB2040D1A77F7E20CB" />
<link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{e(url)}">
<link rel="stylesheet" href="{U('/static/style.css')}">{ld}
</head><body>
<header class="site"><div class="wrap"><a class="logo" href="{U('/')}">Bye<span>Bulky</span></a>
<nav><a href="{U('/boston/')}">Boston</a><a href="{U('/about/')}">How we verify</a></nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">© {year} {e(CFG['site_name'])}. Information is gathered from official sources and can change. Always confirm with the organization before you haul anything. <a href="{U('/about/')}">Affiliate disclosure &amp; how we verify</a>. <a href="{U('/privacy/')}">Privacy policy</a>. <a href="{YT_CHANNEL}" rel="noopener" target="_blank">ByeBulky on YouTube</a>.</div></footer>
</body></html>"""


from urllib.parse import quote as _q
def report_link(name):
    """Public 'Report a change' mailto on every listing card (added 2026-10-26; address = privacy.CONTACT)."""
    subj = _q(f"Report a change: {name}")
    return f'<p class="meta report"><a href="mailto:{privacy.CONTACT}?subject={subj}">Report a change</a></p>'

def listing_card(l):
    for k in REQUIRED:
        assert k in l, f"listing {l.get('id')} missing {k}"
    assert l["type"] in TYPES, f"bad type {l['type']} in {l['id']}"
    assert l["source_urls"], f"listing {l['id']} has no source"
    items = "".join(f"<li>{e(i)}</li>" for i in l["items_accepted"])
    notacc = ""
    if l.get("items_not_accepted"):
        notacc = "<dt>Not accepted</dt><dd><ul class='items'>" + "".join(f"<li>{e(i)}</li>" for i in l["items_not_accepted"]) + "</ul></dd>"
    book = []
    if l.get("book_url"): book.append(f'<a href="{e(l["book_url"])}" rel="nofollow noopener" target="_blank">Website / booking</a>')
    if l.get("phone"): book.append(e(l["phone"]))
    if l.get("email"): book.append(f'<a href="mailto:{e(l["email"])}">{e(l["email"])}</a>')
    book = " · ".join(book) or f'<span class="ns">{NS}</span>'
    srcs = " ".join(f'<a href="{e(u)}" rel="nofollow noopener" target="_blank">[{i+1}]</a>' for i, u in enumerate(l["source_urls"]))
    addr = f"<dt>Address</dt><dd>{e(l['address'])}</dd>" if l.get("address") else ""
    notes = f"<dt>Notes</dt><dd>{e(l['notes'])}</dd>" if l.get("notes") else ""
    search = e((l["name"] + " " + " ".join(l["items_accepted"])).lower())
    return f"""<article class="card" id="{e(l['id'])}" data-type="{e(l['type'])}" data-search="{search}">
<span class="badge">{e(l['type'])}</span><h3>{e(l['name'])}</h3>
<dl><dt>Takes</dt><dd><ul class="items">{items}</ul></dd>{notacc}
<dt>Condition rules</dt><dd>{val(l['condition_rules'])}</dd>
<dt>Stairs / inside pickup</dt><dd>{val(l['stairs_inside'])}</dd>
<dt>Lead time / hours</dt><dd>{val(l['lead_time'])}</dd>
<dt>Cost</dt><dd>{val(l['cost'])}</dd>
<dt>Service area</dt><dd>{val(l['service_area'])}</dd>{addr}
<dt>How to book</dt><dd>{book}</dd>{notes}
<dt>Sources</dt><dd>{srcs} · last verified {e(l['last_verified'])}</dd></dl>{report_link(l['name'])}</article>"""

FILTER_JS = """<script>
(function(){var t=document.getElementById('ft'),q=document.getElementById('fq');if(!t)return;
function f(){var tv=t.value,qv=q.value.toLowerCase().trim();document.querySelectorAll('article.card').forEach(function(c){
var ok=(!tv||c.dataset.type===tv)&&(!qv||c.dataset.search.indexOf(qv)>-1);c.style.display=ok?'':'none';});}
t.addEventListener('change',f);q.addEventListener('input',f);})();
</script>"""

def loadup_slot():
    # >>> LOADUP WIDGET PLACEHOLDER <<<  Filled only from site.json "loadup_widget_html" (empty = nothing shown).
    w = CFG.get("loadup_widget_html", "").strip()
    if not w:
        return "<!-- LOADUP_WIDGET_PLACEHOLDER: intentionally empty until an approved LoadUp affiliate/Brand Builder embed exists (see site.json). -->"
    return f'<section class="card" id="book-a-haul"><h2>Book a paid junk pickup</h2><p class="meta">Affiliate link: we may earn a commission. See our <a href="{U('/about/')}">disclosure</a>.</p>{w}</section>'

def faq_ld(qas):
    if not qas:
        return None
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": x["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in qas]}

def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": base_url() + u}
                                for i, (n, u) in enumerate(items)]}

def qa_block(qas):
    if not qas:
        return ""
    return '<div class="qa">' + "".join(f"<div><strong>{e(x['q'])}</strong>{e(x['a'])}</div>" for x in qas) + "</div>"

def _names(ls):
    n = [l["name"] for l in ls]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + " and " + n[-1]

ITEM_RX = [("mattress", r"mattress"), ("couch", r"couch|sofa|sectional|upholster"),
           ("refrigerator or other large appliance", r"refrigerat|fridge|freezer|washer|dryer|air condition|appliance")]
ITEM_EXCLUDE = re.compile(r"small (electronics|appliance|furniture)|no appliance", re.I)

def takes_item(l, rx, item):
    """Listing explicitly accepts the item (or, for couches, generic Furniture)."""
    acc = [i for i in l.get("items_accepted", []) if not ITEM_EXCLUDE.search(i)]
    if any(re.search(rx, i, re.I) for i in acc):
        return True
    # Generic "Furniture" counts for couches only if the listing doesn't list couches/sofas as not accepted
    # (item-specific exclusions like "stained mattresses" are conditions, so they don't remove a listing).
    return (item == "couch" and any(re.match(r"furniture\b", i, re.I) for i in acc)
            and not any(re.search(rx, i, re.I) for i in l.get("items_not_accepted", [])))

def city_faq(c):
    """Computed fan-out answers from the listing fields (never hand-written)."""
    ls = c["listings"]; city = c["name"]; n = len(ls)
    out = []
    yes = [l for l in ls if l.get("stairs_inside", "").startswith("Yes")]
    no = [l for l in ls if l.get("stairs_inside", "").startswith("No.")]
    unk = [l for l in ls if l.get("stairs_inside", "").startswith("Not stated")]
    if yes:
        other = n - len(yes) - len(no) - len(unk)
        a = (f"Of the {n} options we list for {city}, {len(yes)} {'says it' if len(yes) == 1 else 'say they'} will collect from inside your home: {_names(yes)}. "
             f"{len(no)} {'is' if len(no) == 1 else 'are'} curbside or drop-off only"
             + (f", {other} give partial details (see each listing)" if other else "")
             + f", and {len(unk)} {'doesn' if len(unk) == 1 else 'don'}'t say, so ask them. Fees and conditions vary; check each listing.")
        out.append({"q": f"Who will pick up bulky items from inside my home in {city}?", "a": a})
    # Multi-condition (item x inside-pickup) answers. Learning 2026-10-25, Neil Patel "AI Mode ... 5 New Rules":
    # long, specific queries trigger AI answers far more often and need cited sources. Counted from fields only.
    for item, rx in ITEM_RX:
        m = [l for l in ls if takes_item(l, rx, item)]
        my = [l for l in m if l.get("stairs_inside", "").startswith("Yes")]
        if not my:
            continue
        mn = [l for l in m if l.get("stairs_inside", "").startswith("No.")]
        mu = [l for l in m if l.get("stairs_inside", "").startswith("Not stated")]
        mo = len(m) - len(my) - len(mn) - len(mu)
        city_no = [l for l in mn if l["type"] == "city bulk pickup"]
        rest = []
        if mn:
            rest.append(f"{len(mn)} {'is' if len(mn) == 1 else 'are'} curbside or drop-off only"
                        + (f" (including the city's own pickup, {_names(city_no)})" if city_no else ""))
        if mo:
            rest.append(f"{mo} give{'s' if mo == 1 else ''} partial details")
        if mu:
            rest.append(f"{len(mu)} {'doesn' if len(mu) == 1 else 'don'}'t say")
        rest_s = (", ".join(rest[:-1]) + (", and " if len(rest) > 2 else " and ") + rest[-1]) if len(rest) > 1 else (rest[0] if rest else "")
        a = (f"{len(my)} of the {len(m)} options we list for {city} that take a {item} "
             f"{'says it' if len(my) == 1 else 'say they'} will collect it from inside your home: {_names(my)}. "
             + (rest_s[0].upper() + rest_s[1:] + ". " if rest_s else "")
             + "Prices and conditions differ; check each listing.")
        out.append({"q": f"Who will take a {item} out of my apartment or house (not just from the curb) in {city}?", "a": a})
    cnt = [(t, sum(1 for l in ls if l["type"] == t)) for t in TYPES]
    cnt = [(t, k) for t, k in cnt if k]
    out.append({"q": f"What are the ways to get rid of bulky items in {city}?",
                "a": f"We list {n} options in {city}: " + "; ".join(f"{t} ({k})" for t, k in cnt) + ". Each listing links to the page we checked."})
    return out

# City-specific section headings (learning 2026-10-25, Jesse Cunningham "AI micro directories": every city page is a
# money page; headings should name the service and the place). Labels describe the listing type only; no ranking words.
TYPE_HEADINGS = {"city bulk pickup": "City bulk item pickup for {city} residents",
                 "charity pickup": "Charity donation pickup for {city} residents",
                 "drop-off": "Drop-off locations for {city} residents",
                 "furniture bank": "Furniture banks for {city} residents",
                 "paid hauler": "Paid junk removal and hauling for {city} residents",
                 "retailer haul-away": "Retailer haul-away for {city} residents"}

def type_heading(t, city):
    return TYPE_HEADINGS.get(t, t.title()).format(city=city)

def city_page(c):
    set_page(f"/{c['slug']}/")
    used_types = [t for t in TYPES if any(l["type"] == t for l in c["listings"])]
    opts = "".join(f'<option value="{e(t)}">{e(t.title())}</option>' for t in used_types)
    qas = c.get("quick_answers", []) + city_faq(c)
    qa = "".join(f"<div><strong>{e(x['q'])}</strong>{e(x['a'])}</div>" for x in qas)
    groups = ""
    for t in used_types:
        cards = "".join(listing_card(l) for l in c["listings"] if l["type"] == t)
        n = sum(1 for l in c["listings"] if l["type"] == t)
        groups += f"<h2>{e(type_heading(t, c['name']))} ({n})</h2>{cards}"
    res = "".join(f'<li><a href="{e(r["url"])}" rel="nofollow noopener" target="_blank">{e(r["label"])}</a></li>' for r in c.get("resources", []))
    guides = [g for g in GUIDES if g["city"] == c["slug"]]
    glinks = ""
    if guides:
        glinks = "<h2>Item guides for " + e(c["name"]) + "</h2><ul>" + "".join(f'<li><a href="{U("/" + g["path"] + "/")}">{e(g["title"])}</a></li>' for g in guides) + "</ul>"
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › {e(c['name'])}, {e(c['state'])}</p>
<h1>How to get rid of a couch, mattress or furniture in {e(c['name'])}</h1>
<p class="lead">{e(c['intro'])}</p>
<p class="meta">{len(c['listings'])} options · every listing links to its source · last verified {e(c['last_verified'])}{(" · page updated " + e(MODIFIED[f"/{c['slug']}/"])) if MODIFIED.get(f"/{c['slug']}/", c['last_verified']) != c['last_verified'] else ""}</p>
<div class="qa">{qa}</div>
{loadup_slot()}
{glinks}
{other_city_hubs(c)}
<div class="filters"><select id="ft" aria-label="Filter by type"><option value="">All types</option>{opts}</select>
<input id="fq" type="search" placeholder="Filter: mattress, sofa, fridge…" aria-label="Filter by item"></div>
{groups}
<h2>Useful official tools</h2><ul>{res}</ul>
<p class="note">Spotted something out of date? Policies change often. Tell us and we'll re-check it against the source.</p>
{FILTER_JS}"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": c["title"],
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": l["name"]} for i, l in enumerate(c["listings"])]}
    lds = [ld, faq_ld(qas), crumbs_ld([("Home", "/"), (c["name"], f"/{c['slug']}/")])]
    return page(c["title"], c["meta_description"], f"/{c['slug']}/", body, lds)

# Entity hubs (added 2026-10-25): each city page is the hub for that city; each item type ("Mattress") is an entity
# shared across cities. Item guides link up to their city hub in prose and sideways to the same item in other cities;
# city hubs link to the other city hubs. All counts are computed from data/.
def city_hub_line(g, city):
    n = len(city["listings"]); k = len([x for x in GUIDES if x["city"] == city["slug"]])
    return (f'<p>This guide is one part of our <a href="{U("/" + city["slug"] + "/")}">{e(city["name"])} bulky item hub</a>, '
            f'which lists all {n} {e(city["name"])} options we\'ve verified'
            + (f' and {k - 1} more item guide{"s" if k - 1 != 1 else ""}' if k > 1 else '') + '.</p>')

def same_item_other_cities(g):
    cmap = {c["slug"]: c for c in CITIES}
    oth = [x for x in GUIDES if x["short"] == g["short"] and x["city"] != g["city"] and x["city"] in cmap]
    cost = (f'<p><a href="{U(COST_PATH)}">Compare mattress disposal costs around Boston (City fees and published hauler prices) →</a></p>'
            if g["short"] == "Mattress" else "")
    if not oth: return cost
    return cost + (f"<h2>{e(g['short'])} guides for other cities</h2><ul>" + "".join(
        f'<li><a href="{U("/" + x["path"] + "/")}">{e(cmap[x["city"]]["name"])}: {e(x["title"])}</a> '
        f'({len(x.get("listing_ids", []))} options)</li>' for x in oth) + "</ul>")

def other_city_hubs(c):
    oth = [o for o in CITIES if o["slug"] != c["slug"]]
    if not oth: return ""
    def gcount(o): return len([x for x in GUIDES if x["city"] == o["slug"]])
    return ("<h2>Other Boston-area cities we cover</h2><ul>" + "".join(
        f'<li><a href="{U("/" + o["slug"] + "/")}">{e(o["name"])}, {e(o["state"])}</a> ({len(o["listings"])} options'
        + (f', {gcount(o)} item guide{"s" if gcount(o) != 1 else ""}' if gcount(o) else '') + ')</li>' for o in oth) + "</ul>")

def sibling_guides(g, city):
    """Contextual internal links (added 2026-10-24): other item guides for the same city."""
    sib = [x for x in GUIDES if x["city"] == city["slug"] and x["path"] != g["path"]]
    if not sib: return ""
    return f"<h2>More {e(city['name'])} item guides</h2><ul>" + "".join(
        f'<li><a href="{U("/" + x["path"] + "/")}">{e(x["title"])}</a></li>' for x in sib) + "</ul>"

ITEM_PHRASE = {"Mattress": "a mattress", "Couch": "a couch or sofa", "Appliances": "a fridge, AC, TV or other appliance"}

def options_heading(g, city, n):
    """Intent-matched heading for the listing section (added 2026-10-26, run #22): replaces generic "Options"."""
    if g.get("options_h"): return g["options_h"]
    item = ITEM_PHRASE.get(g["short"], g["short"].lower())
    return f"Every option we list: {n} ways to get rid of {item} in {city['name']}"

_SENT = re.compile(r"(?<![ap]\.m)(?<!\b[A-Z])\.\s+(?=[A-Z$(])")

def _cell(s, n=170):
    """Verbatim leading sentences of a field for table cells: keeps adding sentences while short (so "No." or
    "Paid service." aren't left alone) and never splits inside "a.m."/"p.m.". Adds "…" when cut."""
    s = (s or "").strip()
    parts = _SENT.split(s)
    out = parts[0]
    for x in parts[1:]:
        if len(out) >= 40 and len(out) + len(x) > n:
            return out + ". …" if not out.endswith(".") else out + " …"
        out = out + ". " + x
    return out

def guide_glance(ls, g, city):
    """Answer-first comparison table on each item guide (run #24, Surfer "3-Step SEO Playbook": consistent per-option
    framework + skimmable TL;DR). Every cell is the first sentence of a listing field, verbatim; no new claims."""
    if len(ls) < 2:
        return ""
    item = ITEM_PHRASE.get(g["short"], g["short"].lower())
    rows = "".join(
        f'<tr><th scope="row"><a href="#{e(l["id"])}">{e(l["name"])}</a></th><td>{e(l["type"])}</td>'
        f'<td>{e(_cell(l.get("cost")))}</td><td>{e(_cell(l.get("stairs_inside")))}</td><td>{e(_cell(l.get("lead_time")))}</td></tr>'
        for l in ls)
    return (f'<h2 id="at-a-glance">At a glance: cost, inside pickup and timing for {len(ls)} ways to get rid of {e(item)} in {e(city["name"])}</h2>'
            '<p>Each row is copied from the listing below and links to it, with its sources and the date we last checked.</p>'
            '<div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">Option</th><th scope="col">Type</th><th scope="col">Cost</th>'
            '<th scope="col">Inside / stairs pickup</th><th scope="col">Lead time / hours</th></tr></thead><tbody>' + rows + '</tbody></table></div>')

def guide_page(g, city):
    set_page(f"/{g['path']}/")
    ids = g.get("listing_ids", [])
    ls = [l for l in city["listings"] if l["id"] in ids]
    missing = set(ids) - {l["id"] for l in ls}
    assert not missing, f"guide {g['path']} references unknown listings {missing}"
    secs = "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" for s in g.get("sections", []))
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › <a href="{U('/' + city['slug'] + '/')}">{e(city['name'])}</a> › {e(g['short'])}</p>
<h1>{e(g['h1'])}</h1><p class="lead">{e(g['intro'])}</p><p class="meta">Last verified {e(g['last_verified'])}{(" · page updated " + e(MODIFIED[f"/{g['path']}/"])) if MODIFIED.get(f"/{g['path']}/", g['last_verified']) != g['last_verified'] else ""}</p>
{city_hub_line(g, city)}
{qa_block(g.get("quick_answers"))}{guide_glance(ls, g, city)}{secs}{yt_embed('/' + g['path'] + '/', YT_CHANNEL, 'ByeBulky')}{loadup_slot()}<h2 id="all-options">{e(options_heading(g, city, len(ls)))}</h2>{''.join(listing_card(l) for l in ls)}
<p><a href="{U('/' + city['slug'] + '/')}">See all {e(city['name'])} options →</a></p>{sibling_guides(g, city)}{same_item_other_cities(g)}"""
    for x in g.get("quick_answers", []):
        assert x.get("q") and x.get("a"), f"guide {g['path']} has an empty quick answer"
    lds = [faq_ld(g.get("quick_answers")),
           crumbs_ld([("Home", "/"), (city["name"], f"/{city['slug']}/"), (g["short"], f"/{g['path']}/")])]
    return page(g["title"], g["meta_description"], f"/{g['path']}/", body, lds)

def home_guides(cities):
    """Home-page list of every item guide, grouped by city (added 2026-10-24, internal linking)."""
    out = ""
    for c in cities:
        gs = [g for g in GUIDES if g["city"] == c["slug"]]
        if gs:
            out += f"<h3>{e(c['name'])}, {e(c['state'])}</h3><ul>" + "".join(
                f'<li><a href="{U("/" + g["path"] + "/")}">{e(g["title"])}</a></li>' for g in gs) + "</ul>"
    return ("<h2>Item guides</h2>" + out) if out else ""

def _first(s):
    """First sentence of a data field, verbatim (no new claims)."""
    s = (s or "").strip()
    i = s.find(". ")
    return s if i < 0 else s[:i + 1]

def home_mattress_compare(cities):
    """Home-page cross-city table of each City's own mattress program, built only from listing fields
    (cost, service_area, stairs_inside, book_url, phone, source_urls, last_verified). Added run #18 (data-gap tactic)."""
    rows, qa = [], []
    for c in cities:
        l = next((x for x in c["listings"] if x.get("type") == "city bulk pickup" and "mattress" in x["id"]), None)
        if not l:
            continue
        g = next((x for x in GUIDES if x["city"] == c["slug"] and x["short"] == "Mattress"), None)
        city = f"{c['name']}, {c['state']}"
        si = (l.get("stairs_inside") or "").strip()
        where = _first(si[4:] if si.startswith("No. ") else si)
        guide = f'<br><a href="{U("/" + g["path"] + "/")}">Full {e(c["name"])} mattress guide</a>' if g else ""
        src = " ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">source {i + 1}</a>' for i, u in enumerate(l.get("source_urls", [])))
        rows.append(f"<tr><th scope=\"row\">{e(city)}{guide}</th><td>{e(_first(l.get('cost')))}</td>"
                    f"<td>{e(l.get('service_area') or '')}</td><td>{e(where)}</td>"
                    f'<td><a href="{e(l["book_url"])}" rel="noopener" target="_blank">Book</a>' + (f" or call {e(l['phone'])}" if l.get("phone") else "") + "</td>"
                    f"<td>{src}<br><span class=\"meta\">checked {e(l.get('last_verified', ''))}</span></td></tr>")
        qa.append(f"{c['name']}: {_first(l.get('cost'))}")
    if len(rows) < 2:
        return "", None
    names = [c["name"] for c in cities]
    q = {"q": f"How much does it cost to get rid of a mattress in {', '.join(names[:-1])} or {names[-1]}?",
         "a": "Through each City's own mattress pickup, per the official pages: " + " ".join(qa) +
              " Massachusetts bans mattresses and box springs from the trash, so they need one of these programs, a donation outlet or a hauler."}
    html = (f"<h2>City mattress pickup compared: {e(', '.join(names))}</h2>"
            "<p>Each City runs its own mattress and box spring program, and the fees and rules differ. This table is built from the official City pages linked in each row.</p>"
            '<div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">City</th><th scope="col">Fee</th><th scope="col">Who qualifies</th>'
            '<th scope="col">Pickup location</th><th scope="col">How to book</th><th scope="col">Source</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>" + qa_block([q]))
    return html, q

COST_PATH = "/boston-area-mattress-disposal-cost/"
def mattress_cost_rows():
    """Every listing on a Mattress guide whose cost field publishes a dollar amount (not the City programs, which have
    their own table). Same listing id + same cost text across cities = one row. Cells are verbatim fields."""
    cmap = {c["slug"]: c for c in CITIES}
    rows = {}
    for g in GUIDES:
        if g["short"] != "Mattress" or g["city"] not in cmap: continue
        c = cmap[g["city"]]
        for l in c["listings"]:
            if l["id"] not in g.get("listing_ids", []) or l["type"] == "city bulk pickup" or "$" not in (l.get("cost") or ""):
                continue
            k = (l["id"], l["cost"].strip())
            r = rows.setdefault(k, {"l": l, "guides": []})
            r["guides"].append((c, g))
    return list(rows.values())

def mattress_cost_page():
    """Linkable data asset (run #26; Sturm "linkable data assets" + Skipblast "give visitors a reason to stay"):
    what mattress disposal costs around Boston, built only from listing fields already on the mattress guides."""
    set_page(COST_PATH)
    cmp_html, cmp_q = home_mattress_compare(CITIES)
    rows = mattress_cost_rows()
    tr = ""
    for r in rows:
        l = r["l"]
        where = ", ".join(f'<a href="{U("/" + g["path"] + "/")}#{e(l["id"])}">{e(c["name"])}</a>' for c, g in r["guides"])
        src = " ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">source {i + 1}</a>' for i, u in enumerate(l.get("source_urls", [])[:2]))
        tr += (f'<tr><th scope="row">{e(l["name"])}</th><td>{e(l["type"])}</td><td>{e(_cell(l.get("cost"), 260))}</td>'
               f'<td>{e(_cell(l.get("stairs_inside")))}</td><td>{where}</td><td>{src}<br><span class="meta">checked {e(l.get("last_verified", ""))}</span></td></tr>')
    names = [c["name"] for c in CITIES]
    n_guides = len([g for g in GUIDES if g["short"] == "Mattress"])
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › Mattress disposal cost</p>
<h1>What mattress disposal costs around Boston: City programs and published hauler prices</h1>
<p class="lead">Mattresses and box springs can't go in the trash in Massachusetts, so you need a City program, a hauler, or (if it's clean and the charity accepts mattresses) a donation outlet. This page puts every price we've verified for {e(', '.join(names))} in one place. Each row comes from the official City page or the company's own page, linked in the row, and shows when we last checked it. A price is only shown when the source publishes one.</p>
<p class="meta">Page updated {e(MODIFIED.get(COST_PATH, ''))}.</p>
{cmp_html}
<h2 id="haulers">Haulers and donation pickups that publish a mattress or pickup price ({len(rows)})</h2>
<p>These are the options on our {n_guides} city mattress guides whose own page (or the City's list) states a dollar amount. Many other haulers on those guides quote only by phone or photo, so they aren't in this table. Prices are what the source said on the date shown; confirm before you book.</p>
<div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">Option</th><th scope="col">Type</th><th scope="col">Published price</th><th scope="col">Inside / stairs pickup</th><th scope="col">Listed on our guide for</th><th scope="col">Source</th></tr></thead><tbody>{tr}</tbody></table></div>
{yt_embed(COST_PATH, YT_CHANNEL, 'ByeBulky')}
<h2>Every mattress option, city by city</h2><ul>""" + "".join(
        f'<li><a href="{U("/" + g["path"] + "/")}">{e(g["title"])}</a> ({len(g.get("listing_ids", []))} options)</li>'
        for g in GUIDES if g["short"] == "Mattress") + "</ul>"
    lds = [faq_ld([cmp_q]) if cmp_q else None, crumbs_ld([("Home", "/"), ("Mattress disposal cost", COST_PATH)])]
    return page("Mattress disposal cost around Boston: City fees and hauler prices",
                f"City mattress pickup fees and published hauler prices for {', '.join(names[:-1])} and {names[-1]}, with official sources.",
                COST_PATH, body, [x for x in lds if x])

def home(cities):
    set_page("/")
    cmp_html, cmp_q = home_mattress_compare(cities)
    cl = "".join(f'<a href="{U("/" + c["slug"] + "/")}">{e(c["name"])}, {e(c["state"])}<br><span class="meta">{len(c["listings"])} verified options</span></a>' for c in cities)
    body = f"""<h1>Get rid of a couch, mattress or old fridge without the runaround</h1>
<p class="lead">{e(CFG['tagline'])} For each city we list every real option: City bulk and mattress pickup, charities that pick up, drop-off spots, furniture banks, and paid haulers. You see what each one takes, its condition rules, whether it will come inside or up stairs, and its cost. A cost is only shown when the organization publishes it.</p>
<h2>Cities</h2><div class="cities">{cl}</div>
{cmp_html}
<p><a href="{U(COST_PATH)}">Mattress disposal cost around Boston, including published hauler prices →</a></p>
{yt_embed('/', YT_CHANNEL, 'ByeBulky')}
{home_guides(cities)}
<h2>Why this exists</h2>
<p>Charities change what they accept, some stop picking up furniture altogether, and city rules differ from one place to the next. People end up calling three places and still having a couch on the curb. We collect the rules from official sources, link every listing to its source, and date when we last checked it.</p>
<p class="meta">Listings last verified {e(MODIFIED.get('/', ''))}.</p>
<p><a href="{U('/about/')}">How we verify listings &amp; how this site makes money →</a></p>"""
    return page(f"{CFG['site_name']}: How to get rid of furniture, mattresses & appliances in your city",
                "Verified, city-by-city options for getting rid of couches, mattresses, furniture and appliances: city pickup, donation pickup, drop-off, furniture banks and haulers.", "/", body, faq_ld([cmp_q]) if cmp_q else None)

def about(cities):
    set_page("/about/")
    ls = [l for c in cities for l in c["listings"]]
    nsrc = len({u for l in ls for u in l["source_urls"]})
    dates = sorted(l["last_verified"] for l in ls)
    nns = sum(1 for l in ls for k in ("condition_rules", "stairs_inside", "lead_time", "cost", "service_area")
              if (l.get(k) or NS).strip().startswith(NS))
    cl = ", ".join(f'<a href="{U("/" + c["slug"] + "/")}">{e(c["name"])}</a> ({len(c["listings"])})' for c in cities)
    nums = f"""<h2>By the numbers</h2>
<ul>
<li>{len(ls)} listings across {len(cities)} cities: {cl}, plus {len(GUIDES)} item guides.</li>
<li>{nsrc} distinct source pages cited, each linked from the listing that uses it.</li>
<li>Listings were last verified between {e(dates[0])} and {e(dates[-1])}.</li>
<li>{nns} listing fields say <span class="ns">{e(NS)}</span> because the source doesn't state them. We don't fill those in with guesses.</li>
</ul>
<p class="meta">These counts are computed from the site's data each time it's built. This page was last updated {e(ABOUT_UPDATED)}.</p>"""
    body = """<h1>About ByeBulky &amp; how we verify</h1>
<h2>How we verify</h2>
<ul>
<li>Every listing comes from the organization's own website or an official government page (for example, the City of Boston's Public Works pages). Each listing links to its sources.</li>
<li>We never guess. If a source doesn't state something (a price, a lead time, whether they'll carry things down stairs), the listing says <span class="ns">Not stated, check with them</span>.</li>
<li>Costs appear only when the organization (or the city's official list) publishes them. Prices quoted from a city's list are labeled as such.</li>
<li>Each listing shows a "last verified" date. We re-check listings regularly, and sooner when someone reports a change.</li>
<li>We don't publish reviews or ratings.</li>
</ul>
<h2>Affiliate disclosure</h2>
<p>ByeBulky is free to use and is meant to earn money through affiliate or referral partnerships, for example a commission when you book a paid junk pickup through a partner link. <strong>Right now ByeBulky has no affiliate relationships, and no link on this site earns a commission.</strong> If that changes, affiliate links and partner booking widgets will be clearly labeled where they appear. Free and City options will always be listed, and placement will never be sold in a way that hides them.</p>
<h2>Analytics</h2>
<p>ByeBulky uses Google Analytics to collect aggregate traffic statistics, such as which pages are visited, so we can see what's useful. It doesn't collect your name or email, though Google may set cookies to tell visits apart. Details are in our <a href="../privacy/">privacy policy</a>.</p>
<h2>Corrections</h2>
<p>Rules change often. If a listing is wrong or out of date, let us know and we'll re-check it against the source and update the date.</p>""" + nums
    return page("About ByeBulky: how we verify listings & affiliate disclosure",
                "How ByeBulky verifies every listing against official sources, and how the site makes money (affiliate disclosure).", "/about/", body)

def privacy_page():
    set_page("/privacy/")
    vids = [(VIDEOS[k].get("heading", k).split(" (")[0], U(k)) for k in sorted(VIDEOS)]
    aff = """<h2>Affiliate links</h2>
<p><strong>ByeBulky has no affiliate relationships right now, and no link on this site earns a commission or carries an affiliate or tracking code.</strong> Because there are no affiliate links, the site sets no affiliate cookies. If we add affiliate links or a partner booking widget later, they'll be labeled where they appear, explained on our <a href="%s">about page</a>, and described here before they go live.</p>""" % U("/about/")
    body = privacy.body(CFG["site_name"], "byebulky.com", (CFG.get("ga_measurement_id") or "").strip(), vids, aff,
                        "City pages have a filter box and a type menu for narrowing the list.")
    return page("Privacy policy | ByeBulky",
                "What ByeBulky collects (Google Analytics, click-to-play YouTube videos, GitHub Pages hosting logs), what it doesn't, and how to opt out.",
                "/privacy/", body)

def check_links(out):
    """Fail the build if any internal href/src in the generated site points at a file that doesn't exist."""
    import posixpath
    from urllib.parse import urlparse as up, unquote
    sub = up(base_url()).path.rstrip("/")
    bad = []
    for f in out.rglob("*.html"):
        r = str(f.parent.relative_to(out)); rel_dir = "/" + ("" if r == "." else r)
        for u in re.findall(r'(?:href|src)="([^"]+)"', f.read_text()):
            u = html.unescape(u)
            if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", u, re.I): continue
            path = unquote(u.split("#")[0].split("?")[0])
            if not path: continue
            if path.startswith("/"):
                if sub and path.startswith(sub + "/"): path = path[len(sub):]
                tgt = posixpath.normpath(path)
            else:
                tgt = posixpath.normpath(posixpath.join(rel_dir, path))
            t = out / tgt.lstrip("/")
            if not (t.is_file() or (t / "index.html").is_file()):
                bad.append(f"{f.relative_to(out)} -> {u}")
    assert not bad, "Broken internal links:\n" + "\n".join(bad)
    return True

def load_all():
    cities = [json.loads(p.read_text()) for p in sorted((ROOT / "data/cities").glob("*.json"))]
    guides = [json.loads(p.read_text()) for p in sorted((ROOT / "data/guides").glob("*.json"))]
    return cities, guides

LLMS_SUMMARY = (CFG["tagline"] + " A directory of real options for getting rid of couches, mattresses, furniture and "
                "appliances: City bulk and mattress pickup, charities that pick up, drop-off spots, furniture banks and paid haulers.")
LLMS_NOTES = ["Every listing comes from the organization's own website or an official government page, links to its sources, "
              "and shows the date it was last verified. When a source doesn't state something, the listing says "
              f'"{NS}". ByeBulky publishes no reviews or ratings.']
LLMS_SECTIONS = [("Cities", lambda p: p.count("/") == 2 and p not in ("/", "/about/", "/privacy/", COST_PATH)),
                 ("Cost comparisons", lambda p: p == COST_PATH),
                 ("Item guides", lambda p: p.count("/") == 3),
                 ("Home, about and privacy", lambda p: p in ("/", "/about/", "/privacy/"))]

# Search and AI-answer crawlers we explicitly welcome (one robots.txt group, RFC 9309).
# The catch-all group below allows everyone else too; this list just makes intent explicit.
ALLOWED_BOTS = ["Googlebot", "Bingbot", "Applebot", "DuckDuckBot", "DuckAssistBot", "OAI-SearchBot", "ChatGPT-User",
                "PerplexityBot", "Perplexity-User", "Claude-SearchBot", "Claude-User", "ClaudeBot", "YandexBot",
                "SeznamBot", "Yeti", "MojeekBot", "GPTBot", "Google-Extended", "Applebot-Extended",
                "Amazonbot", "meta-externalagent", "CCBot"]
def robots_txt(base):
    group = "".join(f"User-agent: {b}\n" for b in ALLOWED_BOTS)
    return (f"# {CFG['site_name']}: search engines and AI answer engines are welcome.\n"
            f"{group}Allow: /\n\nUser-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")

def llms_txt(base, pages):
    """/llms.txt (llmstxt.org format) built only from the site's own page titles and meta descriptions."""
    def item(path):
        t, d = META[path]
        return f"- [{t}]({base}{path}): {d}"
    out = [f"# {CFG['site_name']}", "", f"> {LLMS_SUMMARY}", ""] + LLMS_NOTES + [""]
    for heading, test in LLMS_SECTIONS:
        items = [item(p) for p in pages if test(p)]
        if items: out += [f"## {heading}", ""] + items + [""]
    out += ["## Optional", "", f"- [Sitemap]({base}/sitemap.xml): every page with a lastmod date", ""]
    return "\n".join(out)


GUIDES = []
CITIES = []
def main():
    global GUIDES, CITIES
    cities, GUIDES = load_all()
    CITIES = cities
    for c in cities:
        ids = [l["id"] for l in c["listings"]]
        assert len(ids) == len(set(ids)), f"duplicate listing ids in {c['slug']}"
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    bycity = {c["slug"]: c for c in cities}
    def city_mod(c): return max([c["last_verified"]] + [l["last_verified"] for l in c["listings"]])
    for c in cities: MODIFIED[f"/{c['slug']}/"] = city_mod(c)
    for g in GUIDES:
        used = [l["last_verified"] for l in bycity[g["city"]]["listings"] if l["id"] in g.get("listing_ids", [])]
        MODIFIED[f"/{g['path']}/"] = max([g["last_verified"]] + used)
    MODIFIED["/"] = max(city_mod(c) for c in cities)
    MODIFIED["/about/"] = ABOUT_UPDATED
    MODIFIED["/privacy/"] = PRIVACY_UPDATED
    mg = [g for g in GUIDES if g["short"] == "Mattress"]
    MODIFIED[COST_PATH] = max(MODIFIED[f"/{g['path']}/"] for g in mg)
    pages = {"/": home(cities), "/about/": about(cities), "/privacy/": privacy_page()}
    for c in cities: pages[f"/{c['slug']}/"] = city_page(c)
    for g in GUIDES: pages[f"/{g['path']}/"] = guide_page(g, bycity[g["city"]])
    pages[COST_PATH] = mattress_cost_page()
    for path, h in pages.items():
        d = OUT / path.strip("/"); d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(h)
    global PREFIX
    from urllib.parse import urlparse
    PREFIX = urlparse(base_url()).path.rstrip("/") + "/"   # 404 can be served at any depth
    (OUT / "404.html").write_text(page("Page not found | ByeBulky", "Page not found.", "/404.html", f'<h1>Page not found</h1><p><a href="{U("/")}">Go to the home page</a></p>'))
    base = base_url()
    today = datetime.date.today().isoformat()
    def lastmod(path):
        return MODIFIED.get(path, today)
    urls = "".join(f"<url><loc>{base}{p}</loc><lastmod>{lastmod(p)}</lastmod></url>" for p in pages)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    if CFG.get("indexnow_key"):  # IndexNow (Bing/Yandex) key file must sit at the site root
        (OUT / f"{CFG['indexnow_key']}.txt").write_text(CFG["indexnow_key"])
    (OUT / "robots.txt").write_text(robots_txt(base))
    (OUT / "llms.txt").write_text(llms_txt(base, pages))
    if (ROOT / "BingSiteAuth.xml").exists():  # Bing Webmaster Tools verification file, must sit at the site root
        shutil.copyfile(ROOT / "BingSiteAuth.xml", OUT / "BingSiteAuth.xml")
    if CFG.get("cname"):
        (OUT / "CNAME").write_text(CFG["cname"].strip() + "\n")
    check_links(OUT)
    print(f"Built {len(pages)} pages (internal links OK), {sum(len(c['listings']) for c in cities)} listings -> {OUT}")

if __name__ == "__main__":
    main()
