#!/usr/bin/env python3
"""Scripted mock of the noesis TUI, for recording with asciinema.

Nothing here talks to herdr-core: the tree, the agents and the conversations are
made up. It plays a fixed script (keys are shown in the bottom-right corner) to
illustrate the tree view (spec §3), the main view, fork (§6.2) and roll-up (§6.4).

    asciinema rec -c 'python3 docs/demos/mock_noesis.py' demo.cast   # 120x34 terminal
"""

import sys
import time

COLS, ROWS = 120, 34
LEFT = 46                      # tree pane width, borders included
RIGHT = COLS - LEFT            # main view width, borders included
BODY = ROWS - 5                # rows between the pane borders

# ── styling ────────────────────────────────────────────────────────────────
ESC = "\x1b["
RESET = ESC + "0m"
def sgr(*codes): return ESC + ";".join(str(c) for c in codes) + "m"
BOLD, DIM, REV = sgr(1), sgr(2), sgr(7)
FG = {"red": sgr(31), "green": sgr(32), "yellow": sgr(33), "blue": sgr(34),
      "magenta": sgr(35), "cyan": sgr(36), "white": sgr(37), "grey": sgr(90)}
CURSOR_BG = sgr(48, 5, 238)
HEADER_BG = sgr(48, 5, 24) + sgr(97)

GLYPH = {"blocked": ("⚠", "yellow"), "working": ("●", "green"), "idle": ("○", "grey"),
         "offline": ("✕", "red"), "rolled": ("✓", "cyan")}
WORD = {"blocked": "needs input", "working": "working", "idle": "idle",
        "offline": "offline", "rolled": "→ knowledge"}
RANK = {"blocked": 3, "working": 2, "idle": 1, "rolled": 0}


class Seg(list):
    """A line built from (text, style) pieces so width can be measured exactly."""

    def add(self, text, style=""):
        self.append((text, style))
        return self

    def width(self):
        return sum(len(t) for t, _ in self)

    def render(self, width, base=""):
        out, used = [], 0
        for text, style in self:
            room = width - used
            if room <= 0:
                break
            text = text[:room]
            used += len(text)
            out.append(base + style + text + RESET)
        out.append(base + " " * (width - used) + RESET)
        return "".join(out)


# ── model ──────────────────────────────────────────────────────────────────
def node(label, kind, status=None, children=None, open_=False, agent=None, machine=None):
    return {"label": label, "kind": kind, "status": status, "children": children or [],
            "open": open_, "agent": agent, "machine": machine, "convo": []}


push = node("push-alerts", "agent", "working", agent="claude")
flow = node("checkout-flow", "agent", "blocked", agent="claude")
ops = node("ops", "group", children=[node("deploy-check", "agent", "working", agent="claude"),
                                     node("log-triage", "agent", "working", agent="codex")])
checkout = node("checkout", "group", children=[push, flow], open_=True)
roots = [
    node("storefront", "group", children=[checkout, ops], open_=True, machine="cws"),
    node("(ungrouped)", "group", children=[node("scratch", "agent", "idle", agent="claude")],
         machine="cws"),
    node("home-dash", "group", children=[node("weather-sync", "agent", "working", agent="claude")],
         machine="pi"),
    node("dotfiles", "group", children=[node("nvim-tuning", "agent", "idle", agent="claude")],
         machine="mac", status="offline"),
]

flow["convo"] = [
    ("you", "Totals in the cart summary are off by a cent on some orders."),
    ("tool", "read src/cart/total.ts"),
    ("tool", "read src/cart/tax.ts"),
    ("claude", "Line items and order totals round in different places."),
    ("claude", "Before I change anything: should totals round per line or per order?"),
]


def rollup_status(n):
    if n["status"] == "offline":
        return "offline"
    if n["kind"] != "group" and not n["children"]:
        return n["status"]
    states = [rollup_status(c) for c in n["children"]]
    if n["kind"] != "group":
        states.append(n["status"])
    live = [s for s in states if s in RANK]
    return max(live, key=RANK.get) if live else "idle"


def counts(n):
    found = {}
    def walk(x):
        for c in x["children"]:
            if c["kind"] != "group" and c["status"] in ("working", "blocked", "idle"):
                found[c["status"]] = found.get(c["status"], 0) + 1
            walk(c)
    walk(n)
    return found


def visible():
    rows = []
    def walk(n, depth):
        rows.append((n, depth))
        if n["open"]:
            for c in n["children"]:
                walk(c, depth + 1)
    for r in roots:
        walk(r, 0)
    return rows


# ── view state ─────────────────────────────────────────────────────────────
state = {"cursor": 0, "focus": "tree", "opened": None, "caption": "", "key": "",
         "status": "", "input": "", "prompt": ""}


