#!/usr/bin/env bun
/**
 * X/Twitter Brave Skill - Timeline Reader
 * Reads a user's timeline using browser automation
 */

const username = process.argv[2]?.replace(/^@/, '');

if (!username) {
  console.log('Usage: bun run timeline.ts @username');
  console.log('       bun run timeline.ts username');
  process.exit(1);
}

console.log(`📱 Fetching timeline for @${username}...\n`);

const CDP_PORT = 18801;

// Open timeline in a new tab via CDP (PUT required by Brave)
const createRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?https://x.com/${username}`, { method: 'PUT' });
const newTab = await createRes.json();
const ws = new WebSocket(newTab.webSocketDebuggerUrl);
await new Promise((resolve) => { ws.onopen = resolve; });

// Wait for page to load
await new Promise((resolve) => setTimeout(resolve, 4000));

// Extract tweets
ws.send(JSON.stringify({
  id: 1,
  method: 'Runtime.evaluate',
  params: {
    expression: `JSON.stringify(
      Array.from(document.querySelectorAll('article[data-testid="tweet"]')).slice(0, 10).map(tweet => {
        const textEl = tweet.querySelector('[data-testid="tweetText"]');
        const timeEl = tweet.querySelector('time');
        const authorEl = tweet.querySelector('[data-testid="User-Name"]');
        const stats = tweet.querySelectorAll('[data-testid$="count"]');

        return {
          text: textEl?.innerText || '',
          time: timeEl?.getAttribute('datetime') || '',
          author: authorEl?.innerText?.split('\\n')[0] || '',
          replies: stats[0]?.innerText || '0',
          reposts: stats[1]?.innerText || '0',
          likes: stats[2]?.innerText || '0'
        };
      })
    )`,
    returnByValue: true
  }
}));

const tweets: any[] = await new Promise((resolve) => {
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id === 1) {
      resolve(JSON.parse(data.result?.result?.value || '[]'));
    }
  };
});

// Close the tab we opened
await fetch(`http://127.0.0.1:${CDP_PORT}/json/close/${newTab.id}`);
ws.close();

// Output results
console.log(`Found ${tweets.length} tweets:\n`);
console.log('='.repeat(60));

tweets.forEach((tweet: any, i: number) => {
  console.log(`\n[${i + 1}] ${tweet.author}`);
  console.log(`    ${tweet.time}`);
  console.log(`    ${tweet.text.substring(0, 200)}${tweet.text.length > 200 ? '...' : ''}`);
  console.log(`    💬 ${tweet.replies}  🔁 ${tweet.reposts}  ❤️ ${tweet.likes}`);
});

console.log('\n' + '='.repeat(60));
