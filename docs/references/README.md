# References

Source material behind [../spec.md](../spec.md). Copies are pinned to the versions noted so later changes upstream
don't silently change what the spec was based on.

## herdr-core v0.1.18 (API protocol generation 1)

Saved 2026-11-08 into [`herdr-core-v0.1.18/`](herdr-core-v0.1.18/). These are unmodified copies of
[herdrdev/herdr-core](https://github.com/herdrdev/herdr-core) material at tag `v0.1.18`, © the herdr-core
authors, licensed under [Apache-2.0](https://github.com/herdrdev/herdr-core/blob/v0.1.18/LICENSE).
Paths are flattened (`schema/README.md` → `schema_README.md`).

| File | Upstream path | Why it matters |
|---|---|---|
| [`README.md`](herdr-core-v0.1.18/README.md) | `README.md` | What hc is: terminals, agents running agents, machines, status, building a client |
| [`schema_README.md`](herdr-core-v0.1.18/schema_README.md) | `schema/README.md` | Connecting, plain vs framed mode, attach streams, events, documents, status |
| [`schema_hc.openrpc.json`](herdr-core-v0.1.18/schema_hc.openrpc.json) | `schema/hc.openrpc.json` | Every method, param and result as OpenRPC + JSON Schema |
| [`machines.md`](herdr-core-v0.1.18/machines.md) | `docs/machines.md` | `hc machine add`, `--via` custom connections, what runs where, reconnecting |
| [`commands.md`](herdr-core-v0.1.18/commands.md) | `docs/commands.md` | Full CLI reference (`run`, `label`, `wait`, `events`, …) |
| [`templates.md`](herdr-core-v0.1.18/templates.md) | `docs/templates.md` | Agent templates (command + role) |
| [`security.md`](herdr-core-v0.1.18/security.md) | `docs/security.md` | Access, state, endpoints, updates |

See [herdr-core-notes.md](herdr-core-notes.md) for the facts noesis relies on, distilled.

The first draft of the spec was based on the herdr **app** (0.9.5) socket API by mistake; those references
were removed after the PR #1 review and are still in this branch's first commit if ever needed.

## Not yet captured

- **Eternal Terminal (ET)** docs: whether it can carry a plain byte stream without a PTY, port forwarding,
  session lifetime. ET isn't installed on this VM; the ET parts of the spec are unverified (open question 16).
