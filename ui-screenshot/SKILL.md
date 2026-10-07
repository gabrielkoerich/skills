---
name: ui-screenshot
description: Capture a PNG screenshot of any URL with a headless Chromium-family browser over CDP (Brave preferred, no Playwright needed), with phone viewports, browser language lists and a layout check. Use it whenever the user asks you to look at, check or visually verify a page or a frontend change, test it on mobile, or test a language redirect. Output PNG goes to /tmp/ui-shot.png by default; read it back with the Read tool.
---

# UI Screenshot

Takes a screenshot of any URL with a headless browser driven over the Chrome DevTools Protocol. It uses the first installed Chromium-family browser in this order: `$BROWSER_BIN`, Brave, Chromium, Google Chrome, Microsoft Edge, Vivaldi (macOS app bundles first, then binaries on `PATH` for Linux). It prints the browser it picked on stderr. If none is installed it exits with an error that lists every place it looked.

## Usage

```bash
bun ~/.claude/skills/ui-screenshot/shot.ts <url> [out.png] [--wait=3500] [--width=1440] [--height=900] [--full] [--mobile] [--lang=pt-BR,en-US] [--clear-storage] [--check]
```

Defaults: `out=/tmp/ui-shot.png`, `wait=3500ms`, `1440x900`, viewport only.

| Flag | What it does |
|---|---|
| `--full` | Capture the full scrollable page |
| `--mobile` | Phone viewport (390x844, scale 2, touch) unless `--width` or `--height` is given |
| `--lang=pt-BR,en-US` | Set `navigator.languages` and the locale before the page loads, to test language redirects |
| `--clear-storage` | Clear localStorage, cookies and IndexedDB for the URL's origin first. The profile is shared between runs, so use it for any redirect or first-visit test |
| `--click=<selector>` | Click the first element matching the CSS selector. Prints `clicked` or `not found` on stderr |
| `--type=<selector>=<text>` | Set the value of an input and fire `input` and `change` events |
| `--eval=<js>` | Run JavaScript in the page and print the result on stderr (for example `--eval='document.title'`) |
| `--step-wait=1500` | Milliseconds to wait after each click, type or eval, so a navigation can finish |
| `--check` | Print JSON with the final URL after redirects, horizontal overflow, scroll width and header height |

`--click`, `--type` and `--eval` can repeat and run in the order given, after the page loads. Example, clicking a language switch and checking where it lands:

```bash
bun ~/.claude/skills/ui-screenshot/shot.ts http://127.0.0.1:1111/ /tmp/switch.png --clear-storage --click='a[hreflang="pt"]' --check
```

The user agent is sent without `HeadlessChrome`, because some sites (x.com among them) answer 403 to a headless browser. Pages behind a login still need that login in the automation profile.

Example: a Portuguese phone browser should land on `/pt/` without sideways scrolling.

```bash
bun ~/.claude/skills/ui-screenshot/shot.ts http://127.0.0.1:1111/ /tmp/pt-mobile.png --mobile --lang=pt-BR --clear-storage --check
```

The script starts the headless browser on CDP port `18801` if nothing is listening there, with the profile at `~/.claude/browser/Default/user-data`.

## Read the result

After the script writes the PNG, view it with the Read tool, which renders it as an image.

## Notes

- The headless browser must be separate from any interactive window of the same browser, because the profile directory is locked. The script uses `~/.claude/browser/Default/user-data` as a dedicated automation profile.
- For a UI behind a login, log in once in that profile with a visible run, then close it. Headless runs reuse the cookies.
- The CDP port is fixed (`18801`) so several skills can share one browser instance.
- Override the detection with `BROWSER_BIN=/path/to/binary`.