def tree_line(n, depth, selected):
    s = Seg().add(" " + "  " * depth)
    if n["children"]:
        s.add("▾ " if n["open"] else "▸ ", FG["grey"])
    else:
        s.add("└ " if n["kind"] == "thread" else "  ", FG["grey"])
    st = rollup_status(n)
    glyph, colour = GLYPH[st]
    s.add(glyph + " ", FG[colour])
    if n["machine"]:
        s.add("@" + n["machine"] + " ", FG["cyan"] + BOLD)
        s.add(n["label"], BOLD)
    elif n["kind"] == "group":
        s.add(n["label"], BOLD)
    else:
        if n["agent"] and n["kind"] == "agent":   # a thread runs its parent's agent
            s.add(n["agent"] + "  ", FG["grey"])
        s.add(n["label"], DIM if st == "rolled" else "")
    # right-hand detail
    if n["kind"] == "group" and not n["open"] and st != "offline":
        c = counts(n)
        detail = " ".join(f"{v} {GLYPH[k][0]}" for k, v in sorted(c.items(), key=lambda kv: -RANK[kv[0]]))
        detail = f"({detail})" if detail else ""
    elif n["kind"] == "group":
        detail = "offline" if st == "offline" else ""
    else:
        detail = WORD[st]
    gap = (LEFT - 2) - 1 - s.width() - len(detail)
    s.add(" " * max(gap, 1)).add(detail, FG[GLYPH[st][1]] if detail else "")
    return s, selected


def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines or [""]


def main_lines(n):
    inner = RIGHT - 4
    if n is None:
        return [Seg(), Seg().add("  Select an agent and press Enter to open its conversation.", FG["grey"])]
    out = []
    for role, text in n["convo"]:
        if role == "tool":
            out.append(Seg().add("    └ " + text, FG["grey"]))
            continue
        if role == "note":
            label, colour = "noesis ›", "cyan"
        elif role == "you":
            label, colour = "you ›", "blue"
        else:
            label, colour = (n["agent"] or "agent") + " ›", "magenta"
        lines = wrap(text, inner - len(label) - 1)
        out.append(Seg().add(" " + label + " ", FG[colour] + BOLD).add(lines[0]))
        for more in lines[1:]:
            out.append(Seg().add(" " * (len(label) + 2) + more))
        out.append(Seg())
    return out


def border(title, width, active):
    colour = FG["cyan"] if active else FG["grey"]
    title = f" {title} "
    return colour + "┌─" + RESET + BOLD + title + RESET + colour + "─" * (width - 3 - len(title)) + "┐" + RESET


def draw():
    rows = visible()
    out = [ESC + "H"]
    # header
    head = Seg().add(" noesis ", BOLD).add(" │ ").add("@cws ", BOLD).add("● online  ", FG["green"]) \
        .add("@pi ", BOLD).add("● online  ", FG["green"]).add("@mac ", BOLD).add("✕ offline", FG["red"])
    out.append(head.render(COLS, HEADER_BG) + "\r\n")
    opened = state["opened"]
    title = "main view" + (f" · {opened['agent']} {opened['label']}" if opened else "")
    out.append(border("tree", LEFT, state["focus"] == "tree") +
               border(title, RIGHT, state["focus"] == "main") + "\r\n")
    body = main_lines(opened)
    # keep the newest conversation lines in view, leaving room for the input box
    room = BODY - 3
    body = body[-room:] if len(body) > room else body
    for i in range(BODY):
        lc = FG["cyan"] if state["focus"] == "tree" else FG["grey"]
        rc = FG["cyan"] if state["focus"] == "main" else FG["grey"]
        if i < len(rows):
            seg, _ = tree_line(*rows[i], selected=(i == state["cursor"]))
            base = CURSOR_BG if i == state["cursor"] else ""
            left = seg.render(LEFT - 2, base)
        else:
            left = " " * (LEFT - 2)
        if i < len(body):
            right = body[i].render(RIGHT - 2)
        elif i == BODY - 2 and opened:
            right = (FG["grey"] + " " + "─" * (RIGHT - 4) + " " + RESET)
        elif i == BODY - 1 and opened:
            caret = "█" if state["focus"] == "main" else ""
            right = Seg().add(" › ", FG["blue"] + BOLD).add(state["input"]).add(caret, FG["grey"]).render(RIGHT - 2)
        else:
            right = " " * (RIGHT - 2)
        out.append(lc + "│" + RESET + left + lc + "│" + RESET + rc + "│" + RESET + right + rc + "│" + RESET + "\r\n")
    lc = FG["cyan"] if state["focus"] == "tree" else FG["grey"]
    rc = FG["cyan"] if state["focus"] == "main" else FG["grey"]
    out.append(lc + "└" + "─" * (LEFT - 2) + "┘" + RESET + rc + "└" + "─" * (RIGHT - 2) + "┘" + RESET + "\r\n")
    # status line (roll-up progress, prompts)
    if state["prompt"]:
        status = Seg().add(" " + state["prompt"], FG["yellow"] + BOLD).add(state["input"]).add("█", FG["grey"])
    else:
        status = Seg().add(" " + state["status"], FG["cyan"])
    out.append(status.render(COLS) + "\r\n")
    # caption + key indicator
    key = f" key › {state['key']} " if state["key"] else ""
    cap = Seg().add(" " + state["caption"], BOLD + FG["white"])
    pad = COLS - cap.width() - len(key)
    cap.add(" " * max(pad, 0)).add(key, REV + BOLD if key else "")
    out.append(cap.render(COLS))
    sys.stdout.write("".join(out))
    sys.stdout.flush()


