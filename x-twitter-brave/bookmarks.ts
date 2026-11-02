#!/usr/bin/env bun
/**
 * X/Twitter Brave Skill - Bookmarks
 * Reads bookmarked tweets using browser automation, scrolling to load more
 */

const args = process.argv.slice(2);
const scrollsArg = args.indexOf('--scrolls');
const MAX_SCROLLS = scrollsArg >= 0 ? Number(args[scrollsArg + 1]) : 15;

console.log(`🔖 Fetching bookmarks...\n`);

const CDP_PORT = 18801;
const BOOKMARKS_URL = 'https://x.com/i/bookmarks';

// Connect to browser CDP
const result = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
const allTargets: any[] = await result.json();
const pages = allTargets.filter((t: any) => t.type === 'page');

if (pages.length === 0) {
  console.error('❌ No browser pages found. Make sure Brave is running with your profile.');
  process.exit(1);
}

// Reuse an open x.com tab, or open one via CDP (PUT required by Brave)
let tab = pages.find((p: any) => p.url?.includes('x.com'));
let createdTab = false;
if (!tab) {
  const createRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?${BOOKMARKS_URL}`, { method: 'PUT' });
  tab = await createRes.json();
  createdTab = true;
}

const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((resolve) => { ws.onopen = resolve; });

let msgId = 1;
function send(method: string, params: any): Promise<any> {
  const id = msgId++;
  return new Promise((resolve) => {
    const handler = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      if (data.id === id) {
        ws.removeEventListener('message', handler);
        resolve(data.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

await send('Page.navigate', { url: BOOKMARKS_URL });
await new Promise((resolve) => setTimeout(resolve, 6000));

const EXTRACT = `JSON.stringify(
  Array.from(document.querySelectorAll('article[data-testid="tweet"]')).map(tweet => {
    const textEl = tweet.querySelector('[data-testid="tweetText"]');
    const timeEl = tweet.querySelector('time');
    const authorEl = tweet.querySelector('[data-testid="User-Name"]');
    const handleEl = tweet.querySelector('[data-testid="User-Name"] a[href^="/"]');
    const linkEl = tweet.querySelector('a[href*="/status/"]');
    const links = Array.from(tweet.querySelectorAll('a[href]'))
      .map(a => a.href)
      .filter(h => h.startsWith('http') && !h.includes('x.com/') && !h.includes('twitter.com/'));

    return {
      text: textEl?.innerText || '',
      time: timeEl?.getAttribute('datetime') || '',
      author: authorEl?.innerText?.split('\\n')[0] || '',
      handle: handleEl?.getAttribute('href')?.slice(1) || '',
      url: linkEl ? 'https://x.com' + linkEl.getAttribute('href') : '',
      links: [...new Set(links)].slice(0, 3)
    };
  })
)`;

// X drops tweets from the DOM as you scroll, so collect after every scroll
const seen = new Map<string, any>();
async function collect(): Promise<number> {
  const res = await send('Runtime.evaluate', { expression: EXTRACT, returnByValue: true });
  const before = seen.size;
  for (const item of JSON.parse(res?.result?.value || '[]')) {
    if (item.url && !seen.has(item.url)) {
      seen.set(item.url, item);
    }
  }

  return seen.size - before;
}

await collect();
for (let i = 0; i < MAX_SCROLLS; i++) {
  await send('Runtime.evaluate', { expression: `window.scrollBy(0, 1500)`, returnByValue: true });
  await new Promise((resolve) => setTimeout(resolve, 2000));
  if (await collect() === 0) {
    break;
  }
}

if (createdTab) {
  await fetch(`http://127.0.0.1:${CDP_PORT}/json/close/${tab.id}`);
}

ws.close();

const bookmarks = Array.from(seen.values());

console.log(`Found ${bookmarks.length} bookmarks:\n`);
console.log('='.repeat(60));

bookmarks.forEach((bookmark: any, i: number) => {
  console.log(`\n[${i + 1}] ${bookmark.author} (@${bookmark.handle})`);
  console.log(`    ${bookmark.time}`);
  console.log(`    ${bookmark.text.substring(0, 400)}${bookmark.text.length > 400 ? '...' : ''}`);
  if (bookmark.url) {
    console.log(`    🔗 ${bookmark.url}`);
  }

  if (bookmark.links.length > 0) {
    console.log(`    🌐 ${bookmark.links.join(', ')}`);
  }
});

console.log('\n' + '='.repeat(60));
