#!/usr/bin/env bun
/**
 * X/Twitter Brave Skill - Bookmarks
 * Reads bookmarked tweets using browser automation
 */

console.log(`🔖 Fetching bookmarks...\n`);

const CDP_PORT = 18801;
const BOOKMARKS_URL = 'https://x.com/i/bookmarks';

// Connect to browser CDP
const result = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
const allTargets = await result.json();
const pages = allTargets.filter((t: any) => t.type === 'page');

if (!pages || pages.length === 0) {
  console.error('❌ No browser pages found. Make sure Brave is running with your profile.');
  process.exit(1);
}

// Open bookmarks in a new tab via CDP (PUT required by Brave)
const createRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?${BOOKMARKS_URL}`, { method: 'PUT' });
const newTab = await createRes.json();
const wsUrl = newTab.webSocketDebuggerUrl;

const ws = new WebSocket(wsUrl);
await new Promise((resolve) => { ws.onopen = resolve; });

// Wait for page to load
await new Promise((resolve) => setTimeout(resolve, 5000));

// Extract bookmarks
ws.send(JSON.stringify({
  id: 1,
  method: 'Runtime.evaluate',
  params: {
    expression: `JSON.stringify(
      Array.from(document.querySelectorAll('article[data-testid="tweet"]')).slice(0, 20).map(tweet => {
        const textEl = tweet.querySelector('[data-testid="tweetText"]');
        const timeEl = tweet.querySelector('time');
        const authorEl = tweet.querySelector('[data-testid="User-Name"]');
        const linkEl = tweet.querySelector('a[href*="/status/"]');

        return {
          text: textEl?.innerText || '',
          time: timeEl?.getAttribute('datetime') || '',
          author: authorEl?.innerText?.split('\\n')[0] || '',
          url: linkEl ? 'https://x.com' + linkEl.getAttribute('href') : ''
        };
      })
    )`,
    returnByValue: true
  }
}));

const bookmarks: any[] = await new Promise((resolve) => {
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

console.log(`Found ${bookmarks.length} bookmarks:\n`);
console.log('='.repeat(60));

bookmarks.forEach((bookmark: any, i: number) => {
  console.log(`\n[${i + 1}] ${bookmark.author}`);
  console.log(`    ${bookmark.time}`);
  console.log(`    ${bookmark.text.substring(0, 200)}${bookmark.text.length > 200 ? '...' : ''}`);
  if (bookmark.url) {
    console.log(`    🔗 ${bookmark.url}`);
  }
});

console.log('\n' + '='.repeat(60));
