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
TYPES = ["city bulk pickup", "charity pickup", "drop-off", "furniture bank", "paid hauler", "retailer haul-away", "utility recycling program"]
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

_DAYW = re.compile(r"\b(?:day|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|weekly)s?\b", re.I)
def _day_sent(s):
    """First verbatim sentence of a lead_time that names a day; falls back to the first sentence."""
    s = (s or "").strip(); rest = s
    while rest:
        one = _sent(rest)
        if _DAYW.search(one):
            return one
        rest = rest[len(one):].strip()
        if one == s and not rest: break
    return _sent(s)

def pickup_day_faq(c):
    """'What day is bulky item pickup in {city}?' (Google autocomplete, run #44). Verbatim day sentences from the City's
    own furniture, mattress and appliance listings; says so when the official page names no day."""
    city = c["name"]; parts = []; missing = []
    for label, rx in RULE_KINDS:
        l = next((x for x in c["listings"] if x["type"] == "city bulk pickup" and rx.search(x["id"])), None)
        lt = (l or {}).get("lead_time", "")
        if not l or lt.startswith("Not stated"):
            missing.append(label.lower()); continue
        ds = _day_sent(lt)
        hit = next((x for x in parts if x[1] == ds), None)
        if hit: hit[0].append(label.lower())
        else: parts.append([[label], ds])
    parts = [f"{(', '.join(ls[:-1]) + ' and ' + ls[-1]) if len(ls) > 1 else ls[0]}: {ds}" for ls, ds in parts]
    if not parts:
        return None
    a = " ".join(parts)
    if missing:
        a += f" The City page we checked doesn't give a day for {' or '.join(missing)}; ask the City."
    return {"q": f"What day is bulky item pickup in {city}?", "a": a}

def _city_prog(c, k):
    rx = RULE_KINDS[k][1]
    return next((x for x in c["listings"] if x["type"] == "city bulk pickup" and rx.search(x["id"])), None)

def mattress_bulk_faq(c):
    """'Does bulk pickup take mattresses in {city}?' (top Search Console query, run #45). Built only from the City's own
    furniture and mattress listings: the furniture listing's verbatim mattress exclusion, the mattress program's name,
    first cost sentence, day sentence and verbatim not-accepted items."""
    city = c["name"]; fur = _city_prog(c, 0); mat = _city_prog(c, 1)
    if not mat:
        return None
    excl = next((i for i in (fur or {}).get("items_not_accepted", []) if re.search(r"mattress", i, re.I)), None)
    a = (f"Not with regular bulky item pickup. {city}'s furniture pickup listing names this as not accepted: \"{excl}.\" "
         if excl else f"{city} collects mattresses through a separate program from its furniture pickup. ")
    a += f"The official mattress option is {mat['name']}. Cost: {_sent(mat.get('cost'))}"
    lt = mat.get("lead_time", "")
    if lt and not lt.startswith("Not stated"):
        a += f" When: {_day_sent(lt)}"
    na = [i for i in mat.get("items_not_accepted", []) if not re.match(r"other non-mattress", i, re.I)]
    if na:
        a += " Not accepted by that program: " + "; ".join(na) + "."
    return {"q": f"Does bulk pickup take mattresses in {city}?", "a": a.strip()}

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
    if not any(_DAYW.search(x["q"]) and x["q"].lower().startswith("what day") for x in c.get("quick_answers", [])):
        d = pickup_day_faq(c)
        if d: out.insert(0, d)
    m = mattress_bulk_faq(c)
    if m: out.insert(1 if out and out[0]["q"].startswith("What day") else 0, m)
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
                 "retailer haul-away": "Retailer haul-away for {city} residents",
                 "utility recycling program": "Utility appliance recycling programs for {city} residents"}

def type_heading(t, city):
    return TYPE_HEADINGS.get(t, t.title()).format(city=city)

def mattress_spot(c):
    """Hub -> mattress guide contextual link (run #50, cannibalization fix): SC showed "mattress removal somerville"
    split between /somerville/ and /somerville/mattress/. The hub stays on general bulky items and hands mattress
    intent to the dedicated guide with the target anchor. Count is computed from the guide's listing_ids."""
    g = next((x for x in GUIDES if x["city"] == c["slug"] and x["short"] == "Mattress"), None)
    if not g: return ""
    n = len(g.get("listing_ids", []))
    return (f'<p><strong>Getting rid of a mattress?</strong> See our <a href="{U("/" + g["path"] + "/")}">{e(c["name"])} mattress removal '
            f'and pickup guide</a>: {n} option{"s" if n != 1 else ""} with cost, booking steps and sources.</p>')

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
<h1>{e(c.get('h1') or ('How to get rid of a couch, mattress or furniture in ' + c['name']))}</h1>
<p class="lead">{e(c['intro'])}</p>
<p class="meta">{len(c['listings'])} options · every listing links to its source · last verified {e(c['last_verified'])}{(" · page updated " + e(MODIFIED[f"/{c['slug']}/"])) if MODIFIED.get(f"/{c['slug']}/", c['last_verified']) != c['last_verified'] else ""}</p>
<div class="qa">{qa}</div>
{mattress_spot(c)}
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
    if g.get("short") in ("Mattress", "Couch", "Appliances"):  # rules table + cost checker only cover these items
        cost += rules_link(next((c["name"] for c in CITIES if c["slug"] == g["city"]), "your city"),
                           {"mattress": "mattress", "appliances": "fridge"}.get(g.get("short", "").lower(), "couch"))
    if not oth: return cost
    return cost + (f"<h2>{e(g['short'])} guides for other cities</h2><ul>" + "".join(
        f'<li><a href="{U("/" + x["path"] + "/")}">{e(cmap[x["city"]]["name"])}: {e(x["title"])}</a> '
        f'({len(x.get("listing_ids", []))} options)</li>' for x in oth) + "</ul>")