# ── script helpers ─────────────────────────────────────────────────────────
def wait(s):
    time.sleep(s)


def press(key, then=None, pause=0.55):
    state["key"] = key
    if then:
        then()
    draw()
    wait(pause)


def caption(text, pause=0.0):
    state["caption"] = text
    draw()
    wait(pause)


def move(delta):
    def go():
        state["cursor"] = max(0, min(len(visible()) - 1, state["cursor"] + delta))
    return go


def current():
    return visible()[state["cursor"]][0]


def type_into(field_text, per_char=0.045):
    for ch in field_text:
        state["input"] += ch
        state["key"] = ch if ch != " " else "␣"
        draw()
        wait(per_char)


def stream(n, role, text, pause=0.9):
    n["convo"].append((role, text))
    draw()
    wait(pause)


# ── the demo ───────────────────────────────────────────────────────────────
def demo():
    sys.stdout.write(ESC + "?1049h" + ESC + "?25l" + ESC + "2J")
    caption("Tree view: root groups carry their machine (@cws, @pi); status rolls up from agents.", 3.2)

    caption("j / k move.  l / h unfold and fold. Collapsed groups show counts.")
    for _ in range(4):
        press("j", move(1))
    press("l", lambda: current().update(open=True), 1.6)
    press("h", lambda: current().update(open=False), 1.0)

    caption("]a jumps straight to the next agent that needs input.")
    press("]a", lambda: state.update(cursor=next(i for i, (n, _) in enumerate(visible())
                                                  if n["status"] == "blocked")), 2.0)

    caption("Enter opens the main view: that agent's conversation.")
    press("Enter", lambda: state.update(opened=current(), focus="main"), 2.6)

    caption("Answer it without leaving the keyboard.")
    type_into("Per order. But first find out why tax is off by a cent.")
    wait(0.5)
    def send():
        flow["convo"].append(("you", state["input"]))
        state["input"] = ""
        flow["status"] = "working"
    press("Enter", send, 0.8)
    stream(flow, "claude", "Got it, rounding per order. I'll hold the change until we know about the tax.", 1.4)

    caption("Tab back to the tree.  f forks the thread for a side investigation.")
    press("Tab", lambda: state.update(focus="tree"), 1.0)
    press("f", lambda: state.update(prompt="fork name: ", input=""), 0.5)
    type_into("why-tax-rounding")
    wait(0.4)
    fork = node("why-tax-rounding", "thread", "working", agent="claude")
    fork["convo"] = [("you", "Forked from checkout-flow. Find out why tax is off by a cent. Don't change code.")]
    def make_fork():
        flow["children"].append(fork)
        flow["open"] = True
        state.update(prompt="", input="", cursor=state["cursor"] + 1,
                     status="forked checkout-flow → why-tax-rounding  (same cwd, conversation fork)")
    press("Enter", make_fork, 1.6)

    caption("The fork is a child thread of checkout-flow. Open it to watch the investigation.")
    press("Enter", lambda: state.update(opened=fork, focus="main", status=""), 0.8)
    stream(fork, "tool", "grep -rn 'Math.round' src/cart", 0.7)
    stream(fork, "tool", "read src/cart/tax.ts:12-40", 0.7)
    stream(fork, "claude", "Tax is rounded per line and then summed, so a 3-line order can drift by up to 1 cent.", 1.2)
    stream(fork, "claude", "Fix: compute tax on the order subtotal and round once. Two tests in tax.test.ts assume the old behaviour.", 1.0)
    fork["status"] = "idle"
    draw()
    wait(1.4)

    caption("u rolls the finding up into the central memory, then tells the parent.")
    press("Tab", lambda: state.update(focus="tree"), 0.8)
    steps = [
        "roll-up 1/4 · asking why-tax-rounding to distill its findings …",
        "roll-up 2/4 · child pushed memory/2026-11-08-why-tax-rounding.md  (a1b2c3d)",
        "roll-up 3/4 · verified a1b2c3d on GitHub",
        "roll-up 4/4 · sent summary to checkout-flow · closed the fork",
    ]
    press("u", lambda: state.update(status=steps[0]), 1.3)
    for s in steps[1:]:
        state["status"] = s
        draw()
        wait(1.3)
    fork["status"] = "rolled"
    flow["convo"].append(("note", "Findings from why-tax-rounding: tax was rounded per line, then summed. "
                                  "Round once on the order subtotal. See memory/2026-11-08-why-tax-rounding.md."))
    state.update(cursor=state["cursor"] - 1)
    draw()
    wait(1.4)

    caption("The parent got the summary; the fork stays as ✓ → knowledge.")
    press("Enter", lambda: state.update(opened=flow, focus="main"), 3.2)

    state.update(key="", status="")
    caption("noesis · mock demo: scripted UI, no real agents.  See docs/spec.md.", 3.0)
    sys.stdout.write(RESET + ESC + "?25h" + ESC + "?1049l")
    sys.stdout.flush()


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        sys.stdout.write(RESET + ESC + "?25h" + ESC + "?1049l")
