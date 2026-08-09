#!/usr/bin/python3 
# 
# Overcast ☁️   🌡️+40°F (feels +32°F, 79%) 🌬️↓2mph 🌖&m Sat Mar 11 12:45:33 2023
#W10Q1 – 70 ➡️ 294 – 304 ❇️ 60


"""
GRAB ICAL MEETING LOCATIONS AND OPEN IN GOOGLE MAPS

"""

import os
from subprocess import check_output
#import webbrowser
import sys
import re
import json
from datetime import datetime, timedelta



MYCAL = os.getenv('MYCALENDAR', '')
MYDAYS = os.getenv('MYDAYS') or '7'  # `or` (not getenv default) so a blank config field doesn't break int(MYDAYS)
MYCALlist = MYCAL.split(",")
MYCALlist = [x.strip () for x in MYCALlist if x.strip()]


def log(s, *args):
    if args:
        s = s % args
    print(s, file=sys.stderr)


def contains_zipcode(address):
    pattern = r"\b\d{5}(?:-\d{4})?\b"
    match = re.search(pattern, address)
    return bool(match)



def getDate (deltaDays):
    # Calculate the date N days from today
    future_date = datetime.now() + timedelta(days=deltaDays)

    # Format the date as 'Wednesday, May 10, 2023'
    formatted_date = future_date.strftime('%A, %B %d, %Y')
    return formatted_date

def makeFinalString(currSubset):
    subsetR = "/".join(currSubset)
    subsetR = ' '.join (subsetR.split ())
    subsetR = subsetR.replace('\n', ' ')

    # Replace all spaces with '+'    
    subsetR = subsetR.replace(' ', '+')
    
    if subsetR.endswith ("+"):
        subsetR = subsetR.rstrip('+')
    
    finalString = f"https://www.google.com/maps/dir/{subsetR}"
    return finalString
    


myARG = sys.argv[1]
myZIP = contains_zipcode (myARG)
MY_OUTPUT = {"items": []}


scpt = '''
on run {myCalendars, myDays}
    set eventInfoList to {}
    set todayDate to (current date) - ((time of (current date)) mod days)
    set futureDate to todayDate + (myDays * days) -- Add myDays days to get the future date
    set AppleScript's text item delimiters to ","
    set calendarList to every text item of myCalendars
    set AppleScript's text item delimiters to {""} -- Reset delimiters

    tell application "Calendar"
        repeat with myCalendar in calendarList
            set theCalendar to calendar myCalendar
            set theEvents to every event of theCalendar
            repeat with theEvent in theEvents
                set startDate to start date of theEvent
                set startDate to startDate - ((time of startDate) mod days)
                if startDate is greater than or equal to todayDate and startDate is less than or equal to futureDate then
                    set theLoc to location of theEvent
                    if theLoc is missing value then set theLoc to ""
                    set eventInfo to {}
                    set end of eventInfo to theLoc
                    set end of eventInfo to name of theCalendar
                    set end of eventInfoList to eventInfo
                end if
            end repeat
        end repeat
    end tell

    set AppleScript's text item delimiters to ":::"
    set eventInfoList to eventInfoList as text
    set AppleScript's text item delimiters to ""
    return eventInfoList
end run

'''

calendarString = ",".join(MYCALlist) #passing the list of calendars as a list
command = ['osascript', '-e', scpt, calendarString, str(MYDAYS)]
#p = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)

output = check_output(command).decode('utf-8').strip()
myResults = output.split(":::")
#log (myResults)


resultDict = []
for i in range(0, len(myResults) - 1, 2):
    item = {'location': myResults[i], 'calendar': myResults[i+1]}
    resultDict.append(item)


allEvents = [add for add in resultDict if myARG in add['location']]
allAdresses = list(set([add['location'] for add in allEvents ]))
log (allAdresses)
allAdresses = [x for x in allAdresses if x]

if len (allAdresses) > 10:
    nSplits = int(len (allAdresses) / 10) + 1
else:
    nSplits = 1

#log (nSplits)
if myARG == '':
    ZIPs = "All"
else:
    ZIPs = myARG

myFutDate = getDate(int(MYDAYS))

