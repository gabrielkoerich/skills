---
name: bird
description: bird is a fast X CLI for tweeting, replying, and reading via X/Twitter GraphQL (cookie auth). Requires bird cli installed (bun add -g @steipete/bird)
---


# Bird Skill - X/Twitter Access

Read and search X (Twitter) using the `bird` CLI with Chrome cookie extraction.

## Requirements

Install the bird CLI:

```bash
bun add -g @steipete/bird
```

Requires a Chrome profile logged into x.com (see Chrome Profile section below).

## Usage

```bash
# Read a tweet/thread
bird read https://x.com/username/status/1234567890 --chrome-profile claude --plain

# Read replies
bird replies https://x.com/username/status/1234567890 --chrome-profile claude

# Search tweets
bird search "Solana traders" --limit 20 --chrome-profile claude

# User timeline
bird timeline @username --limit 10 --chrome-profile claude
```

## Chrome Profile

Uses the **claude** Chrome profile. Make sure you're logged into x.com in that profile, or setup another profile.

## Authentication

Bird extracts cookies automatically from the specified Chrome profile. If it fails, cookies can be extracted manually from Chrome DevTools.

## Rate Limits

- Search: ~180 req/15min
- Timeline: ~500 req/15min  
- Read tweet: ~900 req/15min