def rules_link(name, item="couch"):
    """Contextual link to the cross-city rules table (run #38): each city/guide page points to the comparison."""
    n = len(CITIES) - 1
    c = next((x for x in CITIES if x["name"] == name), None)
    tool = (f' Or use the <a href="{U(TOOL_PATH)}#r-{e(c["slug"])}-{item}">cost checker</a> to see every {e(name)} option for one item.' if c else "")
    return (f'<p>How does {e(name)} compare? See the <a href="{U(RULES_PATH)}">furniture, mattress and appliance pickup rules '
            f'for {e(name)} and {n} other Boston-area cities side by side</a>, with official sources.{tool}</p>')

def nocar_link(c):
    """City hub -> no-car/big-building audience page (run #40). Count is computed from this city's own listings:
    pickups (not City programs) whose stairs_inside text starts with "Yes"."""
    k = sum(1 for l in c["listings"] if l["type"] != "city bulk pickup" and _comes_to_you(l)
            and (l.get("stairs_inside") or "").startswith("Yes"))
    lead = (f'{k} pickup option{"s" if k != 1 else ""} listed for {e(c["name"])} {"say they come inside or handle stairs" if k != 1 else "says it comes inside or handles stairs"}. '
            if k else "")
    return (f'<p>No car, upstairs apartment or big building? {lead}See <a href="{U(NOCAR_PATH)}">pickups that come to you around Boston, '
            f'with each option\'s inside/stairs wording and each City\'s building-size rules</a>.</p>')

def other_city_hubs(c):
    oth = [o for o in CITIES if o["slug"] != c["slug"]]
    if not oth: return rules_link(c["name"]) + nocar_link(c)
    def gcount(o): return len([x for x in GUIDES if x["city"] == o["slug"]])
    return rules_link(c["name"]) + nocar_link(c) + ("<h2>Other Boston-area cities we cover</h2><ul>" + "".join(
        f'<li><a href="{U("/" + o["slug"] + "/")}">{e(o["name"])}, {e(o["state"])}</a> ({len(o["listings"])} options'
        + (f', {gcount(o)} item guide{"s" if gcount(o) != 1 else ""}' if gcount(o) else '') + ')</li>' for o in oth) + "</ul>")

def sibling_guides(g, city):
    """Contextual internal links (added 2026-10-24): other item guides for the same city."""
    sib = [x for x in GUIDES if x["city"] == city["slug"] and x["path"] != g["path"]]
    if not sib: return ""
    return f"<h2>More {e(city['name'])} item guides</h2><ul>" + "".join(
        f'<li><a href="{U("/" + x["path"] + "/")}">{e(x["title"])}</a></li>' for x in sib) + "</ul>"

ITEM_PHRASE = {"Mattress": "a mattress", "Couch": "a couch or sofa", "Appliances": "a fridge, AC, TV or other appliance",
               "September 1 move-out": "furniture, mattresses and appliances when moving out", "Donation rules": "furniture by donating it"}

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
    secs = "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" + (('<p class="meta">Sources: ' + " · ".join(f'<a href="{e(r["url"])}" rel="nofollow noopener" target="_blank">{e(r["label"])}</a>' for r in s["sources"]) + '</p>') if s.get("sources") else "") for s in g.get("sections", []))
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
    return page("Boston Mattress Disposal Cost: City Fees & Hauler Prices",
                f"City mattress pickup fees and published hauler prices for {', '.join(names[:-1])} and {names[-1]}, with official sources.",
                COST_PATH, body, [x for x in lds if x])

RULES_PATH = "/boston-area-bulky-item-pickup-compared/"
RULE_KINDS = [("Furniture & bulky items", re.compile(r"furniture|bulky-item")),
              ("Mattresses & box springs", re.compile(r"mattress")),
              ("Fridges & big appliances", re.compile(r"appliance|white|special-items"))]
