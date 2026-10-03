# Tyler State Park Campsite Choices

## Status

Interactive page: [Tyler campsite choices](../campgrounds/tyler-sites.html). Tyler sites BP-306 and BP-308 are now confirmed for Dec 29-31, 2026; this document is retained as the page and asset reference.

## Trip Context

- Campground: Big Pines Campground, Tyler State Park
- Planned stay: Dec 29-31, 2026
- Goal: document the campsite comparison page and selected sites
- Reservation confirmed: Big Pines Sites BP-306 and BP-308, Dec 29-31, 2026; $160 paid, no balance due. See [Tyler reservation summary](../receipts/tyler.html).
- Map currently in the workspace: [Tyler State Park Map.pdf](../assets/maps/Tyler%20State%20Park%20Map.pdf)
- Site availability, map images with roadway detail, and campsite-level photos still need to be supplied or identified

## Intended Experience

Create a page that helps anyone with the link compare available sites and vote for the preferred pair of two campsites. The intended flow is:

1. Show concise campground context and any constraints that affect site choice.
2. Show the campground overview map with three selectable loop regions: Big Pines Loop, Lake View Loop, and Cedar Point Loop.
3. Selecting a loop replaces the overview with that loop's map; a return control takes the visitor back to the overview.
4. On a loop map only, let the visitor toggle a roadway overlay to highlight roads and show how sites are laid out.
5. Make each campsite selectable; selecting one opens its ground-level image and relevant details.
6. Provide a voting control near the bottom for the preferred pair of sites.

This is a discussion aid, not a reservation system. Availability and the final booking should be verified with Texas State Parks.

## Decisions So Far

- Audience: anyone with the link
- Ballot: vote for a preferred pair of two sites
- Pair rule: the two selected sites must be in the same loop
- Submission preference: Google Forms
- Form access: anyone with the form link; voters enter their own names
- Results: live tally shared with voters
- Comments: allow an optional explanation with each vote
- Map navigation: campground overview -> select Big Pines Loop, Lake View Loop, or Cedar Point Loop -> replace with loop map -> optional road overlay -> select a campsite -> ground-level image; return control goes back to overview
- Image assets: place them in [tyler-site-images](../assets/tyler); see its [README](../assets/tyler/README.md) for the naming convention

Because the form will be open to anyone with the link, self-entered names cannot reliably prevent duplicate votes. A live tally may also influence later voters. These are accepted tradeoffs for easier access and visible results.

## Candidate Information To Gather

For each campsite, if available:

- Site number and loop/section
- Current availability and when/how it was checked
- Site type, dimensions, hookups, and any length or vehicle restrictions
- Pad, slope, shade, privacy, nearby facilities, and road exposure
- Ground-level photos, with direction or viewpoint noted
- Location on the map and any relevant access-road details
- Notes about suitability for each camper or travel group

For the map assets:

- Original campground overview and maps for Big Pines Loop, Lake View Loop, and Cedar Point Loop, with resolution and source
- A separate roadway overlay for each loop map, aligned to that map; no roadway overlay is needed on the campground overview
- A way to identify loop boundaries and campsite click targets on each loop map

## Map Zoom And GPS Option

The first version can use the supplied overview and loop images, with SVG click regions and optional browser zoom/pan. This is the simplest route and does not require a Google Maps API key. A geographic satellite map is a separate option: it needs a satellite tile provider, and the existing maps/overlays must be georeferenced to align with GPS coordinates. A single starting GPS coordinate is not enough to accurately position an entire map image; at minimum, provide map bounds or several matching map points. Tile-provider access, API keys, quotas, attribution, and usage terms depend on the provider.

## Voting And GitHub Pages

GitHub Pages serves static files; by itself it cannot receive or store votes on an administrator's server. A vote saved only in the browser would not be sent to the page owner.

Possible ways to receive feedback:

- Link to a hosted form (for example, Google Forms or another form provider). This is usually the simplest static-site approach, but submissions and privacy depend on that provider.
- Post to a form service endpoint. The page can submit structured choices without hosting a backend, but it requires an account/configuration and may have limits or anti-spam settings.
- Link to a GitHub Issue or Discussion. This is only suitable if voters can use GitHub and the repository's visibility/access settings are acceptable.
- Use an email link. It is easy to set up but relies on the voter's mail app and does not provide a reliable structured submission.

The vote should be treated as a preference unless the group explicitly wants it to determine the final booking. The page should not imply that a vote reserves a site.

## Open Questions

### Group And Decision

- Are the two campsites for two separate campers/families, and should the page evaluate whether a pair is compatible (nearby, same loop, suitable access, etc.)?
- Is the vote advisory, or should the winning pair be the default booking choice?

### Site Comparison

- What exact campsite list and availability snapshot should be shown, and who will keep it current?
- Which factors matter most: proximity, privacy, shade, hookups, pad size, road noise, restroom access, or something else?
- Should unavailable sites remain visible as comparison references, or be hidden?
- Do you want side-by-side comparison for selected sites, or is a map-driven detail view enough?

### Images And Map

- Is the roadway overlay already available as a separate image, or should it be created from the map? It should align with the corresponding loop map.
- Should campsite click targets be drawn over the map based on site numbers, or will the maps already label/mark each site clearly enough?
- Should each campsite open one ground-level photo or a small gallery of photos?
- Is zoom/pan on the supplied map images sufficient, or is a geographically aligned satellite basemap important?

### Feedback Delivery

- Should voters be allowed to edit their response or submit again?

## Decisions To Confirm Before Building

- [ ] Confirm whether the same-loop rule is sufficient or if proximity/camper-fit constraints are also needed
- [ ] Choose the decision factors and candidate-site details
- [ ] Add the campground/loop maps, roadway overlays, and ground-level photos to the image folder
- [ ] Decide whether the Google Form allows response edits or repeat submissions
- [ ] Confirm final site availability directly before booking