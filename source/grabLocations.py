#!/usr/bin/python3 
# 
# Overcast ☁️   🌡️+40°F (feels +32°F, 79%) 🌬️↓2mph 🌖&m Sat Mar 11 12:45:33 2023
#W10Q1 – 70 ➡️ 294 – 304 ❇️ 60


"""
GRAB APPLE CALENDAR EVENT LOCATIONS AND OPEN THEM IN GOOGLE MAPS

"""

import os
import re
import sys
import json
import subprocess
from datetime import datetime, timedelta
from urllib.parse import quote_plus


MAX_STOPS = 10  # Google Maps directions take at most 10 stops

MYCAL = os.getenv('MYCALENDAR', '')
MYDAYS = os.getenv('MYDAYS') or '7'  # `or` (not getenv default) so a blank config field doesn't break int(MYDAYS)
MYCALlist = [x.strip() for x in MYCAL.split(",") if x.strip()]

# ASCII unit/record separators: never found in event locations or calendar names
FIELD_SEP = '\x1f'
RECORD_SEP = '\x1e'


def log(s, *args):
    if args:
        s = s % args
    print(s, file=sys.stderr)


def contains_zipcode(address):
    pattern = r"\b\d{5}(?:-\d{4})?\b"
    match = re.search(pattern, address)
    return bool(match)


def getDate(deltaDays):
    # Calculate the date N days from today
    future_date = datetime.now() + timedelta(days=deltaDays)

    # Format the date as 'Wednesday, May 10, 2023'
    formatted_date = future_date.strftime('%A, %B %d, %Y')
    return formatted_date


def makeFinalString(currSubset):
    # Each stop is one path segment: collapse whitespace (locations often span
    # several lines), drop '/' so it can't split a stop, then URL-encode so
    # characters like '#', '?' and '&' don't truncate the URL
    stops = [quote_plus(' '.join(loc.replace('/', ' ').split())) for loc in currSubset]
    return "https://www.google.com/maps/dir/" + "/".join(stops)


def makeItem(title, subtitle="", arg="", valid=True, icon=""):
    return {
        "title": title,
        "subtitle": subtitle,
        "valid": valid,
        "icon": {"path": icon} if icon else {},
        "arg": arg,
    }


def output(items):
    print(json.dumps({"items": items}))


def unique(locations):
    # De-duplicate, keeping the first (chronological) occurrence
    return list(dict.fromkeys(loc for loc in locations if loc))


scpt = '''
on run {myCalendars, myDays}
    set todayDate to (current date) - (time of (current date))
    set endDate to todayDate + ((myDays as integer) + 1) * days -- through the end of day myDays
    set fieldSep to character id 31
    set recordSep to character id 30
    set AppleScript's text item delimiters to ","
    set calendarList to every text item of myCalendars
    set AppleScript's text item delimiters to {""} -- Reset delimiters
    set resultText to ""

    tell application "Calendar"
        repeat with calName in calendarList
            set calName to calName as text
            if not (exists calendar calName) then error "Calendar not found: " & calName number 1001
            set theCalendar to calendar calName
            set theEvents to (every event of theCalendar whose start date is greater than or equal to todayDate and start date is less than endDate)
            repeat with theEvent in theEvents
                set theLoc to location of theEvent
                if theLoc is missing value then set theLoc to ""
                set startOffset to (start date of theEvent) - todayDate
                set resultText to resultText & startOffset & fieldSep & theLoc & fieldSep & (name of theCalendar) & recordSep
            end repeat
        end repeat
    end tell

    return resultText
end run
'''


def calendarError(stderr):
    log(stderr)
    if "-1743" in stderr:
        return makeItem("Alfred is not allowed to control Calendar ⚠️",
                        "Enable it in System Settings › Privacy & Security › Automation", valid=False)
    match = re.search(r"execution error: (.*) \(-?\d+\)", stderr)
    message = match.group(1) if match else stderr.strip()
    return makeItem(f"{message} ⚠️", "Check the calendar names in the workflow configuration", valid=False)


def getEvents(calendars, days):
    command = ['osascript', '-e', scpt, ",".join(calendars), str(days)]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        return None, calendarError(result.stderr)

    events = []
    for record in result.stdout.rstrip('\n').split(RECORD_SEP):
        fields = record.split(FIELD_SEP)
        if len(fields) != 3:
            continue
        events.append({'start': float(fields[0]), 'location': fields[1], 'calendar': fields[2]})
    events.sort(key=lambda e: e['start'])
    return events, None


def main():
    myARG = sys.argv[1].strip() if len(sys.argv) > 1 else ''

    if not MYCALlist:
        output([makeItem("No calendar configured ⚠️",
                         "Set one or more calendar names in the workflow configuration", valid=False)])
        return

    try:
        nDays = int(MYDAYS)
    except ValueError:
        output([makeItem(f"Invalid number of days: '{MYDAYS}' ⚠️",
                         "Set Days to a whole number in the workflow configuration", valid=False)])
        return

    if myARG and not contains_zipcode(myARG):
        output([makeItem("Enter a valid ZIP code ⚠️", "Or leave empty to show all locations", valid=False)])
        return

    events, error = getEvents(MYCALlist, nDays)
    if error:
        output([error])
        return

    myFutDate = getDate(nDays)
    ZIPs = myARG or "All"

    allEvents = [e for e in events if myARG in e['location']]
    allAdresses = unique(e['location'] for e in allEvents)
    log(allAdresses)

    if not allAdresses:
        output([makeItem(f"No event locations found until {myFutDate}",
                         f"ZIP code: {ZIPs}", valid=False)])
        return

    items = []
    for startRec in range(0, len(allAdresses), MAX_STOPS):
        currSubset = allAdresses[startRec:startRec + MAX_STOPS]
        endRec = startRec + len(currSubset)
        log(f"{startRec}-{endRec}: {currSubset}")
        items.append(makeItem(f"All crews: ({startRec+1}-{endRec}) until {myFutDate}",
                              f"ZIP code: {ZIPs}", makeFinalString(currSubset)))

    for myCurrCal in MYCALlist:
        crewAdresses = unique(e['location'] for e in allEvents
                              if e['calendar'].casefold() == myCurrCal.casefold())
        if crewAdresses:
            items.append(makeItem(f"{myCurrCal} – Locations until {myFutDate}: {len(crewAdresses)}",
                                  "↩️ to open in Google Maps", makeFinalString(crewAdresses),
                                  icon="icons/crew.png"))
        else:
            items.append(makeItem(f"{myCurrCal} – no locations until {myFutDate}",
                                  f"ZIP code: {ZIPs}", valid=False, icon="icons/crew.png"))

    output(items)


if __name__ == "__main__":
    main()
