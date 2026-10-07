#!/usr/bin/env bun
/**
 * X/Twitter Brave Skill - Trending
 * Reads trending topics and/or news using browser automation
 *
 * Usage:
 *   bun run trending.ts             # all trends
 *   bun run trending.ts --global    # only worldwide/global trends
 *   bun run trending.ts --news       # trends + today's news
 *   bun run trending.ts --global --news  # global + news
 */

const args = process.argv.slice(2);
const globalOnly = args.includes('--global');
const includeNews = args.includes('--news');

const icon = includeNews ? '📰' : (globalOnly ? '🌍' : '🔥');
const label = includeNews ? 'trending + news' : (globalOnly ? 'global trending' : 'trending topics');
console.log(`${icon} Fetching ${label}...\n`);

const CDP_PORT = 18801;
const TRENDING_TAB_URL = 'https://x.com/explore/tabs/trending';
const FOR_YOU_TAB_URL = 'https://x.com/explore/tabs/for_you';

const result = await fetch(`http://127.0.0.1:${CDP_PORT}/json`);
const allTargets = await result.json();
const pages = allTargets.filter((t: any) => t.type === 'page' || t.type === 'other');

if (!pages || pages.length === 0) {
  console.error('❌ No browser pages found. Make sure Brave is running with your profile.');
  process.exit(1);
}

// Fetch a page and extract body text
async function fetchPage(url: string): Promise<string> {
  const createRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?${url}`, { method: 'PUT' });
  const newTab = await createRes.json();
  const wsUrl = newTab.webSocketDebuggerUrl;

  const ws = new WebSocket(wsUrl);
  await new Promise((resolve) => { ws.onopen = resolve; });
  await new Promise((resolve) => setTimeout(resolve, 7000));

  ws.send(JSON.stringify({
    id: 1,
    method: 'Runtime.evaluate',
    params: { expression: `document.body.innerText || ''`, returnByValue: true }
  }));

  const bodyText: string = await new Promise((resolve) => {
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.id === 1) resolve(data.result?.result?.value || '');
    };
  });

  await fetch(`http://127.0.0.1:${CDP_PORT}/json/close/${newTab.id}`);
  ws.close();
  return bodyText;
}

// --- Trends: pull from the trending tab ---
const forYouText = await fetchPage(TRENDING_TAB_URL);
const lines = forYouText.split('\n');

const knownHeaders = ['Global Trending', 'The most popular posts', 'Explore', 'For You', 'Trending', 'News', 'Sports', 'Entertainment'];
const trends: { num: string; meta: string; topic: string }[] = [];
let i = 0;

while (i < lines.length) {
  const num = lines[i]?.trim();
  const next = lines[i + 1]?.trim();

  if (/^\d+$/.test(num) && next === '·') {
    const meta = lines[i + 2]?.trim();
    const topic = lines[i + 3]?.trim();

    if (meta && topic && !knownHeaders.includes(topic)) {
      trends.push({ num, meta, topic });
      i += 4;
      continue;
    }
    const topic2 = lines[i + 4]?.trim();
    if (meta && topic2 && !knownHeaders.includes(topic2)) {
      trends.push({ num, meta, topic: topic2 });
      i += 5;
      continue;
    }
  }
  i++;
}

// --- News: pull from for_you tab which has "Today's News" section ---
const newsLines = includeNews ? (await fetchPage(FOR_YOU_TAB_URL)).split('\n') : [];

const globalTrends = trends.filter(t => !/^Trending in \w/.test(t.meta));
const display = globalOnly ? globalTrends : trends;

if (display.length === 0 && !includeNews) {
  console.log('No trends found (page structure may have changed).');
} else if (display.length > 0) {
  if (globalOnly) console.log(`Found ${display.length} global trending topics:\n`);
  else console.log(`Found ${display.length} trending topics:\n`);
  console.log('='.repeat(60));
  display.forEach((trend) => {
    console.log(`\n[${trend.num}] ${trend.topic}`);
    console.log(`    ${trend.meta}`);
  });
  console.log('\n' + '='.repeat(60));
}

// --- Today's News ---
if (includeNews) {
  const newsIdx = newsLines.findIndex(l => l.includes("Today") && l.includes("News"));
  if (newsIdx !== -1) {
    const newsSection = newsLines.slice(newsIdx + 1);
    const news: { title: string; meta: string }[] = [];
    let j = 0;

    while (j < newsSection.length) {
      const title = newsSection[j]?.trim();
      const meta = newsSection[j + 1]?.trim();

      if (title && meta) {
        // Stop at "Who to follow" section
        if (title.includes('Who to follow')) break;
        // Only include items with a time/post meta (e.g. "21 hours ago · News · 37K posts")
        if (/^\d+ \w+ ago|^Trending now/i.test(meta)) {
          news.push({ title, meta });
          j += 2;
          continue;
        }
      }
      j++;
    }

    if (news.length > 0) {
      console.log(`\n📰 Today's News:\n`);
      console.log('='.repeat(60));
      news.forEach((item, i) => {
        console.log(`\n[${i + 1}] ${item.title}`);
        console.log(`    ${item.meta}`);
      });
      console.log('\n' + '='.repeat(60));
    }
  }
}