_ABBR = re.compile(r"(?:\b[ap]\.m|\betc|\bSt|\bAve|\bNo|\bDr)\.$")
def _sent(s):
    """First sentence, verbatim, without cutting at abbreviations like 'p.m.' or 'etc.'."""
    s = (s or "").strip()
    for m in re.finditer(r"\. ", s):
        if not _ABBR.search(s[:m.start() + 1]):
            return s[:m.start() + 1]
    return s

def _fee_class(cost):
    c = (cost or "").strip()
    if c.lower().startswith("free"): return "free"
    if "$" in _sent(c): return "paid"
    return "unstated"

def rules_rows():
    """Per city, the City's own pickup program for each item kind (city bulk pickup listings only). Cells are verbatim
    first sentences of listing fields; nothing new is claimed. Added run #37 (first-party data table, WordsAtScale/Gotch)."""
    out = []
    for c in CITIES:
        cells = []
        for label, rx in RULE_KINDS:
            l = next((x for x in c["listings"] if x["type"] == "city bulk pickup" and rx.search(x["id"])), None)
            cells.append(l)
        out.append((c, cells))
    return out

def rules_cell(c, l):
    if not l:
        return '<td><span class="ns">No separate City program on our page</span></td>'
    gp = next((g for g in GUIDES if g["city"] == c["slug"] and l["id"] in g.get("listing_ids", [])), None)
    href = U(f"/{gp['path']}/" if gp else f"/{c['slug']}/") + "#" + l["id"]
    src = " ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">source {i + 1}</a>' for i, u in enumerate(l.get("source_urls", [])[:2]))
    lt = _sent(l.get("lead_time"))
    return (f'<td><strong>{val(_sent(l.get("cost")))}</strong>'
            + (f'<br>When: {val(lt)}' if lt else "")
            + f'<br><a href="{href}">details</a> · {src}<br><span class="meta">checked {e(l.get("last_verified", ""))}</span></td>')

def rules_faq(rows):
    qas = []
    for k, (label, _) in enumerate(RULE_KINDS):
        groups = {"free": [], "paid": [], "unstated": []}
        for c, cells in rows:
            l = cells[k]
            if l: groups[_fee_class(l.get("cost"))].append((c, l))
        noun = label.lower()
        parts = []
        if groups["free"]: parts.append("Free per the official pages: " + " ".join(f'{c["name"]}: {_sent(l["cost"])}' for c, l in groups["free"]))
        if groups["paid"]: parts.append("Fee charged: " + " ".join(f'{c["name"]}: {_sent(l["cost"])}' for c, l in groups["paid"]))
        if groups["unstated"]: parts.append("No fee stated on the official page (ask the City): " + ", ".join(c["name"] for c, _ in groups["unstated"]) + ".")
        qas.append({"q": f"Which Boston-area cities pick up {noun} for free, and what do the others charge?",
                    "a": " ".join(parts)})
    days = []
    for c, cells in rows:
        l = cells[0]
        if l and not l.get("lead_time", "").startswith("Not stated"):
            days.append(f'{c["name"]}: {_day_sent(l["lead_time"])}')
    if days:
        qas.append({"q": "What day is bulky item pickup in Boston-area cities?",
                    "a": "For furniture and other bulky items, per each City's own page: " + " ".join(days)
                         + " Mattresses and appliances can have a separate day or booking step; see each city's page."})
    mats = []
    for c, cells in rows:
        f, m = cells[0], cells[1]
        if not m: continue
        sep = bool(f and any(re.search(r"mattress", i, re.I) for i in f.get("items_not_accepted", [])))
        mats.append(f'{c["name"]}: {"not with furniture pickup; " if sep else ""}{m["name"]}, {_sent(m.get("cost"))}')
    if mats:
        qas.append({"q": "Does bulk pickup take mattresses in Boston-area cities?",
                    "a": f"Each of these {len(mats)} cities handles mattresses through its own mattress program, per the City pages we checked. " + " ".join(mats)})
    return qas

