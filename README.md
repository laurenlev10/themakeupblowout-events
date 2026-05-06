# themakeupblowout-events

Public landing pages for Makeup Blowout Sale events.

- **Live site:** https://events.themakeupblowout.com
- **Auto-generated** from `EVENT_DATA.md` by the `landing-page-builder` agent
- **Updated weekly** on Sundays by the `site-updater` agent

## Structure

```
docs/
├── index.html              ← Events list (homepage of the subdomain)
├── upcoming-events.json    ← Data file driving the homepage
├── CNAME                   ← events.themakeupblowout.com
└── {event-slug}/           ← Per-event landing pages (auto-generated)
    └── index.html
```

## Domains

- `themakeupblowout.com` → Shopify (untouched)
- `events.themakeupblowout.com` → this repo (GitHub Pages)
- `themakeupblowoutsale-group.com` → ClickFunnels (legacy, in active use; will be retired gradually)

## Migration plan

Phase 1 (this repo created): Build out infrastructure on new domain.
Phase 2: Lauren switches new event ad campaigns to point here instead of ClickFunnels.
Phase 3: Old CF events finish their lifecycle. Cancel ClickFunnels.
