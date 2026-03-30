#!/bin/bash
# List events in a date range
# Usage: cal-events.sh [days_ahead] [calendar_name]
# Examples:
#   cal-events.sh              # Today's events from all calendars
#   cal-events.sh 7            # Next 7 days from all calendars
#   cal-events.sh 7 Personal   # Next 7 days from Personal calendar only
#
# Uses icalBuddy for reliable access to all calendar providers (iCloud, Google, Exchange)

DAYS_AHEAD="${1:-0}"
CALENDAR_NAME="${2:-}"

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

OUTPUT=$(icalBuddy "${ARGS[@]}" eventsFrom:today to:"today+${DAYS_AHEAD}" | sed $'s/\033\[[0-9;]*m//g')

if [[ -z "$OUTPUT" ]]; then
    echo "No events found"
else
    echo "$OUTPUT"
fi
