# noesis

An opinionated, keyboard-first TUI built on top of [herdr-core](https://github.com/herdrdev/herdr-core)
(`hc`): a neo-tree-style view of machines, groups, agents and threads, backed by one centralized memory repo.

Status: **spec only — no code yet.**

## Demo (mock)

A scripted mock of the tree view and main view, with made-up data and no real agents: `]a` jumps to the agent
that needs input, `Enter` opens its conversation, `f` forks a thread, and `u` rolls the finding up into memory.

https://github.com/user-attachments/assets/7b73dfc1-f74e-471a-ba88-7981e2c53d81

Video file: [`assets/noesis-mock-demo.mp4`](assets/noesis-mock-demo.mp4). Rebuild it with
`bash assets/make-demo.sh`; see [`assets/`](assets/).

## Docs

- [docs/spec.md](docs/spec.md) — what's decided
- [docs/open-questions.md](docs/open-questions.md) — where to resume
- [docs/references/](docs/references/) — pinned herdr-core docs/schema and distilled notes

## License

[Apache License 2.0](LICENSE). See [NOTICE](NOTICE).