def rules_page():
    """Linkable first-party data table: every City's own furniture, mattress and appliance pickup side by side."""
    set_page(RULES_PATH)
    rows = rules_rows()
    names = [c["name"] for c in CITIES]
    tr = "".join(f'<tr><th scope="row"><a href="{U("/" + c["slug"] + "/")}">{e(c["name"])}, {e(c["state"])}</a></th>'
                 + "".join(rules_cell(c, l) for l in cells) + "</tr>" for c, cells in rows)
    qas = rules_faq(rows)
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › Bulky item pickup compared</p>
<h1>Bulky item pickup around Boston compared: furniture, mattresses and appliances by city</h1>
<p class="lead">Every city around Boston runs its own bulky item rules: some pick up furniture free with the trash, others charge per item, and mattresses and fridges usually have their own fee and booking step. This table puts the official City or Town program for {e(', '.join(names[:-1]))} and {e(names[-1])} side by side. Each cell comes from the official page linked in it and shows when we last checked it. Where the official page doesn't state a fee, we say so instead of guessing.</p>
<p class="meta">Page updated {e(MODIFIED.get(RULES_PATH, ''))}.</p>
<div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">City</th>""" + "".join(f'<th scope="col">{e(k)}</th>' for k, _ in RULE_KINDS) + f"""</tr></thead><tbody>{tr}</tbody></table></div>
<p>City programs only cover residents the City collects trash for; many larger apartment buildings use private trash service. Check the "details" link for who qualifies. If the City option doesn't fit, each city page also lists charity pickups, drop-off spots, furniture banks and paid haulers.</p>
<h2>Quick answers</h2>{qa_block(qas)}
{yt_embed(RULES_PATH, YT_CHANNEL, 'ByeBulky')}
<p><a href="{U(COST_PATH)}">Mattress disposal cost around Boston, including published hauler prices →</a></p>
<p><a href="{U(NOCAR_PATH)}">No car, upstairs apartment or big building? Pickups that come to you →</a></p>
<p><a href="{U(TOOL_PATH)}">Check one city and item: bulky item pickup cost checker →</a></p>
<h2>City pages</h2><ul>""" + "".join(f'<li><a href="{U("/" + c["slug"] + "/")}">{e(c["title"])}</a></li>' for c in CITIES) + "</ul>"
    lds = [faq_ld(qas), crumbs_ld([("Home", "/"), ("Bulky item pickup compared", RULES_PATH)])]
    return page("Boston-Area Bulky Item Pickup Rules Compared by City",
                f"Furniture, mattress and appliance pickup fees and booking rules for {', '.join(names[:-1])} and {names[-1]}, side by side with official sources.",
                RULES_PATH, body, lds)

NOCAR_PATH = "/no-car-apartment-bulky-item-pickup-boston/"
def _all_listings():
    """Unique listings across cities (same id = same listing), with the cities whose page lists it."""
    out = {}
    for c in CITIES:
        for l in c["listings"]:
            out.setdefault(l["id"], {"l": l, "cities": []})["cities"].append(c)
    return list(out.values())

def _comes_to_you(l):
    """Pickup options (not drop-off), judged only from the listing's own type and stairs_inside text."""
    si = (l.get("stairs_inside") or "").strip()
    return l["type"] != "drop-off" and not re.match(r"No\. (Drop-off|You bring)", si)

def _nocar_groups():
    inside, cond = [], []
    for r in _all_listings():
        l = r["l"]
        if l["type"] == "city bulk pickup" or not _comes_to_you(l):
            continue
        (inside if (l.get("stairs_inside") or "").startswith("Yes") else cond).append(r)
    return inside, cond

def _where(r):
    return ", ".join(f'<a href="{U("/" + c["slug"] + "/")}#{e(r["l"]["id"])}">{e(c["name"])}</a>' for c in r["cities"])

def _src(l):
    return (" ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">source {i + 1}</a>' for i, u in enumerate(l.get("source_urls", [])[:2]))
            + f'<br><span class="meta">checked {e(l.get("last_verified", ""))}</span>')

def _nocar_table(rs):
    tr = "".join(f'<tr><th scope="row">{e(r["l"]["name"])}</th><td>{e(r["l"]["type"])}</td><td>{val(_cell(r["l"].get("stairs_inside"), 220))}</td>'
                 f'<td>{val(_cell(r["l"].get("cost"), 220))}</td><td>{_where(r)}</td><td>{_src(r["l"])}</td></tr>' for r in rs)
    return ('<div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">Option</th><th scope="col">Type</th>'
            '<th scope="col">Inside / stairs (their words)</th><th scope="col">Cost</th><th scope="col">Listed for</th>'
            f'<th scope="col">Source</th></tr></thead><tbody>{tr}</tbody></table></div>')