if myZIP or myARG == '':
    for mySplit in range (0,nSplits):
        startRec = mySplit*10
        if mySplit == nSplits-1:
            endRec = len(allAdresses)
        else:
            endRec = startRec+10
        
        
        currSubset = allAdresses[startRec:endRec]
        log (f"{startRec}-{endRec}: {currSubset}")

        finalString = makeFinalString (currSubset)

        MY_OUTPUT["items"].append({
                            "title": f"All crews: ({startRec+1}-{endRec}) until {myFutDate}",
                            'subtitle': f"ZIP code: {ZIPs}",
                            'valid': True,
                            
                            
                            "icon": {
                                
                            },
                            'arg': finalString
                                }) 
                            #webbrowser.open_new_tab(finalString)
    for myCurrCal in MYCALlist:
        currCrew = [add for add in allEvents if add['calendar'] == myCurrCal]
        allAdresses = list(set([add['location'] for add in currCrew if add['location']]))
        finalString = makeFinalString (allAdresses)
        MY_OUTPUT["items"].append({
                        "title": f"{myCurrCal} – Locations until {myFutDate}: {len (allAdresses)}",
                        'subtitle': "↪️ to open in Google Maps",
                        'valid': True,
                        
                        
                        "icon": {
                            'path': "icons/crew.png"
                        },
                        'arg': finalString
                            }) 
                        #webbrowser.open_new_tab(finalString)

else:
	#log ("NOPE")
    MY_OUTPUT["items"].append({
                        "title": f"Enter a valid ZIP code ⚠️",
                        'subtitle': "",
                        'valid': True,
                        
                        
                        "icon": {
                            
                        },
                        'arg': ""
                            }) 
                        #webbrowser.open_new_tab(finalString)



print (json.dumps(MY_OUTPUT))


"""
scpt = '''
on run {myCalendar, myDays}
    set eventLocations to {}
    set todayDate to (current date) - ((time of (current date)) mod days)
    set futureDate to todayDate + (myDays * days) -- Add 7 days to get the future date

    tell application "Calendar"
        set theCalendar to calendar myCalendar
        set theEvents to every event of theCalendar
        repeat with theEvent in theEvents
            set startDate to start date of theEvent
            set startDate to startDate - ((time of startDate) mod days)
            if startDate is greater than or equal to todayDate and startDate is less than or equal to futureDate then
                set the end of eventLocations to (location of theEvent)
            end if
        end repeat
    end tell
    
    set AppleScript's text item delimiters to ":::"
    set eventLocations to eventLocations as text
    set AppleScript's text item delimiters to ""
    
    return eventLocations
end run




if myZIP or myARG == '':
    #log ("valid ZIP")
    for myCurrCal in MYCALlist:
                args = [myCurrCal.strip(),MYDAYS]
                p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                stdout, stderr = p.communicate(scpt)
                myResults = stdout.split(":::")
                if myResults[-1].endswith('\n'):
                    myResults[-1] = myResults[-1].rstrip('\n')
                subsetRS = set([address for address in myResults if myARG in address])
                subsetRS = [x for x in subsetRS if x]
                subsetR = "/".join(subsetRS)
                subsetR = subsetR.replace('\n', ' ')
            
                # Replace all spaces with '+'    
                subsetR = subsetR.replace(' ', '+')
                
                if subsetR.endswith ("+"):
                    subsetR = subsetR.rstrip('+')
				
                finalString = f"https://www.google.com/maps/dir/{subsetR}"
                myFutDate = getDate(int(MYDAYS))
                
                
                MY_OUTPUT["items"].append({
                        "title": f"{myCurrCal} – Locations until {myFutDate}: {len (subsetRS)}",
                        'subtitle': "↪️ to open in Google Maps",
                        'valid': True,
                        
                        
                        "icon": {
                            
                        },
                        'arg': finalString
                            }) 
                        #webbrowser.open_new_tab(finalString)


else:
	#log ("NOPE")
    MY_OUTPUT["items"].append({
                        "title": f"Enter a valid ZIP code ⚠️",
                        'subtitle': "",
                        'valid': True,
                        
                        
                        "icon": {
                            
                        },
                        'arg': ""
                            }) 
                        #webbrowser.open_new_tab(finalString)

        


print (json.dumps(MY_OUTPUT))


"""
