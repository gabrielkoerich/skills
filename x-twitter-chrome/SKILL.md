---
name: x-twitter-chrome
description: Read and search X/Twitter using Chrome browser automation with an authenticated local profile.
---

# X/Twitter Chrome Skill

Read and search X (Twitter) using browser automation with the logged-in Chrome profile.

## Prerequisites

1. Chrome browser with **your profile** running
2. Logged into x.com in that profile

## Start Chrome (if not running)

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="$HOME/.claude/browser/<profile>/user-data" \
  --remote-debugging-port=18800
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
1. Connect to running Chrome instance on port 18800
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
- Make sure Chrome is running with your configured profile
- Check port 18800 is accessible: `curl http://127.0.0.1:18800/json`

**Empty results**
- X may have changed their DOM structure
- Try increasing the wait time in the scripts
- Check if you're still logged in

## Rate Limits

Built-in delays between requests to avoid rate limiting.
