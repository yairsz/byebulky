# NIGHTLY.md: add one new page to ByeBulky each night

Goal: each night, publish **one** new page that is useful and 100% sourced. One accurate page beats three sloppy ones. If a page can't be verified well enough, skip it, note why in `published-log.md`, and take the next item in the queue.

## Ground rules (never break these)
1. **Never invent anything.** That covers facts, prices, hours, lead times, policies, reviews, and ratings. If the source doesn't say it, write `Not stated, check with them`.
2. Only use **official sources**: the organization's own site, a city or state government page, or an official city list. Third-party lists (Reddit, blogs, Yelp, other directories) can help you *find* candidates, but they are never the citation.
3. Every listing needs at least one `source_urls` entry and `last_verified` set to today's date (YYYY-MM-DD, America/New_York).
4. Facts taken from a city's list instead of the company's own page get a note: "as listed by the City" plus the note text.
5. **No affiliate links** unless Yair has approved an account and put the official embed into `site.json` → `loadup_widget_html`. Never sign up for programs or create accounts without Yair's explicit approval. Publishing new pages to the existing GitHub Pages site is approved. Changing hosting, domains, or repo settings is not.
6. Save raw snapshots of the pages you used in `research/<city>/` (curl → `research/h2t.py` → .txt) so the claims can be checked later.

## Procedure
1. **Pick the page:** take the top unchecked item in `content-queue.md`.
2. **Research** (target about 30–60 minutes of tool time):
   - New **city page**: start with the city's official bulk-trash, 311, and mattress pages. Then the local Habitat ReStore (https://www.habitat.org/local/restore), satruck.org (enter the city ZIP), local furniture banks (find via the city site or the Furniture Bank Network), ReSupply's city page if one exists (`resupply.com/<city>/`), and any hauler list the city publishes.
   - New **item guide** (e.g. "mattress in Boston"): reuse listings already in `data/cities/<city>.json`. Only add new listings if you verify them first.
   - Fetch with `curl -sL -A "Mozilla/5.0 ..." URL -o research/<city>/<name>.html` and convert with `python3 research/h2t.py file.html > file.txt`. If curl is blocked, use WebFetch, then the browser.
3. **Write the data:**
   - City: create `data/cities/<slug>.json` using the same shape as `data/cities/boston.json` (fields: id, name, type, items_accepted, items_not_accepted, condition_rules, stairs_inside, lead_time, cost, service_area, address, book_url, phone, email, source_urls, last_verified, notes). `type` must be one of: `city bulk pickup`, `charity pickup`, `drop-off`, `furniture bank`, `paid hauler`, `retailer haul-away`.
   - Guide: create `data/guides/<city>-<item>.json` using the same shape as `data/guides/boston-mattress.json` (path, city, short, title, meta_description, h1, intro, quick_answers[], sections[], listing_ids[], last_verified). Every sentence in `sections` must be backed by a cited listing or the city source. `quick_answers` (added 2026-10-23) = 3–5 `{q, a}` pairs phrased the way people search ("Does the City of Boston pick up mattresses?"); each answer only restates facts already in `sections`. They render as a Q&A block under the intro plus FAQPage JSON-LD (for AI answer engines).
   - Title ≤ 65 characters where possible; meta description ≤ 160 characters.
4. **Build:** `python3 build.py`. Links are relative and canonical/sitemap URLs come from `site.json` `base_url`. The builder fails on missing required fields, unknown types, listings with no source, duplicate ids, or guides that point to unknown listings. Fix any errors and rebuild. It regenerates `site/sitemap.xml` (with lastmod from `last_verified`) and `robots.txt` automatically.
5. **Check:** `cd site && python3 -m http.server 8765`, open the new page (or `curl -s -o /dev/null -w "%{http_code}"`), and take a headless screenshot at 390px and 1280px widths:
   `google-chrome --headless=new --no-sandbox --window-size=390,2400 --screenshot=/tmp/p.png http://localhost:8765/<path>/`
   Spot-check 3 listings against the saved source snapshots.
6. **Log:** append a row to `published-log.md` with the date, path, listing count, sources checked, and any gaps.
7. **Update the queue:** tick the item in `content-queue.md` and add new ideas you found (keep about 30 items queued).
8. **Re-verify one old page** if time allows: re-fetch its sources, update changed facts, and bump `last_verified`.
9. **Commit & publish** (approved by Yair: GitHub Pages under `yairsz/byebulky`):
   ```
   cd /workspace/bulky-directory
   git pull --rebase                      # in case anything changed remotely
   git add data/ content-queue.md published-log.md NIGHTLY.md build.py static/ site.json
   git commit -m "Add <page path> (<n> listings, verified <YYYY-MM-DD>)"
   git push
   ./publish.sh                           # builds and force-pushes site/ to the gh-pages branch
   ```
   Do not commit `site/` or `research/<city>/` raw snapshots to main (both are gitignored).
10. **Confirm the deploy succeeded** (takes about 1–2 minutes):
   ```
   gh run list -R yairsz/byebulky --workflow pages-build-deployment --limit 1   # expect: completed success
   gh api repos/yairsz/byebulky/pages --jq .status                              # expect: built
   curl -s -o /dev/null -w "%{http_code}\n" "https://yairsz.github.io/byebulky/<new path>/?v=$(date +%s)"   # expect 200
   curl -s https://yairsz.github.io/byebulky/sitemap.xml | grep -c "<new path>"                             # expect 1
   ```
   (After the custom domain is live, use https://byebulky.com/ instead; see DOMAIN.md.) If the run failed, open it with `gh run view <id> --log-failed`, fix it, and re-run `./publish.sh`. Record the result (success, or the failure and fix) in `published-log.md`.

## Re-verification cadence
- City pages: re-check every 90 days, or right away if someone reports a change.
- Anything with a price: re-check every 60 days.

## After publishing (added 2026-10-23)
- Submit new/changed URLs to IndexNow: POST https://api.indexnow.org/indexnow with {"host","key": site.json indexnow_key, "keyLocation": "https://<host>/<key>.txt", "urlList": [...]} (expect 200/202).
- Search Console already has the sitemap; for a new page optionally check it with the URL Inspection API (developer@ ADC, quota project plenary-totem-501619-e6).
- Videos: add an entry to data/videos.json keyed by page path to embed a lazy YouTube player + VideoObject JSON-LD.
