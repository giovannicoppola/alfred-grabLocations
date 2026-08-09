# alfred-grabLocations 📍

An [Alfred](https://www.alfredapp.com/) workflow to fetch the locations of your
Apple Calendar events over the next *N* days and open them as a **Google Maps**
directions route.

## What it does

- Reads events from one or more named calendars ("crews") over the next `MYDAYS` days.
- Collects their locations and builds Google Maps directions URLs — all locations in
  batches of 10, plus one route per calendar.
- Optional ZIP-code filter to narrow the results.

## Setup

Configure in the workflow's **Configuration** panel:

| Variable | Meaning |
|----------|---------|
| `MYCALENDAR` | Comma-separated list of Apple Calendar names to scan |
| `MYDAYS` | How many days ahead to look (default `7`) |

The workflow uses AppleScript to read Calendar.app, so grant Alfred access to
**Calendars** when prompted.

## Usage

Trigger the keyword and optionally type a ZIP code to filter. `↩` opens the route in
Google Maps.

## Notes

Personal workflow. Not published to the Alfred gallery.

# Changelog
- 2026-07-21: version 0.4.1, handle Calendar events with no location, guard unset config, drop empty locations
