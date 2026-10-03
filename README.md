# The Winter Loop

A static trip-planning website for the December 2026 Texas camping loop.

## Pages and Files

- [index.html](index.html) opens the [trip overview](master-plan-2026.html).
- [weather-forecast.html](weather-forecast.html) contains historical temperature curves and the live forecast.
- `driving/` contains the operational guides for Days 1-5, including both Day 3 options.
- `campgrounds/` contains campground details and the [interactive Tyler site map](campgrounds/tyler-sites.html).
- `activities/` contains the [MERUS trail guide](activities/merus-trails.html).
- `receipts/` contains local reservation and payment summaries.
- `assets/` contains shared navigation/theme code, park maps, receipt PDFs, and MERUS/Tyler imagery.
- `docs/` contains planning inputs, route notes, and research prompts.

The old root-level campground, driving, trail, and receipt HTML files are compatibility redirects. Edit their corresponding grouped pages instead. Redirects retain query parameters and fragment anchors.

## Navigation and Themes

Every content page loads [assets/site.js](assets/site.js) and [assets/site.css](assets/site.css). Navigation sits inside the page header and offers the overview, weather, trails, Tyler sites, full-loop map, and driving/campground/receipt menus.

Green Sage preserves the original page styling and still uses the saved `original` theme key. Dark uses low-light surfaces, Compact reduces type size and spacing, and Clean uses white surfaces with restrained accents. Green, Blue, and Red add color variations. The chosen theme is remembered in browser local storage and shared across pages and open tabs. Header navigation links to pages, not overview section jumps.

The overview's reservation table links to campground information, including [Dauphin Island](campgrounds/dauphin-island.html). Receipt links remain in the Trip Costs notes column. Fuel defaults to 11 MPG per vehicle; mapped-road subtotals exclude local mileage that has not yet been measured, and Day 3 Option B includes its additional road travel when selected.

Theme-selection controls are intentionally not displayed. The existing theme definitions remain in place, and each browser continues to use its last saved appearance.

Grouped HTML pages use `<base href="../">`; their local URLs are relative to the site root, not the containing directory. Links to a grouped page's own anchors must include its full site-relative filename. Shared navigation derives the site root from its script URL, so it also works under a GitHub Pages repository prefix.

## Preview and Weather Updates

From this directory, run:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/`. No build or package installation is required.

The existing weather updater, [update_weather_curves.py](update_weather_curves.py), [weather-temperature-curves.md](weather-temperature-curves.md), and forecast page intentionally remain at the root. This preserves the updater's default input/output paths.

```powershell
python update_weather_curves.py
```

Reservation-provider and map links remain external; protected original receipts may require sign-in. Local receipt summaries are not official receipts. Missing Tyler campsite photos remain placeholders rather than unrelated images.