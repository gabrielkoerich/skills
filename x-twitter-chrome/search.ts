#!/usr/bin/env bun
/**
 * X/Twitter Chrome Skill - Search
 * Search tweets using browser automation
 */

const query = process.argv.slice(2).join(' ');

if (!query) {
  console.log('Usage: bun run search.ts "your search query"');
  process.exit(1);
}

console.log(`🔍 Searching for: "${query}"\n`);

const result = await fetch('http://127.0.0.1:18800/json');
const pages = await result.json();

if (!pages || pages.length === 0) {
  console.error('❌ No browser pages found. Make sure Chrome is running with your profile.');
  process.exit(1);
}

const page = pages[0];
const wsUrl = page.webSocketDebuggerUrl;

const ws = new WebSocket(wsUrl);

await new Promise((resolve, reject) => {
  ws.onopen = () => {
    ws.send(JSON.stringify({
      id: 1,
      method: 'Page.navigate',
      params: { url: `https://x.com/search?q=${encodeURIComponent(query)}&src=typed_query` }
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id === 1) {
      setTimeout(resolve, 4000);
    }
  };
  
  ws.onerror = reject;
});

// Extract search results
ws.send(JSON.stringify({
  id: 2,
  method: 'Runtime.evaluate',
  params: {
    expression: `
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
    `,
    returnByValue: true
  }
}));

const results = await new Promise((resolve) => {
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id === 2) {
      resolve(data.result?.value || []);
    }
  };
});

ws.close();

console.log(`Found ${results.length} results:\n`);
console.log('='.repeat(60));

results.forEach((tweet, i) => {
  console.log(`\n[${i + 1}] ${tweet.author}`);
  console.log(`    ${tweet.time}`);
  console.log(`    ${tweet.text.substring(0, 200)}${tweet.text.length > 200 ? '...' : ''}`);
  if (tweet.url) {
    console.log(`    🔗 ${tweet.url}`);
  }
});

console.log('\n' + '='.repeat(60));
