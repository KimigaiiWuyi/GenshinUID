# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Despite the name, the `v4-nonebot2` branch is **not** the GenshinUID bot itself — it is a thin
**connector plugin** (`nonebot-plugin-genshinuid`) that bridges a NoneBot2 instance to a separate
server called **gsuid_core** (a.k.a. SayuCore). All actual feature/command logic lives in
gsuid_core plugins, *not here*. This repo only does two things:

1. Receives platform events from NoneBot2 adapters, normalizes them into a unified protocol, and
   forwards them to gsuid_core over a WebSocket.
2. Receives unified outgoing messages from gsuid_core and dispatches them to the correct platform
   adapter to actually send.

So when a user reports a "command doesn't work" or "feature X is broken," the fix usually belongs in
gsuid_core, not in this repo. This repo is the right place only for **protocol translation** bugs
(an event/segment not converted correctly, or a platform send path failing).

gsuid_core is expected to live at a sibling directory `../gsuid_core` (see `GenshinUID/path.py`),
or wherever `gsuid_core_path` config points.

## Commands

This project uses **PEP 621 `pyproject.toml`** and **pre-commit**. There is no application
entrypoint here — the code runs as a plugin inside a host NoneBot2 bot.

- Install (editable): `pip install -e .`
- Install with lint tools: `pip install -e ".[dev]"`
- Build distributables: `python -m build` (outputs to `dist/`)
- Lint + format everything: `pre-commit run --all-files`
- Format only (matches CI / gsuid_core): `ruff check --fix .` then `ruff format .`

Formatting is strict: **ruff** with `ruff.toml` aligned to gsuid_core (`line-length = 120`,
select `E,F,I,W`, isort `length_sort`). `pyproject.toml` configures pytest
(`asyncio_mode = "auto"`), but there is currently **no test suite** in this branch.

## Architecture

Four conceptual layers, mapped to files:

- **Plugin entrypoint** — root `__init__.py` calls `load_plugins(...)` to load the `GenshinUID/`
  subpackage as the actual NoneBot2 plugin.
- **Event ingestion** — `GenshinUID/__init__.py`. Registers matchers (`on_message`, `on_notice`,
  `on('inline')`, and a `连接core` fullmatch command). `get_all_message` / `get_notice_message` are
  giant `if bot.adapter.get_name() == ...` dispatchers that translate each platform's event into the
  unified `MessageReceive`, then push it to the client queue via `gsclient._input(...)`.
- **WebSocket client** — `GenshinUID/client.py`. `GsClient` is a **singleton** (`__new__` returns
  `_instance`). `recv_msg` decodes incoming `MessageSend` from core and routes by `msg.bot_id` to a
  per-platform `*_send` coroutine (`onebot_send`, `guild_send`, `telegram_send`, `discord_send`,
  etc.). `send_msg` drains the queue and ships `MessageReceive` to core. Includes auto-reconnect on
  `ConnectionClosedError`.
- **Wire protocol** — `GenshinUID/models.py`. `msgspec.Struct` types (`Message`, `MessageReceive`,
  `MessageSend`) define the JSON contract with gsuid_core. These must stay in sync with gsuid_core's
  copies of the same structs.

### The unified `Message` protocol

Every message is a list of `Message(type, data)` segments. Common `type` values: `text`, `image`,
`file`, `at`, `reply` (quoted text, ingest), `reply_id` (quoted message id), `node` (forward msg),
`record` (audio), `video`, `markdown`, `buttons`, `group`. Quoted images are always forwarded to
core as extra `image` segments. On the send path, both `reply` and `reply_id` become a quote
(core still uses `reply` as a message id). Media `data` is a string carrying a scheme prefix:

- `base64://<...>` — raw bytes, base64-encoded (preferred for uploads).
- `link://<url>` — a remote URL to fetch/forward.
- `file` segments are encoded as `"<filename>|<base64>"` (split on `|`).

Helpers `get_bytes_from_base64_str`, `store_file`/`del_file`, and `convert_file` handle these.

### `bot_id` is the routing key

`bot_id` identifies the platform on both directions. On ingest it is usually derived from the
adapter package name: `ev.__class__.__module__.split('.')[2]`, but many platforms override it with
`sp_bot_id` (e.g. `qqguild`, `qqgroup`, `onebot:red`, `onebot_v12`). On send, `recv_msg` switches on
`msg.bot_id` to pick the `*_send` function, and `_get_bot`/`_refresh_bots` map a `bot_id` back to a
live NoneBot `Bot` instance.

### Adding / fixing a platform

A platform touches **three** places, all keyed off the adapter name / `bot_id`:

1. An ingest branch in `get_all_message` (and `get_notice_message` if it has button/notice events).
2. A `*_send` coroutine in `client.py`.
3. A dispatch branch in `GsClient.recv_msg`.

**Critical convention:** adapter imports (`from nonebot.adapters.qq... import ...`) are done
**lazily inside** the per-platform branch/function, never at module top level. Adapters are optional
dependencies; a top-level import would crash hosts that don't have that adapter installed. Always
follow this pattern.

### Configuration

All config is read from NoneBot `PluginConfig` (`GenshinUID/config.py`). Keys: `gsuid_core_host`
(default `localhost`), `gsuid_core_port` (`8765`), `gsuid_core_ws_token`, `gsuid_core_botid`,
`gsuid_core_repeat` (enables a 10s reconnect cron), `gsuid_core_path`. `gsuid_core_reply_img` is
kept for host-config compatibility but no longer gates quoted-image upload. The WS URL is
`ws://{host}:{port}/ws/{BOT_ID}[?token=...]`.

### Permission levels (`user_pm`)

Sent to core as an int: `1` = SUPERUSER, `2` = group owner, `3` = group admin, `5`/`6` = lower /
normal member. Platform-specific role mapping happens in the ingest branches.

## Conventions

- Code comments and log strings are in **Chinese**; match this when editing.
- Commits use **gitmoji**-style prefixes (`🎨`, `✨`, `🔖`, `⬆️`), as seen in history.
- pre-commit CI auto-fixes formatting on PRs and targets the `v4-nonebot2` branch.
