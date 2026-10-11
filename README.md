# alfred-grabLocations 📍

An [Alfred](https://www.alfredapp.com/) workflow to fetch the locations of your
Apple Calendar events over the next *N* days and open them as a **Google Maps**
directions route.

Created in response to [this Alfred Forum request](https://www.alfredforum.com/topic/20087-search-for-multiple-address-in-googlemaps-to-make-a-route/).

## Download

Get the latest `grabLocations_*.alfredworkflow` from [`releases/`](releases/) and
double-click it to install.

## Requirements

- [Alfred 5](https://www.alfredapp.com/) with the [Powerpack](https://www.alfredapp.com/powerpack/)
- Python 3. On a fresh Mac, `python3` is only a stub until the Command Line
  Tools are installed: run `xcode-select --install`, or install Python with
  [Homebrew](https://brew.sh/).

## What it does

- Reads events from one or more named calendars from today through
  `MYDAYS` days ahead, including every occurrence of repeating events. Calendars
  with the same name in different accounts are all included.
- Collects their locations in chronological order, skipping duplicates and events
  without a location, and builds Google Maps directions routes: one per
  calendar, plus a combined "All calendars" route when you list more than one.
  Routes are split into batches of 10 stops, the most Google Maps accepts.
- Optional US ZIP-code filter to narrow the results.

## Setup

Configure in the workflow's **Configure Workflow…** panel:

| Variable | Meaning |
|----------|---------|
| `MYCALENDAR` | Comma-separated list of Apple Calendar names to scan |
| `MYDAYS` | How many days ahead to look (default `7`) |

The workflow reads your calendars through macOS EventKit, so Alfred needs **Full
Access** to Calendars: **System Settings › Privacy & Security › Calendars › Alfred ›
Full Access**. If access is missing, the workflow says so; press `↩` on that
message to jump to the right settings pane.

## Usage

- `grablocation`: routes for all upcoming locations.
- `grablocation 02139`: only locations containing that ZIP code.
- `↩` opens the route in Google Maps.

## Limitations

- The ZIP filter only recognizes 5-digit US ZIP codes (optionally ZIP+4).

## Changelog

- 2026-10-11: version 0.5.0 — prepared for public release
  - Fix: addresses containing `#`, `/`, `?` or `&` broke the Maps URL
  - Fix: an empty extra batch appeared when the number of locations was a multiple of 10
  - Fix: a missing calendar, invalid config or missing Calendar access now shows a
    message in Alfred instead of failing silently
  - Read events through EventKit instead of scripting Calendar.app: instant on
    large calendars (which previously hung), includes repeating events, and
    covers same-named calendars across accounts. Requires Full Access to
    Calendars for Alfred
  - Stops are listed in chronological order; per-calendar routes are also split
    into batches of 10 stops
  - "All crews" renamed to "All calendars", and only shown with more than one calendar
  - Items with nothing to open can no longer be actioned
- 2026-07-21: version 0.4.1 — handle Calendar events with no location, guard unset config, drop empty locations
