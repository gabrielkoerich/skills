#!/usr/bin/env bun
/**
 * X/Twitter Chrome Skill - Read Tweet/Thread
 * Reads a specific tweet or thread using browser automation
 */

const url = process.argv[2];

if (!url) {
  console.log('Usage: bun run read.ts https://x.com/username/status/1234567890');
  process.exit(1);
}

console.log(`📖 Reading tweet/thread...\n`);

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
      params: { url }
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id === 1) {
      setTimeout(resolve, 3000);
    }
  };
  
  ws.onerror = reject;
});

// Extract tweet content
ws.send(JSON.stringify({
  id: 2,
  method: 'Runtime.evaluate',
  params: {
    expression: `
      (() => {
        const mainTweet = document.querySelector('article[data-testid="tweet"]:first-child');
        if (!mainTweet) return null;
        
        const textEl = mainTweet.querySelector('[data-testid="tweetText"]');
        const timeEl = mainTweet.querySelector('time');
        const authorEl = mainTweet.querySelector('[data-testid="User-Name"]');
        const stats = mainTweet.querySelectorAll('[data-testid$="count"]');
        
        // Get replies
        const replies = Array.from(document.querySelectorAll('article[data-testid="tweet"]')).slice(1, 6).map(reply => {
          const replyText = reply.querySelector('[data-testid="tweetText"]');
          const replyAuthor = reply.querySelector('[data-testid="User-Name"]');
          const replyTime = reply.querySelector('time');
          return {
            author: replyAuthor?.innerText?.split('\\n')[0] || '',
            text: replyText?.innerText || '',
            time: replyTime?.getAttribute('datetime') || ''
          };
        });
        
        return {
          text: textEl?.innerText || '',
          time: timeEl?.getAttribute('datetime') || '',
          author: authorEl?.innerText?.split('\\n')[0] || '',
          replies: stats[0]?.innerText || '0',
          reposts: stats[1]?.innerText || '0',
          likes: stats[2]?.innerText || '0',
          replyTweets: replies
        };
      })()
    `,
    returnByValue: true
  }
}));

const tweet = await new Promise((resolve) => {
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id === 2) {
      resolve(data.result?.value);
    }
  };
});

ws.close();

if (!tweet) {
  console.error('❌ Could not extract tweet content');
  process.exit(1);
}

console.log('='.repeat(60));
console.log(`\n👤 ${tweet.author}`);
console.log(`🕐 ${tweet.time}`);
console.log('\n' + tweet.text);
console.log(`\n💬 ${tweet.replies}  🔁 ${tweet.reposts}  ❤️ ${tweet.likes}`);

if (tweet.replyTweets.length > 0) {
  console.log('\n' + '-'.repeat(60));
  console.log(`\n📥 ${tweet.replyTweets.length} Replies:\n`);
  
  tweet.replyTweets.forEach((reply, i) => {
    console.log(`  [${i + 1}] ${reply.author} · ${reply.time}`);
    console.log(`       ${reply.text.substring(0, 150)}${reply.text.length > 150 ? '...' : ''}`);
    console.log('');
  });
}

console.log('='.repeat(60));
