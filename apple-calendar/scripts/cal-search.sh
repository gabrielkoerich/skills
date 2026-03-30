#!/bin/bash
# Search events by text (summary, location, or description)
# Usage: cal-search.sh <query> [days_ahead] [calendar_name]
# Examples:
#   cal-search.sh "meeting"           # Search all calendars, next 30 days
#   cal-search.sh "dentist" 90        # Search next 90 days
#   cal-search.sh "standup" 14 Work   # Search Work calendar, next 14 days
#
# Uses icalBuddy for reliable access to all calendar providers (iCloud, Google, Exchange)

QUERY="${1:-}"
DAYS_AHEAD="${2:-30}"
CALENDAR_NAME="${3:-}"

if [ -z "$QUERY" ]; then
    echo "Usage: cal-search.sh <query> [days_ahead] [calendar_name]"
    exit 1
fi

if ! command -v icalBuddy &>/dev/null; then
    echo "Error: icalBuddy not found. Install with: brew install ical-buddy"
    exit 1
fi

ARGS=(-f -nc -nrd)
ARGS+=(-b "")
ARGS+=(-df "%Y-%m-%d")
ARGS+=(-tf "%H:%M")
ARGS+=(-iep "title,datetime,location,calendar,uid")
ARGS+=(-po "uid,title,datetime,location,calendar")
ARGS+=(-ps "| | |")
ARGS+=(-ss "")

if [[ -n "$CALENDAR_NAME" ]]; then
    ARGS+=(-ic "$CALENDAR_NAME")
fi

OUTPUT=$(icalBuddy "${ARGS[@]}" eventsFrom:today to:"today+${DAYS_AHEAD}" | sed $'s/\033\[[0-9;]*m//g' | grep -i "$QUERY")

if [[ -z "$OUTPUT" ]]; then
    echo "No events found matching: $QUERY"
else
    echo "$OUTPUT"
fi
