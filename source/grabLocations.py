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

CALENDAR_SETTINGS = "x-apple.systempreferences:com.apple.preference.security?Privacy_Calendars"


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


def routeItems(label, addresses, untilDate, subtitle, icon=""):
    # One item per route of at most MAX_STOPS stops
    n = len(addresses)
    items = []
    for startRec in range(0, n, MAX_STOPS):
        currSubset = addresses[startRec:startRec + MAX_STOPS]
        endRec = startRec + len(currSubset)
        log(f"{label} {startRec}-{endRec}: {currSubset}")
        if n <= MAX_STOPS:
            title = f"{label} – {n} location{'s' if n > 1 else ''} until {untilDate}"
        elif endRec - startRec == 1:
            title = f"{label} – stop {endRec} of {n} until {untilDate}"
        else:
            title = f"{label} – stops {startRec+1}-{endRec} of {n} until {untilDate}"
        items.append(makeItem(title, subtitle, makeFinalString(currSubset), icon=icon))
    return items


def unique(locations):
    # De-duplicate, keeping the first (chronological) occurrence
    return list(dict.fromkeys(loc for loc in locations if loc))


# JavaScript for Automation reading events through EventKit: fast on large
# calendars (no Calendar.app scripting) and expands repeating events
jxa = '''
ObjC.import('EventKit');

function requestAccess(store) {
    let done = false;
    const callback = () => { done = true; };
    if (store.respondsToSelector('requestFullAccessToEventsWithCompletion:')) {
        store.requestFullAccessToEventsWithCompletion(callback);  // macOS 14+
    } else {
        store.requestAccessToEntityTypeCompletion($.EKEntityTypeEvent, callback);
    }
    const deadline = $.NSDate.dateWithTimeIntervalSinceNow(60);
    while (!done && deadline.timeIntervalSinceNow > 0) {
        $.NSRunLoop.currentRunLoop.runModeBeforeDate($.NSDefaultRunLoopMode, $.NSDate.dateWithTimeIntervalSinceNow(0.2));
    }
}

function run(argv) {
    const names = argv[0].split(',');
    const days = parseInt(argv[1]);
    let store = $.EKEventStore.alloc.init;
    // the bridge returns the enum as a string ("3"), so convert before comparing
    const authStatus = () => Number($.EKEventStore.authorizationStatusForEntityType($.EKEntityTypeEvent));

    // 0 = not determined, 1 = restricted, 2 = denied,
    // 3 = full access (macOS 14+) / authorized (older), 4 = write only
    if (authStatus() === 0) {
        requestAccess(store);
        store = $.EKEventStore.alloc.init;
    }
    const status = authStatus();
    if (status !== 3) {
        return JSON.stringify({error: 'notAuthorized', status: status});
    }

    const wanted = names.map(n => n.toLowerCase());
    const calendars = ObjC.unwrap(store.calendarsForEntityType($.EKEntityTypeEvent))
        .filter(c => wanted.includes(ObjC.unwrap(c.title).toLowerCase()));
    const found = calendars.map(c => ObjC.unwrap(c.title).toLowerCase());
    const missing = names.filter(n => !found.includes(n.toLowerCase()));
    if (missing.length) {
        return JSON.stringify({error: 'notFound', calendars: missing});
    }

    const start = $.NSCalendar.currentCalendar.startOfDayForDate($.NSDate.date);
    const end = start.dateByAddingTimeInterval((days + 1) * 86400);  // through the end of day `days`
    const predicate = store.predicateForEventsWithStartDateEndDateCalendars(start, end, $(calendars));
    const events = ObjC.unwrap(store.eventsMatchingPredicate(predicate)).map(e => ({
        start: Number(e.startDate.timeIntervalSince1970),
        location: ObjC.unwrap(e.location) || '',
        calendar: ObjC.unwrap(e.calendar.title),
    }));
    return JSON.stringify({events: events});
}
'''


def calendarError(result):
    if result.get('error') == 'notAuthorized':
        return makeItem("Alfred needs Full Access to your Calendars ⚠️",
                        f"↩ to open Privacy & Security › Calendars, then set Alfred to Full Access (status {result.get('status')})",
                        CALENDAR_SETTINGS)
    if result.get('error') == 'notFound':
        return makeItem(f"Calendar not found: {', '.join(result['calendars'])} ⚠️",
                        "Check the calendar names in the workflow configuration", valid=False)
    return makeItem(f"Could not read Calendar: {result.get('error')} ⚠️", valid=False)


def getEvents(calendars, days):
    command = ['osascript', '-l', 'JavaScript', '-e', jxa, ",".join(calendars), str(days)]
    proc = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    try:
        result = json.loads(proc.stdout)
    except ValueError:
        log(proc.stderr)
        result = {'error': proc.stderr.strip() or 'no output'}
    if 'error' in result:
        return None, calendarError(result)

    events = sorted(result['events'], key=lambda e: e['start'])
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

    subtitle = f"ZIP code: {ZIPs} · ↩ to open in Google Maps"
    items = []
    # The combined route only adds something when there are several calendars
    if len(MYCALlist) > 1:
        items += routeItems("All calendars", allAdresses, myFutDate, subtitle)

    for myCurrCal in MYCALlist:
        calAdresses = unique(e['location'] for e in allEvents
                             if e['calendar'].casefold() == myCurrCal.casefold())
        if calAdresses:
            items += routeItems(myCurrCal, calAdresses, myFutDate, subtitle, icon="icons/crew.png")
        else:
            items.append(makeItem(f"{myCurrCal} – no locations until {myFutDate}",
                                  f"ZIP code: {ZIPs}", valid=False, icon="icons/crew.png"))

    output(items)


if __name__ == "__main__":
    main()
