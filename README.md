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

- Reads events from one or more named calendars ("crews") from today through
  `MYDAYS` days ahead.
- Collects their locations in chronological order, skipping duplicates and events
  without a location, and builds Google Maps directions URLs: all locations in
  batches of 10 stops, plus one route per calendar.
- Optional US ZIP-code filter to narrow the results.

## Setup

Configure in the workflow's **Configure Workflow…** panel:

| Variable | Meaning |
|----------|---------|
| `MYCALENDAR` | Comma-separated list of Apple Calendar names to scan |
| `MYDAYS` | How many days ahead to look (default `7`) |

The workflow reads Calendar.app with AppleScript. On first run macOS asks whether
Alfred may **control Calendar**: click **OK**. If you declined, re-enable it in
**System Settings › Privacy & Security › Automation › Alfred › Calendar**.

## Usage

- `grablocation`: routes for all upcoming locations, plus one per calendar.
- `grablocation 02139`: only locations containing that ZIP code.
- `↩` opens the route in Google Maps.

## Limitations

- **Repeating events** only appear on the date of their first occurrence:
  Calendar's AppleScript interface doesn't expand recurrences.
- Calendar scripting is slow on large calendars (a few seconds per few hundred
  events). Very large or subscribed calendars may time out; the workflow then
  shows the error instead of results.
- The ZIP filter only recognizes 5-digit US ZIP codes (optionally ZIP+4).

## Changelog

- 2026-10-09: version 0.5.0 — prepared for public release
  - Fix: addresses containing `#`, `/`, `?` or `&` broke the Maps URL
  - Fix: an empty extra batch appeared when the number of locations was a multiple of 10
  - Fix: a missing calendar, invalid config or denied Calendar access now shows a
    message in Alfred instead of failing silently
  - Stops are listed in chronological order; only events in the date range are
    fetched (much faster on large calendars)
  - Items with nothing to open can no longer be actioned
- 2026-07-21: version 0.4.1 — handle Calendar events with no location, guard unset config, drop empty locations
