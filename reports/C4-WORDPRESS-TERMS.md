# WordPress vulnerability sources: terms check (2026-10-24)

**1. Wordfence Intelligence (Defiant). Use this one.**
- Licence: a custom, permissive per-record grant: "perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute". Source: the `copyrights.defiant.license` field in the v3 feed docs. The T&C §2(a) grant has the same wording.
- Commercial use: YES. "This feed is publicly available for free for personal and commercial use". The T&C say "WORDFENCE INTELLIGENCE IS OFFERED AT NO FEE."
- Attribution: required in any copy. Each copy must "include a hyperlink to this vulnerability record, and reproduce Defiant's copyright designation and this license". MITRE-sourced records must also carry MITRE's notice.
- Bulk access: built in. `GET /api/intelligence/v3/vulnerabilities/production` returns "the complete feed" as one JSON. Fields: slug, affected_versions, patched_versions, cwe, references. Limits: none published, only a 429 response when you poll too often. Paid editions: UNCONFIRMED (none found).
- Account/key: YES. A free wordfence.com account and a Bearer API key are needed.
- Blockers: none found. Caveat: the live T&C page sits behind a WAF; the last readable copy is the Jan 2025 Wayback capture, so later edits are UNCONFIRMED.
- URLs: https://www.wordfence.com/help/wordfence-intelligence/v3-accessing-and-consuming-the-vulnerability-data-feed/ (Wayback 2026-10-15) and https://www.wordfence.com/wordfence-intelligence-terms-and-conditions/

**2. WPScan (Automattic). This one blocks us.**
- Licence: proprietary. "All of our database data is copyrighted and owned by WPScan SAS"; "custom license that requires a fee to be paid if used commercially."
- Commercial use: NO on the free plan. The free plan is for "non‑commercial purposes", "Capped at 25 API calls per day". Commercial use needs a paid Enterprise quote.
- Blockers, free terms: "Permanent storage of our vulnerability data is not permitted", "API vulnerability data caching is not permitted", "No scrapping".
- Blockers, Enterprise TOS (updated 2024-06-27): "prohibited from storing or downloading (in any fashion or for any length of time) any data … other than for the purpose of using the Services". Enterprise customers get DB dumps (`enterprise-data.wpscan.com/*.json.gz`), but storage and reuse are still restricted.
- Account/token: YES.
- URLs: https://wpscan.com/api/ , https://wpscan.com/pricing/ , https://wpscan.com/terms/

**3. Patchstack. This one also blocks us.**
- Licence: proprietary. §3.1 grants a "non-sublicensable, non-transferable … licence, exclusively in support of Customer Operations".
- Commercial use for our purpose: NO.
  - §3.2 bans derivative works and use "for the benefit of any third party".
  - §3.5 covers "vulnerability and mitigation data": "Customer shall not disclose Service Deliverables to any third party".
  - §7.3 says copies must be destroyed on termination.
- Access: the Standard tier (5,000 requests/24 h) "is no longer offered to new customers". The Extended tier has custom pricing, is activated on request, and has a batch endpoint of 50 products per request.
- Key: YES (`PSKey`).
- Whether the terms also cover anonymous browsing of patchstack.com/database: UNCONFIRMED.
- URLs: https://patchstack.com/terms-and-conditions/ , https://docs.patchstack.com/api-solutions/threat-intelligence-api/overview/ , https://docs.patchstack.com/api-solutions/threat-intelligence-api/standard/

**4. WordPress.org plugin directory and SVN**
- Code licence: GPL. Guideline 1: "All code, data, and images — anything stored in the plugin directory … must comply with the GPL or a GPL-Compatible license." That page was last updated 2026-03-11. Commercial use is allowed under the GPL, but anything we redistribute must keep its GPL notices and offer source.
- Bulk access policy: no official policy found (UNCONFIRMED). `plugins.svn.wordpress.org/robots.txt` sets `Crawl-delay: 3`. Versioned zips (`downloads.wordpress.org/plugin/<slug>.<ver>.zip`) need no account. Practical rule: throttle requests and fetch only the versions we need.
- Guideline 17 (trademarks) is worth noting for plugin names.
- URL: https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/

**5. GitLab Advisory Database**
- advisories-community: MIT licence ("MIT-licensed, time-delayed clone … older than 30 days"). Commercial use: YES. Attribution: keep the MIT notice. Access: `git clone`, no key needed.
- gemnasium-db: custom "GitLab Advisory Database Terms" (2022-05-02), with blocking clauses:
  - §4(f): "you expressly agree not to download, copy, or otherwise store … any of the Content".
  - §5(f): no crawlers or bots.
  - Do not use it.
- Coverage: the packagist tree covers Composer packages only. There is no `wpackagist-plugin` path, so it is not a WordPress source.
- URLs: https://gitlab.com/gitlab-org/advisories-community , https://gitlab.com/gitlab-org/security-products/gemnasium-db/-/blob/master/LICENSE.md

**6. CVE List and NVD**
- cvelistV5: CVE Terms of Use. Commercial use: YES ("perpetual … irrevocable copyright license … distribute"). Attribution: "reproduce MITRE's copyright designation and this license". Access: daily zip releases, no key. URLs: https://github.com/CVEProject/cvelistV5 and https://www.cve.org/Legal/TermsOfUse (text checked in the cve-website source).
- NVD: a public service of the US government. Required notice: "This product uses the NVD API but is not endorsed or certified by the NVD." Rate limits: 5 requests per 30 s without a key, 50 with a free key. Keys must not be shared. Data is US-government work; a public-domain statement was not seen on the page, so that point is UNCONFIRMED. URL: https://nvd.nist.gov/developers/terms-of-use (Wayback 2026-08).

## Recommendation
- **Pull the data:** use Wordfence Intelligence as the only WordPress vulnerability source. It is commercial-friendly, it is one bulk JSON download, and it includes the slug, affected and patched versions and the CWE.
  - Someone has to create a free wordfence.com account to get the key. I did not create one.
  - Keep each record's hyperlink, Defiant notice and licence text (and MITRE's where it applies) in our private store. Carry them into any task that copies record text.
- **Cross-check:** use cvelistV5 or NVD for CVE IDs.
- **Get the code:** take plugin source from downloads.wordpress.org or SVN at a throttled rate (Crawl-delay 3). Ship the tasks under the GPL with the licence notices kept.
- **Avoid WPScan and Patchstack:** their terms forbid storage and third-party or derivative use.
