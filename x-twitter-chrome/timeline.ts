#!/usr/bin/env bun
/**
 * X/Twitter Chrome Skill - Timeline Reader
 * Reads a user's timeline using browser automation
 */

const username = process.argv[2]?.replace(/^@/, '');

if (!username) {
  console.log('Usage: bun run timeline.ts @username');
  console.log('       bun run timeline.ts username');
  process.exit(1);
}

console.log(`📱 Fetching timeline for @${username}...\n`);

// Use browser automation via Chrome DevTools Protocol
const result = await fetch('http://127.0.0.1:18800/json');
const pages = await result.json();

if (!pages || pages.length === 0) {
  console.error('❌ No browser pages found. Make sure Chrome is running with your profile.');
  process.exit(1);
}

const page = pages[0];
const wsUrl = page.webSocketDebuggerUrl;

// Navigate to user timeline
const ws = new WebSocket(wsUrl);

await new Promise((resolve, reject) => {
  ws.onopen = () => {
    ws.send(JSON.stringify({
      id: 1,
      method: 'Page.navigate',
      params: { url: `https://x.com/${username}` }
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id === 1) {
      setTimeout(resolve, 3000); // Wait for page load
    }
  };
  
  ws.onerror = reject;
});

// Extract tweets
ws.send(JSON.stringify({
  id: 2,
  method: 'Runtime.evaluate',
  params: {
    expression: `
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
    `,
    returnByValue: true
  }
}));

const tweets = await new Promise((resolve) => {
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id === 2) {
      resolve(data.result?.value || []);
    }
  };
});

ws.close();

// Output results
console.log(`Found ${tweets.length} tweets:\n`);
console.log('='.repeat(60));

tweets.forEach((tweet, i) => {
  console.log(`\n[${i + 1}] ${tweet.author}`);
  console.log(`    ${tweet.time}`);
  console.log(`    ${tweet.text.substring(0, 200)}${tweet.text.length > 200 ? '...' : ''}`);
  console.log(`    💬 ${tweet.replies}  🔁 ${tweet.reposts}  ❤️ ${tweet.likes}`);
});

console.log('\n' + '='.repeat(60));
