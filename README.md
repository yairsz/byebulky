# ByeBulky v1 (static directory)

Verified, city-by-city ways to get rid of couches, mattresses, furniture, and appliances.

## Layout
- `build.py`: stdlib-only static generator → `site/`
- `site.json`: site name, base_url (used for canonical links and the sitemap), and the LoadUp widget slot (empty)
- `data/cities/<slug>.json`: city metadata + listings (structured fields)
- `data/guides/<city>-<item>.json`: item guides that reuse city listings
- `static/style.css`: mobile-first CSS
- `scripts/make_boston.py`: the script that wrote boston.json (documents the source for each fact)
- `research/`: raw HTML/text snapshots of the source pages used for verification, plus `h2t.py`
- `NIGHTLY.md`, `content-queue.md`, `published-log.md`: nightly publishing workflow
- `site/`: build output (deploy this folder)

## Build & preview
    python3 build.py
    cd site && python3 -m http.server 8765   # http://localhost:8765/

## LoadUp placeholder
`build.py` → `loadup_slot()` renders `<!-- LOADUP_WIDGET_PLACEHOLDER -->` on city and guide pages until `site.json.loadup_widget_html` holds an approved official embed. When filled, it renders with an affiliate label. Also update the disclosure text in `about()` at that point.

## Hosting (not deployed; needs Yair's approval)
- GitHub Pages: free for public repos (`gh` is logged in as `yairsz`, with `repo` scope). Push `site/` (or build with Actions) and point a custom domain at it.
- Cloudflare Pages: free tier allows 500 builds/month. Direct upload of `site/` is possible with `wrangler` (not installed). Needs a Cloudflare account.
- Netlify free: 300 credits/month, and each production deploy costs 15 credits, so nightly deploys (~450 credits/month) would exceed it. Not recommended.
