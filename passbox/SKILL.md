---
name: passbox
description: Read secrets from passbox, inject them into a child process, and stop Touch ID prompts in an unattended job using injection at launch or a scoped grant token. Use when a script, daemon or agent needs a credential, when repeated fingerprint prompts are blocking something long-running, or when working on the passbox store itself.
---

# passbox

An agentic password manager. An agent asks for a secret, macOS raises a Touch ID
prompt naming the agent and the secret, and the value goes into one child process
rather than into the agent.

Store lives at `~/.passbox` (`PASSBOX_DIR` overrides). Every secret is one age file
with a random id; the name and policy are inside the ciphertext.

## Install

If `passbox` is not on `PATH`, install it before anything else:

```bash
brew install gabrielkoerich/tap/passbox
passbox init
```

Homebrew downloads a prebuilt binary, so Rust is not needed. If recent Homebrew stops and asks you to trust the tap, run `brew trust --formula gabrielkoerich/tap/passbox` and try again. Without Homebrew, `cargo install passbox` builds it from crates.io (needs Rust and the Command Line Tools).

`passbox init` binds the store to this Mac's Secure Enclave, with no passphrase. The store then opens on this Mac only, so losing the Mac loses the secrets unless sync is turned on. Linux and sync are covered in the [README](https://github.com/gabrielkoerich/passbox#install).

## Reading a secret

```bash
passbox get github/token                    # prints it, interactive use
passbox ls                                  # tree of names, needs a prompt
```

**Prefer injection over reading.** The value goes broker to child and never through
the caller, so a traceback or a crash dump cannot carry it.

```bash
passbox exec --env GITHUB_TOKEN=github/token -- gh api /user
passbox exec --stdin db/password -- psql
```

`--stdin` is the safer of the two: any process running as you can read a child's
environment with `ps eww`.

## Unattended: inject at launch

**The first thing to reach for when a daemon runs 24/7.** A token expires, and renewing one
needs a human at the sensor. Injecting does not.

```bash
passbox exec --env EXCHANGE_API_KEY=trading/exchange-api-key -- python -m your.daemon
```

One approval at launch. The value lands in the process environment and every child inherits
it, so nothing reads passbox again for the life of that process. A daemon runs for weeks on
one fingerprint and needs you only when you restart it.

This works because a credential layer should check environment variables before any provider.
If yours does, injecting needs no code change at all: the reads simply stop reaching passbox.

Cost: the value sits in the process environment for its lifetime, and any process running as
you can read it with `ps eww`. That is the price of unattended. Use `--stdin` instead where
the child accepts a secret on stdin.

Limit: an env var name has to be a valid identifier, so a secret whose name contains a hyphen
in the variable (`MY-SERVICE_API_KEY`) cannot be injected. Cover those with a
token, and cache them in-process so it is one read per start.

## Grants and tokens

A **grant** is one approval that mints a **token**: a bearer string that opens exactly the
secrets it was granted, for whoever holds it, until it lapses. Capped at 24 hours.

```bash
export PASSBOX_TOKEN=$(passbox grant trading/exchange-api-key trading/exchange-secret --for 3600)
passbox get trading/exchange-api-key  # no prompt, audited as `by token`
```

The token goes to stdout and the covered names to stderr, so `$(...)` captures the token alone.

**A namespace is refused.** `grant trading` would hand over everything under it to save one
prompt, and it scopes on how the store is laid out rather than on what the job reads. Put
everything at the root and a namespace rule protects nothing. The refusal lists the names so
you can copy the ones you want, and costs no fingerprint: it is checked locally against the
name index before the broker is involved.

Revoke by restarting the broker, which tears up every outstanding token:

```bash
pkill -f "passbox broker"
```

### There are no long-lived tokens, and that is deliberate

24 hours is the ceiling and it cannot be raised from the command line. A token that never
lapses is a password with extra steps, and the point of a token is that it stops.

So a token is the wrong tool for something that must run untended indefinitely. That is what
injection above is for. Reach for a token when a process needs several secrets over a bounded
run, or when the value must not sit in an environment where `ps eww` finds it.

### Mint once per process, not per call

The trap that will bite you. A token caches on the provider instance, so a factory that builds
a fresh provider on every call mints a fresh grant every call, and each one is a fingerprint.