def nocar_page():
    """Audience-specific comparison (run #39; Ahrefs GEO experts video, run #35): renters with no car, upstairs units or
    big buildings. Every cell is a verbatim listing field; groups are computed from listing type + stairs_inside text."""
    set_page(NOCAR_PATH)
    inside, cond = _nocar_groups()
    city_rows, other, curb_n = "", [], 0
    for c in CITIES:
        for l in c["listings"]:
            if l["type"] != "city bulk pickup": continue
            si = (l.get("stairs_inside") or "").strip()
            if si.startswith("No."): curb_n += 1
            else: other.append(l["name"])
            city_rows += (f'<tr><th scope="row"><a href="{U("/" + c["slug"] + "/")}#{e(l["id"])}">{e(l["name"])}</a></th>'
                          f'<td>{val(_cell(l.get("service_area"), 260))}</td><td>{val(_cell(si))}</td><td>{val(_cell(l.get("cost")))}</td><td>{_src(l)}</td></tr>')
    n_city = sum(1 for c in CITIES for l in c["listings"] if l["type"] == "city bulk pickup")
    names = [c["name"] for c in CITIES]
    big = [(c, l) for c in CITIES for l in c["listings"] if l["type"] == "city bulk pickup"
           and re.search(r"\d+\s*(?:\+\s*)?units|more than (?:\w+ )?units|\d+-family|multi-family", (l.get("service_area") or ""))]
    qas = [
        {"q": "Who will carry a couch or mattress out of my apartment or down the stairs around Boston?",
         "a": "Of the pickup options we list, these say on their own page (or the City's list) that they come inside or handle stairs: "
              + " ".join(f'{r["l"]["name"]}: {_cell(r["l"]["stairs_inside"], 200)}' for r in inside)
              + " Confirm the price and access details with them before you book."},
        {"q": "Will the City come inside to pick up furniture, a mattress or an appliance?",
         "a": f"No, not per the official pages we cite: {curb_n} of the {n_city} City or Town pickup programs we list for {', '.join(names[:-1])} and {names[-1]} "
              "say curbside only, so the item has to be at the curb (or where trash is collected) on pickup day."
              + ("" if not other else f" The page for {_names([{'name': x} for x in other])} doesn't say either way; check with the City.")},
        {"q": "I live in a big apartment building. Can I use City bulky item or mattress pickup?",
         "a": "It depends on the building size and who collects your trash. The official pages say: "
              + " ".join(f'{c["name"]} ({l["name"]}): {l["service_area"]}' for c, l in big)},
        {"q": "Can I get rid of a bulky item without a car?",
         "a": f"Yes. Besides City curbside pickup, we list {len(inside) + len(cond)} charity pickups, furniture banks, haulers and other programs that come to you. "
              f"{len(inside)} of them say they will come inside or handle stairs; for the others, access is limited or not stated, so ask when you book."},
    ]
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › No car or big building</p>
<h1>No car, upstairs apartment or big building? Bulky item pickup options around Boston</h1>
<p class="lead">If you rent, don't have a car, live up a few flights, or live in a building too big for City pickup, most of the usual advice doesn't fit. This page pulls together every option on our {e(', '.join(names[:-1]))} and {e(names[-1])} pages that comes to you, and shows in each source's own words whether they come inside or carry things down stairs, what they charge, and which buildings the City programs cover. Every cell comes from the official page or the company's own page linked in its row, with the date we last checked it.</p>
<p class="meta">Page updated {e(MODIFIED.get(NOCAR_PATH, ''))}.</p>
<h2 id="inside">They say they'll come inside or handle stairs ({len(inside)})</h2>
<p>These options state that they remove items from inside or up and down stairs. Extra fees can apply; the cost column shows only what the source publishes.</p>
{_nocar_table(inside)}
<h2 id="other-pickups">Other pickups that come to you ({len(cond)})</h2>
<p>These charities, furniture banks, programs and haulers pick up, but inside or stairs pickup is limited or not stated on their page. Ask before you book.</p>
{_nocar_table(cond)}
<h2 id="city-programs">City and Town pickup: curbside only, and who qualifies ({n_city} programs)</h2>
<p>Per the official pages, City and Town programs collect at the curb, and several exclude larger apartment buildings. The "Who qualifies" column is the City's own wording.</p>
<div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">City program</th><th scope="col">Who qualifies</th><th scope="col">Inside / stairs</th><th scope="col">Cost</th><th scope="col">Source</th></tr></thead><tbody>{city_rows}</tbody></table></div>
<h2>Quick answers</h2>{qa_block(qas)}
<p><a href="{U(RULES_PATH)}">Furniture, mattress and appliance pickup rules compared by city →</a></p>
<p><a href="{U(COST_PATH)}">Mattress disposal cost around Boston, including published hauler prices →</a></p>
<h2>City pages</h2><ul>""" + "".join(f'<li><a href="{U("/" + c["slug"] + "/")}">{e(c["title"])}</a></li>' for c in CITIES) + "</ul>"
    lds = [faq_ld(qas), crumbs_ld([("Home", "/"), ("No car or big building", NOCAR_PATH)])]
    return page("No Car or Big Building? Bulky Item Pickup Around Boston",
                f"Pickups that come to you in {', '.join(names[:-1])} and {names[-1]}: who comes inside or handles stairs, what they charge, and which buildings City pickup covers.",
                NOCAR_PATH, body, lds)

TOOL_PATH = "/bulky-item-pickup-cost-checker/"
TOOL_ITEMS = [("couch", "Couch, sofa or other furniture", 0, "couch"), ("mattress", "Mattress or box spring", 1, "mattress"),
              ("fridge", "Fridge or other large appliance", 2, "refrigerator or other large appliance")]
TOOL_NOUN = {"couch": "couch", "mattress": "mattress", "fridge": "fridge or large appliance"}
_FEE_LABEL = {True: "$ amount listed", False: "No $ amount listed"}
def _has_amt(l):
    """Purely textual: does the source's cost wording include a dollar amount? (No free/paid judgement: 'Free quote',
    suggested donations and 'starts at' prices all read differently, so the tool only reports what is literally listed.)"""
    return "$" in (l.get("cost") or "")

def tool_options(c, k, item_key):
    """City program for item kind k (same rule as the rules table) + every other listing on the city page that takes the item
    (takes_item on items_accepted). Nothing new is claimed: cells are verbatim listing fields."""
    rx = dict(ITEM_RX)[item_key]
    prog = next((x for x in c["listings"] if x["type"] == "city bulk pickup" and RULE_KINDS[k][1].search(x["id"])), None)
    others = [l for l in c["listings"] if (not prog or l["id"] != prog["id"]) and l["type"] != "city bulk pickup" and takes_item(l, rx, item_key)]
    others.sort(key=lambda l: (not _has_amt(l), l["name"].lower()))
    return prog, others

def _tool_href(c, l):
    gp = next((g for g in GUIDES if g["city"] == c["slug"] and l["id"] in g.get("listing_ids", [])), None)
    return U(f"/{gp['path']}/" if gp else f"/{c['slug']}/") + "#" + l["id"]

def tool_result(c, slug, label, k, item_key):
    prog, others = tool_options(c, k, item_key)
    if prog:
        lt = _sent(prog.get("lead_time"))
        city = (f'<div class="card"><span class="badge">City program</span><h3><a href="{_tool_href(c, prog)}">{e(prog["name"])}</a></h3><dl>'
                f'<dt>Cost</dt><dd><strong>{val(_sent(prog.get("cost")))}</strong></dd>'
                + (f'<dt>When</dt><dd>{val(lt)}</dd>' if lt else "")
                + f'<dt>Who qualifies</dt><dd>{val(_cell(prog.get("service_area"), 260))}</dd>'
                f'<dt>Inside / stairs</dt><dd>{val(_cell(prog.get("stairs_inside")))}</dd>'
                f'<dt>Source</dt><dd>{_src(prog)}</dd></dl></div>')
    else:
        city = f'<p><span class="ns">Our {e(c["name"])} page has no separate City program for this item.</span> See the <a href="{U("/" + c["slug"] + "/")}">{e(c["name"])} page</a> for City trash rules.</p>'
    tr = "".join(f'<tr><th scope="row"><a href="{_tool_href(c, l)}">{e(l["name"])}</a></th><td>{e(l["type"])}</td>'
                 f'<td><span class="meta">{e(_FEE_LABEL[_has_amt(l)])}</span><br>{val(_cell(l.get("cost"), 220))}</td>'
                 f'<td>{val(_cell(l.get("stairs_inside"), 160))}</td><td>{_src(l)}</td></tr>' for l in others)
    tbl = ('<div class="tablewrap"><table class="cmp"><thead><tr><th scope="col">Option</th><th scope="col">Type</th><th scope="col">Cost (their words)</th>'
           f'<th scope="col">Inside / stairs</th><th scope="col">Source</th></tr></thead><tbody>{tr}</tbody></table></div>') if others else '<p class="ns">No other options on our page list this item.</p>'
    return (f'<section class="tool-result" id="r-{e(c["slug"])}-{slug}" data-city="{e(c["slug"])}" data-item="{slug}">'
            f'<h2>{e(label)} in {e(c["name"])}, {e(c["state"])}</h2>'
            f'<h3>The {e(c["name"])} City program</h3>{city}'
            f'<h3>Other options in {e(c["name"])} that list this item ({len(others)})</h3>{tbl}'
            f'<p><a href="{U("/" + c["slug"] + "/")}">All {e(c["name"])} options →</a></p></section>')

TOOL_JS = """<script>
(function(){var c=document.getElementById('tc'),i=document.getElementById('ti');if(!c)return;
function show(){var id='r-'+c.value+'-'+i.value;document.querySelectorAll('section.tool-result').forEach(function(s){s.hidden=(s.id!==id);});
var n=document.getElementById('tall');if(n)n.hidden=false;}
var h=location.hash.match(/^#r-([a-z-]+)-(couch|mattress|fridge)$/);if(h){c.value=h[1];i.value=h[2];}
c.addEventListener('change',show);i.addEventListener('change',show);show();
var a=document.getElementById('tall');if(a)a.addEventListener('click',function(ev){ev.preventDefault();document.querySelectorAll('section.tool-result').forEach(function(s){s.hidden=false;});});})();
</script>"""

def tool_stats():
    """Computed counts across all city pages (unique listing ids per item), for the methodology/Quick answers."""
    out = []
    for slug, label, k, item_key in TOOL_ITEMS:
        rx = dict(ITEM_RX)[item_key]; seen = {}
        for c in CITIES:
            for l in c["listings"]:
                if takes_item(l, rx, item_key) or (l["type"] == "city bulk pickup" and RULE_KINDS[k][1].search(l["id"])):
                    seen[l["id"]] = l
        amt = sum(1 for l in seen.values() if _has_amt(l))
        out.append((slug, label, len(seen), amt, len(seen) - amt))
    return out

def tool_page():
    """Free interactive checker (run #42; Ahrefs 'free tools dodge AI Overviews', Edward Sturm 'stat with a sample size
    and a date gets quoted'). All 18 city x item results are rendered server-side (crawlable); JS only hides the others."""
    set_page(TOOL_PATH)
    names = [c["name"] for c in CITIES]
    copt = "".join(f'<option value="{e(c["slug"])}">{e(c["name"])}, {e(c["state"])}</option>' for c in CITIES)
    iopt = "".join(f'<option value="{s}">{e(l)}</option>' for s, l, _, _ in TOOL_ITEMS)
    results = "".join(tool_result(c, s, l, k, ik) for c in CITIES for s, l, k, ik in TOOL_ITEMS)
    st = tool_stats()
    nlist = len({l["id"] for c in CITIES for l in c["listings"]})
    stat_li = "".join(f'<li>{e(l)}: {n} options listed across the {len(CITIES)} cities. {a} list a dollar amount in their cost wording; {u} list none (no fee mentioned, free, quote only, or not stated).</li>' for _, l, n, a, u in st)
    qas = [{"q": f"How do I find out what my city charges to pick up a {w}?",
            "a": f"Pick your city and item on the ByeBulky bulky item pickup cost checker. It shows the City or Town program's fee in the official page's own words, "
                 f"when it collects and who qualifies, plus every other option on our {', '.join(names[:-1])} and {names[-1]} pages that lists the item, each with its source and the date we checked it."}
           for w in ("couch, mattress or fridge",)]
    for sl, l, n, a, u in st:
        qas.append({"q": f"How many Boston-area options publish a price for getting rid of a {TOOL_NOUN[sl]}?",
                    "a": f"Of the {n} options on our {', '.join(names[:-1])} and {names[-1]} pages that list {l.lower()}, {a} include a dollar amount in their published cost wording "
                         f"and {u} don't (the source says no fee, free, quote only, or doesn't say). Counts are from our data as of {MODIFIED.get(TOOL_PATH, '')}; pick a city above to read each one's own wording."})
    mod = MODIFIED.get(TOOL_PATH, "")
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › Bulky item pickup cost checker</p>
<h1>Bulky item pickup cost checker: what will my city charge?</h1>
<p class="lead">Pick your city and what you're getting rid of. You'll see the City or Town pickup program's fee in the official page's own words, when it collects and who qualifies, then every charity, drop-off, furniture bank and hauler on our page for that city that lists the item, with its published cost. Nothing is estimated: if a source doesn't publish a price, we say so.</p>
<form class="filters" onsubmit="return false"><label>City <select id="tc">{copt}</select></label> <label>Item <select id="ti">{iopt}</select></label> <a href="#" id="tall" hidden>Show all cities and items</a></form>
<p class="meta">Data checked up to {e(mod)}. Covers {e(', '.join(names[:-1]))} and {e(names[-1])}.</p>
{results}
<h2 id="numbers">By the numbers</h2>
<ul>{stat_li}</ul>
{yt_embed(TOOL_PATH, YT_CHANNEL, 'ByeBulky')}
<h2 id="method">How this checker works (and what it doesn't do)</h2>
<ul>
<li>It reads the same listings shown on our city pages ({nlist} unique options). Each one comes from the organization's own site or an official City page, and links to it.</li>
<li>The City program is the City or Town listing for that item kind, the same one shown in the <a href="{U(RULES_PATH)}">rules compared table</a>. Its fee and collection day are the first sentence of the official wording, unchanged.</li>
<li>"Other options" are listings whose accepted-items list names the item (for couches, generic "Furniture" counts unless the listing excludes couches).</li>
<li>Options with a dollar amount in their cost wording are listed first. That amount may be a flat fee, a "starts at" price, a sticker or a suggested donation, so read the wording. The checker doesn't estimate prices, add taxes or fees, or check availability, and it doesn't cover cities we haven't researched yet.</li>
<li>Rules change. Confirm with the City or the organization before you put anything at the curb.</li>
</ul>
<h2>Quick answers</h2>{qa_block(qas)}
<p><a href="{U(RULES_PATH)}">Furniture, mattress and appliance pickup rules compared by city →</a></p>
<p><a href="{U(NOCAR_PATH)}">No car, upstairs apartment or big building? Pickups that come to you →</a></p>
<p><a href="{U(COST_PATH)}">Mattress disposal cost around Boston, including published hauler prices →</a></p>
{TOOL_JS}"""
    lds = [faq_ld(qas), crumbs_ld([("Home", "/"), ("Bulky item pickup cost checker", TOOL_PATH)]),
           {"@context": "https://schema.org", "@type": "WebApplication", "name": "ByeBulky bulky item pickup cost checker",
            "url": base_url() + TOOL_PATH, "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any",
            "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "description": "Shows the City pickup fee and every listed option for a couch, mattress or fridge in " + ", ".join(names) + ", from official sources."}]
    return page("Bulky Item Pickup Cost Checker: What Will My City Charge?",
                f"Pick your city and item to see the City pickup fee in its own words, plus every charity, drop-off and hauler that takes it, for {', '.join(names[:-1])} and {names[-1]}.",
                TOOL_PATH, body, lds)

def home(cities):
    set_page("/")
    cmp_html, cmp_q = home_mattress_compare(cities)
    cl = "".join(f'<a href="{U("/" + c["slug"] + "/")}">{e(c["name"])}, {e(c["state"])}<br><span class="meta">{len(c["listings"])} verified options</span></a>' for c in cities)
    body = f"""<h1>Get rid of a couch, mattress or old fridge without the runaround</h1>
<p class="lead">{e(CFG['tagline'])} For each city we list every real option: City bulk and mattress pickup, charities that pick up, drop-off spots, furniture banks, and paid haulers. You see what each one takes, its condition rules, whether it will come inside or up stairs, and its cost. A cost is only shown when the organization publishes it.</p>
<h2>Cities</h2><div class="cities">{cl}</div>
{cmp_html}
<p><a href="{U(COST_PATH)}">Mattress disposal cost around Boston, including published hauler prices →</a></p>
<p><a href="{U(RULES_PATH)}">Furniture, mattress and appliance pickup rules compared by city →</a></p>
<p><a href="{U(NOCAR_PATH)}">No car, upstairs apartment or big building? Pickups that come to you →</a></p>
<p><a href="{U(TOOL_PATH)}">Free tool: what will my city charge for a couch, mattress or fridge? →</a></p>
{yt_embed('/', YT_CHANNEL, 'ByeBulky')}
{home_guides(cities)}
<h2>Why this exists</h2>
<p>Charities change what they accept, some stop picking up furniture altogether, and city rules differ from one place to the next. People end up calling three places and still having a couch on the curb. We collect the rules from official sources, link every listing to its source, and date when we last checked it.</p>
<p class="meta">Listings last verified {e(MODIFIED.get('/', ''))}.</p>
<p><a href="{U('/about/')}">How we verify listings &amp; how this site makes money →</a></p>"""
    return page(f"{CFG['site_name']}: Get Rid of Furniture, Mattresses & Appliances",
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
    return page("About ByeBulky: How We Verify Listings & Disclosure",
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
LLMS_SECTIONS = [("Cities", lambda p: p.count("/") == 2 and p not in ("/", "/about/", "/privacy/", COST_PATH, RULES_PATH, NOCAR_PATH, TOOL_PATH)),
                 ("Comparisons and tools", lambda p: p in (COST_PATH, RULES_PATH, NOCAR_PATH, TOOL_PATH)),
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
    MODIFIED[RULES_PATH] = max(l["last_verified"] for c in cities for l in c["listings"] if l["type"] == "city bulk pickup")
    pages = {"/": home(cities), "/about/": about(cities), "/privacy/": privacy_page()}
    for c in cities: pages[f"/{c['slug']}/"] = city_page(c)
    for g in GUIDES: pages[f"/{g['path']}/"] = guide_page(g, bycity[g["city"]])
    pages[COST_PATH] = mattress_cost_page()
    pages[RULES_PATH] = rules_page()
    MODIFIED[NOCAR_PATH] = max(l["last_verified"] for c in cities for l in c["listings"] if l["type"] != "drop-off")
    pages[NOCAR_PATH] = nocar_page()
    MODIFIED[TOOL_PATH] = max(l["last_verified"] for c in cities for l in c["listings"])
    pages[TOOL_PATH] = tool_page()
    for path, h in pages.items():
        d = OUT / path.strip("/"); d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(h)
    global PREFIX
    from urllib.parse import urlparse
    PREFIX = urlparse(base_url()).path.rstrip("/") + "/"   # 404 can be served at any depth
    # Smarter 404 (2026-10-27 run #34, from Ahrefs AEO course: AI assistants send visitors to made-up or stale URLs).
    # Lists every real page; old /byebulky/... project-site paths jump to the same page at the root.
    nf_links = "".join(f'<li><a href="{U(p)}">{e(META.get(p, (p, ""))[0].replace(" | ByeBulky", ""))}</a></li>' for p in pages)
    nf_js = ("<script>(function(){var p=location.pathname;if(p.indexOf('/byebulky/')===0){"
             "location.replace(p.slice(9)+location.search+location.hash);}})();</script>")
    (OUT / "404.html").write_text(page("Page not found | ByeBulky", "Page not found.", "/404.html",
        f'<h1>Page not found</h1><p>That page doesn\'t exist (the link may be old or mistyped). Try one of these:</p><ul>{nf_links}</ul>{nf_js}'))
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
