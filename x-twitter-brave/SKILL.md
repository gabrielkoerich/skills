---
name: x-twitter-brave
description: Read and search X/Twitter using Brave browser automation with an authenticated local profile.
---

# X/Twitter Brave Skill

Read and search X (Twitter) using browser automation with the logged-in Brave profile.

## Prerequisites

1. Brave browser with **your profile** running
2. Logged into x.com in that profile

## Start and stop Brave

Several agents share one headless Brave on port 18801, and only one Brave can hold a profile. Pick one run id and use it for both calls:

```bash
python3 scripts/session.py start my-job-202610201030   # launches Brave if nothing listens on 18801
# ... run the scripts below ...
python3 scripts/session.py stop my-job-202610201030    # also when a step failed
```

`stop` quits Brave only when no other run is registered. Never kill that Brave yourself, another agent may be mid-run. A run that never called `stop` stops counting after 2 hours. Close every tab you open over CDP (`curl -s http://127.0.0.1:18801/json/close/<tab id>`), the scripts below close their own. Set `X_BRAVE_PROFILE` to use a profile other than `~/.claude/browser/Default`. `stop` quits only a Brave that `start` launched, never one started by hand.

It runs on macOS and Linux. It finds the macOS app, else `brave-browser`, `brave` or `brave-browser-stable` on PATH (the Debian/Ubuntu package installs `/usr/bin/brave-browser`). Set `BRAVE_BIN` to point elsewhere.

Brave runs headless. Use a window only when it is needed, such as logging in to x.com, or when the user asks for one:

```bash
python3 scripts/session.py start --window login-202610201030   # refuses while another run holds the profile
```

On a Linux desktop (such as Xfce) the window opens on the desktop's screen. When run from a job or SSH with no `DISPLAY`, the script uses `:0` and `~/.Xauthority`, so the window needs that user logged in to the desktop. Headless runs need no desktop session.

Run it as the user that owns the profile, never as root: Brave starts as root only with `--no-sandbox`, which these untrusted pages must not get, and root's home holds a different profile. The script refuses root.

## Usage

### Read User Timeline
```bash
bun run timeline.ts @username
```

### Read a Tweet/Thread
```bash
bun run read.ts https://x.com/username/status/1234567890
```

### Get Bookmarks
```bash
bun run bookmarks.ts
```

### Search
```bash
bun run search.ts "Solana traders"
```

### Trending Topics
```bash
bun run trending.ts              # all local trends
bun run trending.ts --global      # worldwide trends only (filters out location-specific)
bun run trending.ts --news        # trends + today's news
bun run trending.ts --global --news  # worldwide trends + news
```

## How It Works

Uses Chrome DevTools Protocol (CDP) to:
1. Connect to running Brave instance on port 18801
2. Navigate to X pages
3. Extract content via `innerText` parsing (resilient to DOM changes)
4. Return formatted text output

## Files

- `timeline.ts` - Get user tweets
- `read.ts` - Read tweet/thread with replies
- `bookmarks.ts` - Get your bookmarks
- `search.ts` - Search tweets
- `trending.ts` - Trending topics and news
- `scripts/session.py` - Start and stop the shared Brave

## Troubleshooting

**"No browser pages found"**
- Make sure Brave is running with your configured profile
- Check port 18801 is accessible: `curl http://127.0.0.1:18801/json`

**Empty results**
- X may have changed their DOM structure
- Try increasing the wait time in the scripts
- Check if you're still logged in

## Rate Limits

Built-in delays between requests to avoid rate limiting.
