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
- **Non-Google engines (added 2026-10-23, required):** every new or changed page MUST go out through IndexNow (POST above; one call to api.indexnow.org is shared with Bing, Yandex, Seznam, Naver, Yep, Internet Archive and Amazonbot). Expect HTTP 200/202 and log it in published-log.md.
- **llms.txt:** `build.py` regenerates `/llms.txt` from each page's title + meta description, so a new page appears automatically. If you add a new kind of page (new path pattern), update `LLMS_SECTIONS` / `LLMS_SUMMARY` / `LLMS_NOTES` in build.py so llms.txt stays accurate, and check `site/llms.txt` after building. Never put anything in llms.txt that the site itself does not say.
- **robots.txt / Bing:** build.py writes robots.txt (explicit allow for search + AI-answer crawlers in `ALLOWED_BOTS`, plus the Sitemap line) and copies `BingSiteAuth.xml` to the site root; every page carries the msvalidate.01 meta. Don't remove these.
- Search Console already has the sitemap; for a new page optionally check it with the URL Inspection API (developer@ ADC, quota project plenary-totem-501619-e6).
- Videos: add an entry to data/videos.json keyed by page path to embed a lazy YouTube player + VideoObject JSON-LD.

- **Privacy policy (added 2026-10-23):** `/privacy/` is generated from `privacy.py` and linked in every footer. If you add a script, embed, form, affiliate program or hosting change, update `privacy.py` (and its EFFECTIVE date) in the same commit so the policy stays true. The build now fails on broken internal links.

## Freshness signals (added 2026-10-24)
- build.py emits WebPage (AboutPage on /about/) JSON-LD with `dateModified` on every page, plus an Organization with `sameAs` the YouTube channel. `MODIFIED` is computed from the data (latest last_verified/last_checked of what the page shows), never from today; sitemap `lastmod` and the visible "page updated" dates use the same value. Keep it that way: never bump dates without actually re-checking.
- If you edit /about/ text, bump `ABOUT_UPDATED`; if privacy text changes, bump `PRIVACY_UPDATED` with privacy.EFFECTIVE. /about/ has a computed "By the numbers" block, so it updates itself.

## Computed city-hub answers (added 2026-10-24)
- `city_faq(c)` in build.py adds two Quick answers + FAQPage entries to every city hub, counted from the listings: who collects from inside the home (`stairs_inside` starting "Yes" / "No." / "Not stated", the rest counted as partial details) and how many options of each type. Keep `stairs_inside` starting with exactly "Yes.", "No." or "Not stated" when it's a clear answer. Never hand-write these.

- Entity hubs (2026-10-25): build.py adds to every item guide a prose link to its city hub with computed listing/guide counts, plus "<Item> guides for other cities" (same `short` across cities); every city hub gets "Other Boston-area cities we cover" with computed counts. Keep guide `short` values consistent ("Mattress", "Couch", "Appliances") so the cross-city links match. Don't add cities outside the Boston area without renaming that heading.

- **City section headings (added 2026-10-25):** city hubs group listings under `type_heading()` H2s that name the service and the city with a computed count (e.g. "Paid junk removal and hauling for Boston residents (15)"). Edit `TYPE_HEADINGS` in build.py if a new listing type is added. No ranking words ("best", "top") because we do not rank options.

- **Video transcripts (added 2026-10-25):** when you embed a Short via `data/videos.json`, add a `"transcript"` list holding the exact `say` lines from its make_video spec (in order). ytembed.py renders it as a visible "Read the video transcript" block and adds it to the VideoObject, so AI fetchers that only read HTML get the video's facts. Never write a transcript that differs from what the video says.

## Multi-condition answers on city hubs (added 2026-10-25, run #16)
- `city_faq()` also writes one Quick answer per item (mattress, couch, refrigerator/large appliance) for long, specific queries: "Who will take a <item> out of my apartment or house (not just from the curb) in <City>?". It's computed from `items_accepted` + `stairs_inside` (generic "Furniture" counts for couches unless couches/sofas are in `items_not_accepted`; "Small appliances/furniture" don't count). Keep `items_accepted` and `stairs_inside` accurate on new listings, start `stairs_inside` with "Yes", "No." or "Not stated" so it's counted, and never hand-edit these answers.

- (2026-10-25, run #18) The home page has a "City mattress pickup compared" table + FAQPage built by `home_mattress_compare()` from each city's `city bulk pickup` listing whose id contains `mattress` (cost, service_area, stairs_inside, book_url, phone, source_urls, last_verified). When you add a city, give its City mattress program listing that type and id pattern so it joins the table automatically. Keep `cost` starting with a plain first sentence (the table and the FAQ use the first sentence).

- (2026-10-26, run #20) First Search Console query rows arrived (Oct 24+). When real queries show up for a guide, align its title/Quick-answer wording with them (e.g. "sofa" in the couch title, "Will the City pick up an old fridge, AC, or TV?", "donate a TV"), restating only facts already in `sections`. Re-pull queries with /workspace/affiliate-library/scripts/gdata.py.

## Intent-matched headings (added 2026-10-26, run #22)
- The listing section on item guides is headed by `options_heading()` ("Every option we list: N ways to get rid of <item> in <City>"), not a generic "Options". For a new item, add its phrase to `ITEM_PHRASE` in build.py (or set `options_h` on the guide). Section `h` values should name what the section answers (e.g. "Who gets it free, and who pays $60"), never "Introduction"/"Details"/"More info".

## At-a-glance table on item guides (added 2026-10-26, run #24)
- Every item guide shows `guide_glance()` right after the Quick answers: one row per listing (name linked to its card, type, cost, inside/stairs pickup, lead time). Cells are verbatim leading sentences of the listing fields via `_cell()` (never split inside a.m./p.m.; "…" when cut). Don't hand-write table text; fix the listing field instead.
