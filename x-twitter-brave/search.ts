#!/usr/bin/env bun
/**
 * X/Twitter Brave Skill - Search
 * Search tweets using browser automation
 */

const query = process.argv.slice(2).join(' ');

if (!query) {
  console.log('Usage: bun run search.ts "your search query"');
  process.exit(1);
}

console.log(`🔍 Searching for: "${query}"\n`);

const CDP_PORT = 18801;
const searchUrl = `https://x.com/search?q=${encodeURIComponent(query)}&src=typed_query`;

// Open search in a new tab via CDP (PUT required by Brave)
const createRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?${searchUrl}`, { method: 'PUT' });
const newTab = await createRes.json();
const ws = new WebSocket(newTab.webSocketDebuggerUrl);
await new Promise((resolve) => { ws.onopen = resolve; });

// Wait for page to load
await new Promise((resolve) => setTimeout(resolve, 5000));

// Extract search results
ws.send(JSON.stringify({
  id: 1,
  method: 'Runtime.evaluate',
  params: {
    expression: `JSON.stringify(
      Array.from(document.querySelectorAll('article[data-testid="tweet"]')).slice(0, 15).map(tweet => {
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

const results: any[] = await new Promise((resolve) => {
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

console.log(`Found ${results.length} results:\n`);
console.log('='.repeat(60));

results.forEach((tweet: any, i: number) => {
  console.log(`\n[${i + 1}] ${tweet.author}`);
  console.log(`    ${tweet.time}`);
  console.log(`    ${tweet.text.substring(0, 200)}${tweet.text.length > 200 ? '...' : ''}`);
  if (tweet.url) {
    console.log(`    🔗 ${tweet.url}`);
  }
});

console.log('\n' + '='.repeat(60));