```python
@lru_cache(maxsize=1)
def manager() -> CredentialManager: ...
```

Symptom: repeated prompts for the same secret in a loop or per request. Check the audit log:
repeated `approved` for one secret and one agent means the provider is being rebuilt.

### A failed grant must never stop the job

Minting is an optimisation. If it fails, fall back to prompting or to whatever the job did
before; never let it abort the start. A cancelled Touch ID prompt taking down a daemon is
worse than the prompts it was avoiding.

## Modes

Set inside the encrypted file, never in a plaintext policy file.

| Mode | Behaviour |
|---|---|
| `open` | No prompt |
| `window` | One prompt per agent and secret per window. Default |
| `always` | A prompt on every read |
| `never` | Agents never get it, interactive `get` only |

```bash
passbox mode api/key window --window 3600
```

`open` does **not** give unattended operation on its own. The mode lives inside the
encrypted file, so the broker needs the store key to read it, and a cold broker still
prompts. Inject at launch, or mint a token.

## Fields in one entry

The first line is the secret, later `key: value` lines are fields. This is the `pass`
layout, which `import-pass` keeps.

```bash
passbox get db/prod                   # the whole thing
passbox get db/prod --field username  # just that one
```

Use `--field` when handing a value to something that needs only the password: it
leaves the note and the username behind. `examples/python/passbox.py` in the repo
parses the same layout.

## Listing names

`ls` reads `~/.passbox/names`, a plaintext list kept in step as the store changes, so
it needs no key and raises no prompt. `get` still does.

That file names what you hold, and it is local only: sync skips it, a git store
ignores it, it is `0600`. A sync that pulls deletes it, since a pull can bring names
this machine has never decrypted, and the next `ls` rebuilds it with one prompt.

Still do not use `ls` as a health check. Check the binary and that `~/.passbox/wraps`
exists instead.

## Reading from another machine

A Linux box with no Enclave can ask a Mac. The client holds no store and no key.

```bash
echo "100.x.y.z" > ~/.passbox/host    # the Mac's tailnet address
passbox get github/token              # prompt appears on the Mac
```

Three things have to be true on the Mac, and each fails silently in its own way:

**The broker must be a LaunchAgent** in the login session. One started by an incoming
connection blocks inside `evaluatePolicy` forever rather than prompting.

**Give that LaunchAgent a PATH.** It gets a minimal one, `tailscale` is not on it, and the
broker starts with no tailnet listener and says nothing.

**Expose it with `tailscale serve`, not by binding the tailnet address.** macOS runs Tailscale
as a network extension; a socket bound to the 100.x address accepts the connection and then
fails the first read with `ENOTCONN`.

```bash
tailscale serve --bg --tcp 8787 tcp://127.0.0.1:8787
```

In a container, give tailscaled a real `/dev/net/tun`. Userspace networking reaches the tailnet
only through a SOCKS proxy, so `connect()` to a 100.x address times out with no hint why.

The caller is not identified: traffic through `serve` has a loopback peer, so `whois` resolves
nothing and the prompt says `an unidentified tailnet peer`.

## Gotchas

**An upgrade leaves a stale broker.** `brew upgrade passbox` does not restart the running
broker, so the old one keeps serving the old protocol. The symptom is a parse error naming a
command the new binary has and the old one does not, such as `unknown variant \`grant\``.
Restart it: `pkill -f "passbox broker"`.

**GPG steals the smart card.** If a YubiKey wrap is involved, `gpg-agent`'s `scdaemon`
opens the card exclusively and breaks `age-plugin-yubikey` mid-operation with a
misleading `authentication error`. Stop it first: `gpgconf --kill scdaemon`. Anything
calling `pass` restarts it.

**Touch ID needs a real session.** A process spawned over SSH, or by an agent's shell,
often cannot raise the prompt and will hang. Run those from a terminal.

**Backups.** `init` binds the store to one Mac's Secure Enclave and writes no other
wrap, so a Time Machine restore onto a wiped Mac opens nothing. `passbox sync --enable`
adds a passphrase or YubiKey wrap and a copy elsewhere. Check `~/.passbox/wraps/` holds
more than `recipient` and `se-<host>.json`.
