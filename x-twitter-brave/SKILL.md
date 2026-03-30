---
name: x-twitter-brave
description: Read and search X/Twitter using Brave browser automation with an authenticated local profile.
---

# X/Twitter Brave Skill

Read and search X (Twitter) using browser automation with the logged-in Brave profile.

## Prerequisites

1. Brave browser with **your profile** running
2. Logged into x.com in that profile

## Start Brave (if not running)

```bash
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
  --user-data-dir="$HOME/.claude/browser/<profile>/user-data" \
  --remote-debugging-port=18801
```

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

## How It Works

Uses Chrome DevTools Protocol (CDP) to:
1. Connect to running Brave instance on port 18801
2. Navigate to X pages
3. Extract tweet content via DOM queries
4. Return formatted text output

## Files

- `timeline.ts` - Get user tweets
- `read.ts` - Read tweet/thread with replies
- `bookmarks.ts` - Get your bookmarks
- `search.ts` - Search tweets

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
