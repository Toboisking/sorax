<p align="center">
  <a href="https://github.com/Toboisking/sorax">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="packages/console/app/src/asset/brand/sorax-wordmark-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="packages/console/app/src/asset/brand/sorax-wordmark-light.svg">
      <img src="packages/console/app/src/asset/brand/sorax-wordmark-light.svg" alt="SORAX" width="420">
    </picture>
  </a>
</p>

<h1 align="center">SORAX</h1>

<p align="center">
  The open source AI coding agent — forked, hardened and extended.
</p>

<p align="center">
  <a href="https://github.com/Toboisking/sorax/actions"><img alt="Build status" src="https://github.com/Toboisking/sorax/actions/workflows/publish.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <a href="https://t.me/Ghostofhackers"><img alt="Telegram" src="https://img.shields.io/badge/Telegram-%40Ghostofhackers-26A5E4?logo=telegram&logoColor=white"></a>
</p>

---

## Overview

SORAX is a full-featured AI coding agent you can run locally — terminal CLI, background
service and a built-in web UI, rebuilt and extended with model routing, agent packs,
MCP integration and automatic content-filter failover.

**Owner:** [@Ghostofhackers](https://t.me/Ghostofhackers) — Telegram: [t.me/Ghostofhackers](https://t.me/Ghostofhackers)

## Features

- **CLI + Web UI + Service** — one binary runs everything; headless service with a
  browser-based session UI on `http://127.0.0.1:28994`.
- **Model routing** — per-task model selection (plan / build / review / deploy / hack)
  configured in one place.
- **Agent packs** — ready-made agent profiles (build, review, deploy, osint, hacker…)
  with their own prompts and tool policies.
- **MCP servers** — plug in any Model Context Protocol server (playwright, sqlite, …)
  straight from config.
- **Automatic content-filter failover** — when a provider blocks a response,
  SORAX automatically retries on a configured fallback model (once per step) and
  keeps the session running instead of dying:

  ```jsonc
  // ~/.config/sorax/sorax.json
  "model_fallback": {
    "venice/claude-opus-5": "venice/deepseek-v4-pro"
  }
  ```

- **Runtime-loaded config** — agents, packs, models and MCP changes apply live,
  no rebuild needed.

## Quick start

### Prerequisites

- [Bun](https://bun.sh) ≥ 1.4

### Run from source

```bash
git clone https://github.com/Toboisking/sorax.git
cd sorax
bun install
bun run dev
```

### Build the production binary

```bash
cd packages/cli
SORAX_CHANNEL=latest SORAX_VERSION=2.1.4 bun run build
# → dist/cli-windows-x64/bin/sorax.exe  (all platform targets produced)
```

### Run the service + web UI

```bash
sorax service start     # → http://127.0.0.1:28994
sorax service status
sorax service stop
```

Add `sorax service start` to your OS startup (Startup folder / systemd unit) for
auto-start on boot.

## Configuration

Config lives at `~/.config/sorax/sorax.json` (Windows: `C:\Users\<you>\.config\sorax\sorax.json`).

```jsonc
{
  "provider": {
    "venice": { "options": { "apiKey": "YOUR_KEY" } }
  },
  "model_fallback": {
    "venice/claude-opus-5": "venice/deepseek-v4-pro"   // content-filter failover
  },
  "mcp": {
    "servers": {
      "playwright": { "type": "local", "command": ["npx", "@playwright/mcp@latest"], "enabled": true }
    }
  }
}
```

Key points:

| Section       | Purpose                                                        |
| ------------- | -------------------------------------------------------------- |
| `provider`    | API keys / endpoints for model providers                       |
| `model`       | default model                                                  |
| `model_fallback` | failover map used when a provider returns a content filter  |
| `mcp.servers` | Model Context Protocol servers, loaded at runtime              |

## Updates

SORAX uses **GitHub Releases as its update feed** — no external update server.

**For users** — the installed binary updates itself:

```bash
sorax upgrade            # checks the latest release, downloads, replaces in place
```

Release assets are named per platform: `sorax-windows-x64.exe`, `sorax-darwin-arm64`,
`sorax-linux-x64`, … The CLI detects a portable install automatically and swaps the
binary (on Windows the running image is unlinked safely before replacement; restart
`sorax service` afterwards to run the new version).

**For the maintainer** — shipping an update takes one tag:

```bash
git tag v2.1.5
git push origin v2.1.5
```

CI (`.github/workflows/release.yml`) builds every platform target, packages the
binaries as release assets and publishes the GitHub release. Users get it through
`sorax upgrade`. Update checks follow the `update` policy in config
(`"disable"` | `"notify"` | `"auto"`).

## Headless pipeline review

```bash
pipeline-review.cmd C:\path\to\project
```

Runs a read-only, prioritized code review (severity · file:line · concrete fix)
against a directory using the `review` agent.

## Development

```bash
bun run check        # root gate: typecheck + lint + tests (34 tasks)
bun typecheck        # package-level typecheck (never run bare tsc)
```

Repo rules live in [AGENTS.md](AGENTS.md).

> **Note:** after editing core source under `packages/core`, restart the managed
> service before testing — a stale background service keeps running the old code.

## Project layout

```
packages/
  cli/        CLI entry, service, build targets
  core/       agent runtime, session runner, LLM pipeline
  schema/     config schema
  ui/         web UI
  console/    console app + assets
```

## License

[MIT](LICENSE) — © 2026 SORAX contributors. See `LICENSE` for upstream attribution.

## Owner

Built and maintained by **[@Ghostofhackers](https://t.me/Ghostofhackers)**

- Telegram: [https://t.me/Ghostofhackers](https://t.me/Ghostofhackers)
