# Search and sharing

Published to the hosted game on 2026-09-25. See the
[live deployment verification](reports/narration-seo-release-20260925/README.md).

The repository About leads with playing the game, links to the hosted adventure,
and uses relevant GitHub topics for solo RPGs, interactive fiction, cosmic horror,
and AI Dungeon Masters. The README provides a direct play link, an actual screenshot,
player instructions, and local setup.

The public page includes a descriptive title and summary, visible heading and
game description, canonical URL, Open Graph and Twitter sharing metadata,
and `VideoGame` JSON-LD describing the visible game. The sharing image is an
existing gameplay screenshot, not a mockup. Structured data makes no claims about
ratings or guaranteed search enhancements.

Set `PUBLIC_SITE_URL` to the trusted public HTTPS origin, without a trailing slash.
The Fly configuration sets it to `https://lighthouse-cthulhu.fly.dev`.
The canonical, sharing URLs and single-page sitemap use that configuration,
never incoming Host headers, query strings, session IDs or player data.
Unset installations request no indexing so local or staging copies do not compete
with the public site. Fork operators should configure their own public origin.

`/robots.txt` points to `/sitemap.xml` and discourages crawling API, admin and
generated-image paths. This is a crawler preference, not access control.
The sitemap contains only the public landing page. Static CSS, scripts and the
sharing image remain crawlable.

After deploying, verify the public metadata, then use Google Search Console URL
inspection and submit `/sitemap.xml` from the verified property. Property ownership
and actual indexing have not been established by this code change. Compare search
impressions, clicks and player starts over time; avoid treating keyword additions
as guaranteed ranking improvements.

References: [Google's SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
and [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).
