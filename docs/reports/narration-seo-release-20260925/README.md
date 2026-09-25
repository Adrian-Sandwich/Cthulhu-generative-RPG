# Narration and SEO deployed — 2026-09-25

Published application commit: `2dfe602d64ce667b2d3e2b12b9b6ab6cc3d3bd4a`.
The commit passed GitHub CI on Linux, Windows and PostgreSQL.

Live site: https://lighthouse-cthulhu.fly.dev/

Image: `registry.fly.io/lighthouse-cthulhu:release-2dfe602` (52 MB).
Digest: `sha256:935a714264100173b2f5d60bf0b6e85219c9acacbdca0a7a9780a77afaad99b3`.

Fly updated the existing machine, preserving JSON storage, its volume and session
signing key. The pre-deployment volume snapshot
`vs_OB7qLolQaMgcbmyRyLyDGN` was confirmed created with five-day retention.
Previous image for rollback: `registry.fly.io/lighthouse-cthulhu:release-20260925-candidate`.
Any image rollback must preserve current save data.

## Live verification

- [Gameplay checks](production-smoke.json): health, 40-turn clock, finite pickup,
  exact receipt replay, read-only inventory query, rejection of a forged item tag,
  real hosted narration, restored session and inventory on desktop/mobile.
  No new LLM fallback or browser JavaScript errors were observed.
- [SEO checks](seo-check.json): public title and description, canonical URL without
  query parameters, indexable landing page, valid VideoGame JSON-LD, accessible
  sharing image, robots.txt and a sitemap containing only the public homepage.
- Chromium rendered the landing page on [desktop](landing-desktop.png) and
  [mobile](landing-mobile.png), without horizontal overflow.
- The temporary gameplay test session was reset. All **20 original saves** remained
  byte-for-byte identical by SHA-256: [integrity result](save-integrity.json).
  Raw save hashes, cookies and player data are not included in this report.

The smoke helper completed its checks, wrote its report and reset its own session;
printing its final Unicode report hit a Windows console encoding error. The saved
report was then read and validated separately. This did not affect the application.

The GitHub About, play link and repository topics are also published. Search Console
ownership verification and sitemap submission have not been performed; the public
sitemap and crawl metadata are ready. Actual indexing and search ranking are not
established by these checks.
