#!/usr/bin/env python3
"""ByeBulky static site builder (stdlib only).
Usage: python3 build.py            -> writes ./site/
Data:  data/cities/<slug>.json      -> /<slug>/
       data/guides/<slug>.json      -> /<city>/<guide-slug>/  (item guides that reuse city listings)
"""
import json, html, shutil, datetime, re, os
from ytembed import embed as yt_embed, video_ld
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
def page(title, desc, path, body, jsonld=None):
    url = base_url() + path
    META[path] = (title, desc)
    lds = [x for x in ((jsonld if isinstance(jsonld, list) else [jsonld]) + [video_ld(path)]) if x]
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
<footer><div class="wrap">© {year} {e(CFG['site_name'])}. Information is gathered from official sources and can change. Always confirm with the organization before you haul anything. <a href="{U('/about/')}">Affiliate disclosure &amp; how we verify</a>. <a href="{YT_CHANNEL}" rel="noopener" target="_blank">ByeBulky on YouTube</a>.</div></footer>
</body></html>"""

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
<dt>Sources</dt><dd>{srcs} · last verified {e(l['last_verified'])}</dd></dl></article>"""

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

def city_page(c):
    set_page(f"/{c['slug']}/")
    used_types = [t for t in TYPES if any(l["type"] == t for l in c["listings"])]
    opts = "".join(f'<option value="{e(t)}">{e(t.title())}</option>' for t in used_types)
    qa = "".join(f"<div><strong>{e(x['q'])}</strong>{e(x['a'])}</div>" for x in c.get("quick_answers", []))
    groups = ""
    for t in used_types:
        cards = "".join(listing_card(l) for l in c["listings"] if l["type"] == t)
        groups += f"<h2>{e(t.title())}</h2>{cards}"
    res = "".join(f'<li><a href="{e(r["url"])}" rel="nofollow noopener" target="_blank">{e(r["label"])}</a></li>' for r in c.get("resources", []))
    guides = [g for g in GUIDES if g["city"] == c["slug"]]
    glinks = ""
    if guides:
        glinks = "<h2>Item guides for " + e(c["name"]) + "</h2><ul>" + "".join(f'<li><a href="{U("/" + g["path"] + "/")}">{e(g["title"])}</a></li>' for g in guides) + "</ul>"
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › {e(c['name'])}, {e(c['state'])}</p>
<h1>How to get rid of a couch, mattress or furniture in {e(c['name'])}</h1>
<p class="lead">{e(c['intro'])}</p>
<p class="meta">{len(c['listings'])} options · every listing links to its source · last verified {e(c['last_verified'])}</p>
<div class="qa">{qa}</div>
{loadup_slot()}
{glinks}
<div class="filters"><select id="ft" aria-label="Filter by type"><option value="">All types</option>{opts}</select>
<input id="fq" type="search" placeholder="Filter: mattress, sofa, fridge…" aria-label="Filter by item"></div>
{groups}
<h2>Useful official tools</h2><ul>{res}</ul>
<p class="note">Spotted something out of date? Policies change often. Tell us and we'll re-check it against the source.</p>
{FILTER_JS}"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": c["title"],
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": l["name"]} for i, l in enumerate(c["listings"])]}
    lds = [ld, faq_ld(c.get("quick_answers")), crumbs_ld([("Home", "/"), (c["name"], f"/{c['slug']}/")])]
    return page(c["title"], c["meta_description"], f"/{c['slug']}/", body, lds)

def guide_page(g, city):
    set_page(f"/{g['path']}/")
    ids = g.get("listing_ids", [])
    ls = [l for l in city["listings"] if l["id"] in ids]
    missing = set(ids) - {l["id"] for l in ls}
    assert not missing, f"guide {g['path']} references unknown listings {missing}"
    secs = "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" for s in g.get("sections", []))
    body = f"""<p class="meta"><a href="{U('/')}">Home</a> › <a href="{U('/' + city['slug'] + '/')}">{e(city['name'])}</a> › {e(g['short'])}</p>
<h1>{e(g['h1'])}</h1><p class="lead">{e(g['intro'])}</p><p class="meta">Last verified {e(g['last_verified'])}</p>
{qa_block(g.get("quick_answers"))}{secs}{yt_embed('/' + g['path'] + '/', YT_CHANNEL, 'ByeBulky')}{loadup_slot()}<h2>Options</h2>{''.join(listing_card(l) for l in ls)}
<p><a href="{U('/' + city['slug'] + '/')}">See all {e(city['name'])} options →</a></p>"""
    for x in g.get("quick_answers", []):
        assert x.get("q") and x.get("a"), f"guide {g['path']} has an empty quick answer"
    lds = [faq_ld(g.get("quick_answers")),
           crumbs_ld([("Home", "/"), (city["name"], f"/{city['slug']}/"), (g["short"], f"/{g['path']}/")])]
    return page(g["title"], g["meta_description"], f"/{g['path']}/", body, lds)

