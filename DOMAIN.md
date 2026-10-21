# Pointing byebulky.com at GitHub Pages (do this after buying the domain)

The site is live now at **https://yairsz.github.io/byebulky/** (Pages source: `gh-pages` branch, root, published by `./publish.sh`). No custom domain is set yet (`cname: null`). Setting one before DNS exists would redirect the github.io URL to a domain that doesn't resolve.

Reference: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site

## 0. (Recommended) Verify the domain on GitHub first
GitHub → your profile **Settings → Pages → Add a domain** → `byebulky.com`. GitHub shows a TXT record (`_github-pages-challenge-yairsz.byebulky.com`). Add it at the registrar, then click Verify. This protects against takeover.

## 1. DNS records at the registrar for byebulky.com
Delete any default parking A/CNAME records for `@` and `www` first. Do not add a wildcard (`*`) record.

| Type | Name / Host | Value |
|---|---|---|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| AAAA | @ | 2606:50c0:8000::153 |
| AAAA | @ | 2606:50c0:8001::153 |
| AAAA | @ | 2606:50c0:8002::153 |
| AAAA | @ | 2606:50c0:8003::153 |
| CNAME | www | yairsz.github.io |

(The `www` CNAME points to `yairsz.github.io` with no repo name. GitHub will auto-redirect www ↔ apex.)

Check propagation (can take up to 24h):

    dig byebulky.com +noall +answer -t A
    dig www.byebulky.com +nostats +nocomments +nocmd

## 2. Switch the site config (one commit, so the force-pushed gh-pages keeps the CNAME)
`publish.sh` force-pushes `gh-pages`, so a CNAME added only through the GitHub UI would be wiped on the next publish. The CNAME has to come from the build instead:

1. In `site.json`: rename `"cname_pending"` → `"cname"` (value `byebulky.com`), and set `"base_url": "https://byebulky.com"`.
2. `git commit -am "Use custom domain byebulky.com" && git push && ./publish.sh`
   (the build writes `site/CNAME` and switches canonical URLs and the sitemap to byebulky.com. Links are relative, so they work as-is.)

## 3. GitHub Pages settings
Repo **Settings → Pages → Custom domain** → `byebulky.com` → Save (or `gh api -X PUT repos/yairsz/byebulky/pages -f cname=byebulky.com`). Wait for the DNS check to pass, then tick **Enforce HTTPS**. The certificate can take up to 24h before that option is available.

## 4. Confirm
    curl -sI https://byebulky.com/ | head -1          # 200
    curl -sI https://yairsz.github.io/byebulky/ | grep -i location   # should redirect to byebulky.com
    curl -s https://byebulky.com/sitemap.xml | head -c 200

Then submit https://byebulky.com/sitemap.xml in Google Search Console. robots.txt only takes effect at a domain root, so it starts working once the custom domain is live.
