#!/usr/bin/env bun
// Headless CDP screenshot with the first installed Chromium-family browser, Brave preferred
// Usage: bun shot.ts <url> [out.png] [--wait=ms] [--width=N] [--height=N] [--full] [--mobile] [--lang=..] [--clear-storage] [--click=sel] [--type=sel=text] [--eval=js] [--step-wait=ms] [--check]

import { existsSync } from "node:fs";

const CDP_PORT = 18801;
const PROFILE = `${process.env.HOME}/.claude/browser/Default/user-data`;

const MAC_APPS = [
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi",
];
const PATH_BINARIES = ["brave-browser", "brave", "chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "microsoft-edge", "vivaldi"];

const candidates = [
  process.env.BROWSER_BIN,
  ...MAC_APPS,
  ...PATH_BINARIES.map((b) => Bun.which(b)),
].filter((p): p is string => typeof p === "string" && p.length > 0);

const BROWSER = candidates.find((p) => existsSync(p));
if (!BROWSER) {
  console.error(
    "No Chromium-family browser found. Looked for: $BROWSER_BIN, " +
      [...MAC_APPS, ...PATH_BINARIES].join(", ") +
      ". Install Brave, Chromium, Chrome, Edge or Vivaldi, or set BROWSER_BIN to the browser binary.",
  );
  process.exit(1);
}
console.error(`browser: ${BROWSER}`);

const args = process.argv.slice(2);
const flags = new Map<string, string>();
const positional: string[] = [];
// --click, --type and --eval can repeat and run in the order given, after the page loads
const actions: { kind: string; value: string }[] = [];
for (const a of args) {
  if (a.startsWith("--")) {
    const eq = a.indexOf("=");
    const k = eq === -1 ? a.slice(2) : a.slice(2, eq);
    const v = eq === -1 ? "true" : a.slice(eq + 1);
    if (k === "click" || k === "type" || k === "eval") {
      actions.push({ kind: k, value: v });
    } else {
      flags.set(k, v);
    }
  } else {
    positional.push(a);
  }
}
const url = positional[0] ?? "http://localhost:5173/";
const out = positional[1] ?? "/tmp/ui-shot.png";
const waitMs = Number(flags.get("wait") ?? 3500);
const mobile = flags.get("mobile") === "true";
const width = Number(flags.get("width") ?? (mobile ? 390 : 1440));
const height = Number(flags.get("height") ?? (mobile ? 844 : 900));
const full = flags.get("full") === "true";
const langs = flags.get("lang")?.split(",").filter(Boolean) ?? [];
const clearStorage = flags.get("clear-storage") === "true";
const check = flags.get("check") === "true";

async function cdpUp(): Promise<boolean> {
  try {
    const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`);
    return r.ok;
  } catch {
    return false;
  }
}

if (!(await cdpUp())) {
  const proc = Bun.spawn(
    [
      BROWSER,
      `--user-data-dir=${PROFILE}`,
      `--remote-debugging-port=${CDP_PORT}`,
      "--headless=new",
      `--window-size=${width},${height}`,
      "about:blank",
    ],
    { stdout: "ignore", stderr: "ignore" },
  );
  proc.unref();
  // Wait for CDP to come up (up to 8s).
  const deadline = Date.now() + 8000;
  while (Date.now() < deadline) {
    if (await cdpUp()) break;
    await new Promise((r) => setTimeout(r, 200));
  }
  if (!(await cdpUp())) {
    console.error(`failed to start headless browser on port ${CDP_PORT}`);
    process.exit(1);
  }
}

// open a blank tab first, so viewport, language and storage are set before the page runs any script
const createRes = await fetch(`http://127.0.0.1:${CDP_PORT}/json/new?about:blank`, { method: "PUT" });
const tab = (await createRes.json()) as {
  id: string;
  webSocketDebuggerUrl: string;
};

const ws = new WebSocket(tab.webSocketDebuggerUrl);
let id = 0;
const pending = new Map<number, (v: any) => void>();
ws.onmessage = (ev) => {
  const m = JSON.parse(String(ev.data));
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)!(m);
    pending.delete(m.id);
  }
};
await new Promise<void>((r) => (ws.onopen = () => r()));
const send = (method: string, params: any = {}): Promise<any> => {
  const i = ++id;
  return new Promise((resolve) => {
    pending.set(i, resolve);
    ws.send(JSON.stringify({ id: i, method, params }));
  });
};

await send("Page.enable");
await send("Runtime.enable");
// some sites (x.com among them) answer 403 to a user agent that says HeadlessChrome
const version = await send("Browser.getVersion");
const userAgent = String(version.result?.userAgent ?? "").replace("HeadlessChrome", "Chrome");
if (userAgent) {
  await send("Network.setUserAgentOverride", { userAgent, acceptLanguage: langs.join(",") || undefined });
}
await send("Emulation.setDeviceMetricsOverride", {
  width,
  height,
  deviceScaleFactor: mobile ? 2 : 1,
  mobile,
});
if (mobile) {
  await send("Emulation.setTouchEmulationEnabled", { enabled: true, maxTouchPoints: 5 });
}

if (langs.length > 0) {
  await send("Emulation.setLocaleOverride", { locale: langs[0] });
  await send("Page.addScriptToEvaluateOnNewDocument", {
    source: `Object.defineProperty(navigator, "languages", { get: () => ${JSON.stringify(langs)} });
Object.defineProperty(navigator, "language", { get: () => ${JSON.stringify(langs[0])} });`,
  });
}

if (clearStorage) {
  // the profile is shared between runs, a saved choice from an earlier run would skew the result
  await send("Storage.clearDataForOrigin", { origin: new URL(url).origin, storageTypes: "local_storage,cookies,indexeddb" });
}

await send("Page.navigate", { url });
await new Promise((r) => setTimeout(r, waitMs));

const stepWait = Number(flags.get("step-wait") ?? 1500);
for (const action of actions) {
  let expression = action.value;
  if (action.kind === "click") {
    expression = `(() => { const el = document.querySelector(${JSON.stringify(action.value)}); if (!el) { return "not found: " + ${JSON.stringify(action.value)}; } el.click(); return "clicked"; })()`;
  } else if (action.kind === "type") {
    const sep = action.value.indexOf("=");
    const selector = action.value.slice(0, sep);
    const text = action.value.slice(sep + 1);
    expression = `(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) { return "not found: " + ${JSON.stringify(selector)}; } el.focus(); el.value = ${JSON.stringify(text)}; el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); return "typed"; })()`;
  }

  const res = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  const value = res.result?.result?.value ?? res.result?.exceptionDetails?.text;
  console.error(`${action.kind}: ${typeof value === "string" ? value : JSON.stringify(value)}`);
  await new Promise((r) => setTimeout(r, stepWait));
}

if (check) {
  const res = await send("Runtime.evaluate", {
    returnByValue: true,
    expression: `(() => {
      const header = document.querySelector("header");
      return {
        url: location.href,
        overflow: document.documentElement.scrollWidth > window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        headerHeight: header ? Math.round(header.getBoundingClientRect().height) : null,
      };
    })()`,
  });
  console.log(JSON.stringify(res.result.result.value));
}

const shot = await send("Page.captureScreenshot", {
  format: "png",
  captureBeyondViewport: full,
});
await Bun.write(out, Buffer.from(shot.result.data, "base64"));
console.log(out);

await fetch(`http://127.0.0.1:${CDP_PORT}/json/close/${tab.id}`);
ws.close();
