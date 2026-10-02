# Tyler State Park Image Naming

Put campsite-choice page image assets in this folder. Use lowercase names, hyphens instead of spaces, and the campsite/loop labels shown on the park map. Keep original-resolution files when practical.

## File Names

| Image | Pattern | Example |
|---|---|---|
| Campground overview map | `campground-map.<ext>` | `campground-map.jpg` |
| Loop map | `<loop-id>-map.<ext>` | `big-pines-loop-map.jpg` |
| Roadway overlay for a loop map | `<loop-id>-roads-overlay.png` | `big-pines-loop-roads-overlay.png` |
| Campsite hotspots for a loop map | `<loop-id>-hotspots.svg` | `big-pines-loop-hotspots.svg` |
| Ground-level campsite photo | `site-<site-id>-ground-<number>.<ext>` | `site-12-ground-01.jpg` |

Use `.jpg`, `.jpeg`, `.png`, or `.webp` as appropriate. Keep the site's map label in `<site-id>`; for example, a site labeled `12A` becomes `site-12a-ground-01.jpg`.

Use these exact loop IDs in filenames:

- `big-pines-loop`
- `lake-view-loop`
- `cedar-point-loop`

For example, the Big Pines Loop map and its overlay are `big-pines-loop-map.jpg` and `big-pines-loop-roads-overlay.png`. Do not create a roadway overlay for `campground-map`; overlays are only used on loop maps.

Each loop hotspot SVG should contain one closed shape per campsite, on a transparent canvas aligned to that loop's map. Name each campsite shape `site-<site-id>` (for example, `site-12`). Existing Big Pines shapes use IDs such as `bp-307`, Lake View shapes use IDs such as `lv-206`, and Cedar Point shapes use IDs such as `cp-108`. These prefixes are supported and displayed as uppercase park labels (for example, `BP-307`, `LV-206`, and `CP-108`). The page uses the shape IDs to open the campsite detail panel and build the preferred pair. Big Pines `bp-326` remains in the source SVG but is excluded from the interactive map while that site is unavailable; remove it from the page's `unavailableSites` list when it becomes a candidate again.

## Overlay Requirements

- Save roadway overlays as transparent PNG files.
- Match each overlay's pixel width and height to its corresponding loop map. A one-pixel export-rounding difference is scaled by the page.
- Keep roads transparent everywhere except the highlighted road strokes; do not crop or resize the overlay independently.
- Use the same loop ID in the map and overlay names so they can be paired reliably.

## Ground-Level Photos

- Number photos in a consistent viewing order: `01`, `02`, and so on.
- Keep all photos for one campsite together by using the same site ID.
- Preserve any loop/site prefix from the hotspot ID in the photo filename. For example, the Big Pines `bp-307` marker uses `site-bp-307-ground-01.jpg`.
- If there are several photos, optional viewpoint suffixes may clarify them, for example `site-12-ground-02-road.jpg`.
- Do not put spaces or punctuation other than hyphens in filenames.

## Before Adding Files

- Confirm each photo's campsite number; do not infer a site from the image alone.
- If a map uses a different loop label, use that label consistently in the map, overlay, and any site IDs that need it.
- If campsite numbers repeat between loops, prefix those photo filenames with the loop ID, for example `big-pines-loop-site-12-ground-01.jpg`.
- Preserve Big Pines `bp-###`, Lake View `lv-###`, and Cedar Point `cp-###` hotspot IDs in photo names, for example `site-bp-307-ground-01.jpg`, `site-lv-206-ground-01.jpg`, and `site-cp-108-ground-01.jpg`.
- Keep availability and campsite facts in the page's data/notes rather than encoding them in image filenames.