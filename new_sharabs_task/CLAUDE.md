# Trees & Shrubs KPI page

## Files
- Page: `C:\Users\saeed\Downloads\Aa_Canopy\Trees_Shrubs_KPI.html` (single-file HTML/CSS/JS, same pattern as the main dashboard)
- Data: fetched live from a **Dropbox-hosted** Excel file (not local anymore — see "Data source" below)
- Background photos: `new_sharabs_task/sharabs_pic.png` (Trees card), `new_sharabs_task/CARD_sharabs_2.png` (Shrubs card)
- Overlay image: `new_sharabs_task/image_overly.png`, layered between the background photo and the darkening gradient on both cards (`.kpi-photo::after`)
- Served the same way as the rest of the project: `python -m http.server 8080` from `Aa_Canopy`, page at `http://localhost:8080/Trees_Shrubs_KPI.html`

## Data source (switched to Dropbox 2026-08-06)
`SOURCE_URL` now points directly at `https://dl.dropboxusercontent.com/scl/fi/rcukna753b3snqh3zmroa/Trees-Shrubs-GC_Planted.xlsx?rlkey=...&st=...&dl=1` — same CORS-safe pattern as `Overview_Dashboard.html` ([[project-canopy-dashboard]] memory has the background on why `dl.dropboxusercontent.com` works and `www.dropbox.com` share links don't: the latter's first redirect hop lacks a CORS header). Confirmed working via an actual in-browser `fetch()` test, not just curl (curl succeeding is not proof — it doesn't enforce CORS).

This means the page no longer depends on a local Excel file in `new_sharabs_task/` — editing the sheet in Dropbox and refreshing the page is enough. If the Dropbox link ever needs to change (new file, new share link), regenerate the direct-content URL: take the `www.dropbox.com/scl/fi/...` share link, swap the domain for `dl.dropboxusercontent.com`, and change `dl=0` to `dl=1` at the end.

## What the page shows
Two cards side by side: "Trees Planted" and "Shrubs & Ground Cover Planted", each with:
- A title/subtitle, a glass "GR" value box with a year badge on top (year = the actual Date cell's year, see below).
- A timeline bar (0 → mid-year tick → max-year tick, with the old/current target shown past the end) — see "Timeline bar mechanics" below, this went through many iterations and the current behavior is deliberate, not accidental.
- A white-bg breakdown panel: Date (left) / Green Riyadh & Stakeholders (right, stacked), on a `#E2EFD9` panel below the "Breakdown of ... to be planted by {year}:" title line (which stays white).

No year-selector buttons anymore (removed) — the page always shows one snapshot, driven by whatever's in Excel.

## Timeline bar mechanics (as of 2026-08-06 — read before touching this)
This bar encodes **two intentionally independent movements** — don't accidentally re-couple them:
1. **The white date tick** (position `tlPosMid`, label above it): driven purely by the **Date cell's** fractional year (`year + month/12`, from `DATE_YEAR_FRAC`/`DATE_YEAR`), mapped between `YEAR_MIN` and `YEAR_MAX` via `dateFraction³ × TL_POS_MAX` (a cubic curve, not linear) — this guarantees it lands exactly on `TL_POS_MAX` once the date's year reaches `YEAR_MAX` (they visually merge into one tick; see `mergedWithMax` suppression logic), while keeping a comfortable gap from the max tick for typical earlier dates. It moves even if the Excel trees/shrubs numbers never change.
2. **The color fill** (`fillPct`): driven purely by how close `valueMid` (the Year-column mid-row's actual value) is to `target` (the max-row value), independent of the date. It grows in two stages — `[0, target]` maps to `[0%, TL_POS_MAX%]`, and only value *above* target maps into `[TL_POS_MAX%, 100%]` against the old-target ceiling — so the max tick is only crossed once the value actually exceeds target.

These two are deliberately **not tied together** — if data lags behind schedule, the color visibly falls behind the white date tick; if data comes in without a date update, the color still advances on its own. The value label ("1.38M" etc.) is attached to and moves WITH the white date tick (not the color) — this was explicitly requested after an earlier attempt tracked it to the fill position instead, which the user rejected as confusing.

Also note: `YEAR_MIN`/`YEAR_MID`/`YEAR_MAX` come from whatever three numeric years actually exist in the Excel Year column (sorted), NOT hardcoded 2018/2026/2030 — editing the middle Year cell changes which row's value feeds `byYear.mid` and the GR-badge year, but does **not** by itself move the white tick (that only moves via the separate Date cell, per point 1 above — these two are also intentionally decoupled from each other, discovered as a bug 2026-08-05 and fixed by having both the tick's label AND position read from the Date cell instead of mixing Date-cell-position with Year-column-label).

## Known gotcha — SheetJS date parsing bug (fixed 2026-08-03)
Do **not** re-enable `cellDates: true` in the `XLSX.read()` call. SheetJS's `cellDates` conversion builds its epoch anchor with `new Date(1899, 11, 30, ...)` (local time), and for some historical local-timezone rules this bakes a multi-hour offset directly into the resulting `Date` object — confirmed by testing: it turned the correct serial `46113` (April 1, 2026) into `2026-03-31T20:59:08Z`, which then displayed as "March 2026" no matter what timezone formatting was applied afterward (`timeZone: "UTC"` on `toLocaleDateString` does NOT fix this — the corruption happens before formatting).

The working fix: read the Date cell as a **raw number** (`cellDates` off) and convert it with pure UTC math via `excelSerialToUTCDate()` (`Date.UTC(1899, 11, 30) + serial * 86400000`). If the Date row ever shows a wrong month/day again, verify the raw stored serial first rather than assuming the Excel data is wrong.

## Verifying changes without asking the user for screenshots every time
A headless-Chromium screenshot loop was set up for this page (Puppeteer, since `chromium-cli` isn't available in this Windows environment): `npm install puppeteer` in the scratchpad dir, then a small script that `goto()`s `http://localhost:8080/Trees_Shrubs_KPI.html` and screenshots. This was used repeatedly through the 2026-08 session to self-verify CSS/JS changes instead of relying only on user-provided screenshots — much faster feedback loop. Re-set this up early in a future session on this file rather than guessing blind or waiting on the user each time.

## Editing workflow
Edit the single HTML file directly, save, hard-refresh (`Ctrl+F5`) the browser tab if testing manually — a normal refresh can serve a stale cached copy.
