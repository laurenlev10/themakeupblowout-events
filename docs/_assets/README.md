# Assets folder

Static images / GIFs / videos used by landing pages, served by GitHub Pages
under `https://events.themakeupblowout.com/_assets/...`.

## Folder layout

```
_assets/
├── shared/                        ← used across all events
│   ├── glitter.gif                ← e.g. hero glitter animation
│   ├── logo.png
│   └── share-card.jpg             ← for social previews / og:image
└── events/
    └── {slug}/                    ← per-event (matches docs/events/{slug}/)
        ├── hero.gif               ← top banner of the landing page
        ├── product.gif            ← optional second image, mid-page
        └── thanks.gif             ← optional, on share.html
```

## How Lauren uploads new GIFs (no Git needed)

1. Open: https://github.com/laurenlev10/themakeupblowout-events/upload/main/docs/_assets/events/{slug}/
   — replace `{slug}` with the event's slug, e.g. `columbia-mo-2026`
2. Drag-and-drop the GIF file(s) into the page.
3. Optionally fill the commit message ("Add hero GIF for Columbia MO").
4. Click **Commit changes** → green button → done.

GitHub Pages auto-rebuilds within ~1 minute. The agent will then reference these
files when generating the landing page (filenames matching `hero.gif`, `product.gif`,
`thanks.gif` are auto-detected; otherwise specify the full URL in the JSON).

## Filename conventions (recommended, not enforced)

| Filename | Where it appears | Suggested size |
|---|---|---|
| `hero.gif` | Top banner of `index.html` | 600-1200 px wide, < 5 MB |
| `product.gif` | Mid-page accent on `index.html` | 400-800 px wide, < 3 MB |
| `thanks.gif` | Top of `share.html` | 400-800 px wide, < 3 MB |
| `share-card.jpg` (in shared/) | og:image for social previews | 1200 × 630 px, < 500 KB |

## File size guidelines

- GitHub Pages serves files up to ~100 MB but warns above 50 MB.
- For perceived performance, keep individual GIFs under 5 MB.
- If you have raw video, convert to optimized GIF first (https://ezgif.com).
