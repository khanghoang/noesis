# References

Source material behind [../spec.md](../spec.md). Copies are pinned to the versions noted so later changes upstream
don't silently change what the spec was based on.

## herdr 0.9.5 (socket API protocol 22)

Saved 2026-11-08 into [`herdr-v0.9.5/`](herdr-v0.9.5/). These are unmodified copies of
[herdrdev/herdr](https://github.com/herdrdev/herdr) material, © the herdr authors, licensed under
[Apache-2.0](https://github.com/herdrdev/herdr/blob/v0.9.5/LICENSE).

| File | Source | Why it matters |
|---|---|---|
| [`api-schema.json`](herdr-v0.9.5/api-schema.json) | `herdr api schema --output` (installed herdr 0.9.5) | Full JSON schema of every request, response and event |
| [`socket-api.mdx`](herdr-v0.9.5/socket-api.mdx) | [herdrdev/herdr@v0.9.5 docs/…/socket-api.mdx](https://github.com/herdrdev/herdr/blob/v0.9.5/docs/next/website/src/content/docs/socket-api.mdx) | Wire format, `events.subscribe`, `session.snapshot`, recovery after `events_lost`, protocol stability |
| [`connecting-machines.mdx`](herdr-v0.9.5/connecting-machines.mdx) | [same tree, connecting-machines.mdx](https://github.com/herdrdev/herdr/blob/v0.9.5/docs/next/website/src/content/docs/connecting-machines.mdx) | `herdr machine add`, reconnect behaviour, SSH auth, agent forwarding |
| [`cli-reference.mdx`](herdr-v0.9.5/cli-reference.mdx) | [same tree, cli-reference.mdx](https://github.com/herdrdev/herdr/blob/v0.9.5/docs/next/website/src/content/docs/cli-reference.mdx) | `--machine` forwarding and its limits (section "Saved SSH machines") |
| [`persistence-remote.mdx`](herdr-v0.9.5/persistence-remote.mdx) | [same tree, persistence-remote.mdx](https://github.com/herdrdev/herdr/blob/v0.9.5/docs/next/website/src/content/docs/persistence-remote.mdx) | `herdr --remote` setup over SSH |

Other upstream entry points: <https://herdr.dev/llms.txt> (docs index), <https://herdr.dev/llms-full.txt>
(complete bundle).

See [herdr-notes.md](herdr-notes.md) for the facts noesis relies on, distilled.

## Not yet captured

- **Eternal Terminal (ET)** docs: port forwarding, unix-socket forwarding, session lifetime. ET isn't
  installed on this VM; everything the spec says about ET is from general knowledge and still unverified
  (open question 12).