def home(cities):
    set_page("/")
    cl = "".join(f'<a href="{U("/" + c["slug"] + "/")}">{e(c["name"])}, {e(c["state"])}<br><span class="meta">{len(c["listings"])} verified options</span></a>' for c in cities)
    body = f"""<h1>Get rid of a couch, mattress or old fridge without the runaround</h1>
<p class="lead">{e(CFG['tagline'])} For each city we list every real option: City bulk and mattress pickup, charities that pick up, drop-off spots, furniture banks, and paid haulers. You see what each one takes, its condition rules, whether it will come inside or up stairs, and its cost. A cost is only shown when the organization publishes it.</p>
<h2>Cities</h2><div class="cities">{cl}</div>
<h2>Why this exists</h2>
<p>Charities change what they accept, some stop picking up furniture altogether, and city rules differ from one place to the next. People end up calling three places and still having a couch on the curb. We collect the rules from official sources, link every listing to its source, and date when we last checked it.</p>
<p><a href="{U('/about/')}">How we verify listings &amp; how this site makes money →</a></p>"""
    return page(f"{CFG['site_name']}: How to get rid of furniture, mattresses & appliances in your city",
                "Verified, city-by-city options for getting rid of couches, mattresses, furniture and appliances: city pickup, donation pickup, drop-off, furniture banks and haulers.", "/", body)

def about():
    set_page("/about/")
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
<p>ByeBulky uses Google Analytics to collect aggregate traffic statistics, such as which pages are visited, so we can see what's useful. It doesn't collect your name or email, though Google may set cookies to tell visits apart.</p>
<h2>Corrections</h2>
<p>Rules change often. If a listing is wrong or out of date, let us know and we'll re-check it against the source and update the date.</p>"""
    return page("About ByeBulky: how we verify listings & affiliate disclosure",
                "How ByeBulky verifies every listing against official sources, and how the site makes money (affiliate disclosure).", "/about/", body)

def load_all():
    cities = [json.loads(p.read_text()) for p in sorted((ROOT / "data/cities").glob("*.json"))]
    guides = [json.loads(p.read_text()) for p in sorted((ROOT / "data/guides").glob("*.json"))]
    return cities, guides

LLMS_SUMMARY = (CFG["tagline"] + " A directory of real options for getting rid of couches, mattresses, furniture and "
                "appliances: City bulk and mattress pickup, charities that pick up, drop-off spots, furniture banks and paid haulers.")
LLMS_NOTES = ["Every listing comes from the organization's own website or an official government page, links to its sources, "
              "and shows the date it was last verified. When a source doesn't state something, the listing says "
              f'"{NS}". ByeBulky publishes no reviews or ratings.']
LLMS_SECTIONS = [("Cities", lambda p: p.count("/") == 2 and p not in ("/", "/about/")),
                 ("Item guides", lambda p: p.count("/") == 3),
                 ("Home and about", lambda p: p in ("/", "/about/"))]

# Search and AI-answer crawlers we explicitly welcome (one robots.txt group, RFC 9309).
# The catch-all group below allows everyone else too; this list just makes intent explicit.
ALLOWED_BOTS = ["Googlebot", "Bingbot", "Applebot", "DuckDuckBot", "DuckAssistBot", "OAI-SearchBot", "ChatGPT-User",
                "PerplexityBot", "Perplexity-User", "Claude-SearchBot", "Claude-User", "ClaudeBot", "YandexBot",
                "SeznamBot", "Yeti", "MojeekBot"]
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
def main():
    global GUIDES
    cities, GUIDES = load_all()
    for c in cities:
        ids = [l["id"] for l in c["listings"]]
        assert len(ids) == len(set(ids)), f"duplicate listing ids in {c['slug']}"
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    pages = {"/": home(cities), "/about/": about()}
    for c in cities: pages[f"/{c['slug']}/"] = city_page(c)
    bycity = {c["slug"]: c for c in cities}
    for g in GUIDES: pages[f"/{g['path']}/"] = guide_page(g, bycity[g["city"]])
    for path, h in pages.items():
        d = OUT / path.strip("/"); d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(h)
    global PREFIX
    from urllib.parse import urlparse
    PREFIX = urlparse(base_url()).path.rstrip("/") + "/"   # 404 can be served at any depth
    (OUT / "404.html").write_text(page("Page not found | ByeBulky", "Page not found.", "/404.html", f'<h1>Page not found</h1><p><a href="{U("/")}">Go to the home page</a></p>'))
    base = base_url()
    today = datetime.date.today().isoformat()
    def lastmod(path):
        for c in cities:
            if path == f"/{c['slug']}/": return c["last_verified"]
        for g in GUIDES:
            if path == f"/{g['path']}/": return g["last_verified"]
        return today
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
    print(f"Built {len(pages)} pages, {sum(len(c['listings']) for c in cities)} listings -> {OUT}")

if __name__ == "__main__":
    main()
