"""Builds the interactive process section (Before AI / With AI) and swaps it into index.html.
Usage: python3 -I scripts/build_flow.py index.html
Edit step names, descriptions and which steps are AI-assisted in MODES below, then re-run.
"""
import sys, html, re, json

P = sys.argv[1]
UX, UI = "Research & UX design", "UI design"
FEEDBACK = ("feedback", "Customer feedback", "Every release", "The loop", False,
            "After launch, what customers say and do goes straight back into the start of the process.")

# Each step: (id, label, phase, track, ai_assisted, one-line description)
MODES = {
    "ai": {
        "tab": "With AI",
        "intro": "Shorter and more customer-focused. More time analysing what customers do and say, and clear specs that speed delivery to engineering.",
        "top": [
            ("signal", "Customer signal", "Discovery", UX, False,
             "Interviews, support tickets, reviews and product analytics: every place customers tell us something."),
            ("analysis", "Data analysis", "Discovery", UX, True,
             "AI helps sort and cluster large volumes of feedback and usage data. I check the patterns against real conversations before acting on them."),
            ("problem", "Problem statement", "Define", UX, False,
             "A problem backed by evidence, agreed with the team before design starts."),
        ],
        "bottom": [  # listed in flow order: right to left on screen
            ("prototype", "Prototype", "Design", UI, True,
             "AI speeds up exploring directions and building testable prototypes, so ideas reach customers sooner."),
            ("test", "Test with customers", "Design", UI, False,
             "Customers try the prototype. What confuses them goes straight back into the design."),
            ("specs", "Specs to engineering", "Develop", UI, True,
             "Clear specs, states and edge cases handed to engineering, so the build starts without back-and-forth."),
        ],
        "top_phases": [("Discovery", 0), ("Define", 2)],
        "bottom_phases": [("Develop", 0), ("Design", 1)],
        "top_divider": 1.5, "bottom_divider": 0.5,   # between which columns
    },
    "old": {
        "tab": "Before AI",
        "intro": "The full eight-step process, from requirements to design QA, with research and interface design run as separate tracks.",
        "top": [
            ("req", "Requirements", "Discovery", UX, False,
             "Business goals, constraints and what customers have already told us, gathered before any solution."),
            ("research", "Research", "Discovery", UX, False,
             "Interviews, data and sessions with real users to find where they struggle and why."),
            ("problem-old", "Problem Statement", "Define", UX, False,
             "One clear problem worth solving, agreed with the team before design starts."),
            ("solution", "Solution exploration", "Define", UX, False,
             "Several directions, weighed against effort and impact before committing to one."),
        ],
        "bottom": [
            ("design", "Design", "Design", UI, False,
             "Flows and interface for the chosen direction, built on the design system."),
            ("testing", "Testing", "Design", UI, False,
             "Real users try it before it ships. What confuses them goes back into the design."),
            ("handoffs", "Handoffs", "Develop", UI, False,
             "Specs, states and edge cases handed to engineering, with the reasoning behind them."),
            ("qa", "Design QA", "Develop", UI, False,
             "The built product checked against the design before release."),
        ],
        "top_phases": [("Discovery", 0), ("Define", 2)],
        "bottom_phases": [("Develop", 0), ("Design", 2)],
        "top_divider": 1.5, "bottom_divider": 1.5,
    },
}
ORDER = ["ai", "old"]  # first one is shown by default

NW, NH, X0, RIGHT = 190, 56, 260, 1090
Y1, Y2 = 90, 310
C1, C2 = Y1 + NH // 2, Y2 + NH // 2
LX = 206
PILL_W, PILL_H, PILL_CY = 176, 38, (C1 + C2) // 2


def cols(n):
    gap = (RIGHT - X0 - n * NW) / (n - 1)
    return [round(X0 + i * (NW + gap)) for i in range(n)]


def build_svg(key, m):
    n = len(m["top"]); X = cols(n)
    pos = {}
    for i, s in enumerate(m["top"]): pos[s[0]] = (X[i], Y1)
    for i, s in enumerate(m["bottom"]): pos[s[0]] = (X[n - 1 - i], Y2)
    marker = f"flow-arrow-{key}"

    def node(s):
        sid, label, phase, track, ai, _ = s
        x, y = pos[sid]
        tag = f'<text class="flow-ai" x="{x + NW - 10}" y="{y + 14}" text-anchor="end">AI</text>' if ai else ""
        aria = f"{label}, {phase}" + (", AI-assisted" if ai else "")
        return (f'<g class="flow-node{" flow-node--ai" if ai else ""}" data-step="{sid}" tabindex="0" role="button" '
                f'aria-pressed="false" aria-label="{html.escape(aria)}"><rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="2"/>'
                f'<text x="{x + NW / 2}" y="{y + NH / 2}" text-anchor="middle" dominant-baseline="central">{html.escape(label)}</text>{tag}</g>')

    def edge(frm, d):
        return f'<path class="flow-edge" data-from="{frm}" d="{d}" marker-end="url(#{marker})"/>'

    top, bot = [s[0] for s in m["top"]], [s[0] for s in m["bottom"]]
    edges = [edge(a, f"M{pos[a][0] + NW} {C1} H{pos[b][0] - 8}") for a, b in zip(top, top[1:])]
    R = X[-1] + NW
    edges.append(edge(top[-1], f"M{R} {C1} C{R + 78} {C1} {R + 78} {C2} {R + 8} {C2}"))
    edges += [edge(a, f"M{pos[a][0]} {C2} H{pos[b][0] + NW + 8}") for a, b in zip(bot, bot[1:])]
    edges.append(edge(bot[-1], f"M{X0} {C2} C{LX + 8} {C2} {LX} {C2 - 30} {LX} {PILL_CY + PILL_H // 2 + 8}"))
    edges.append(edge("feedback", f"M{LX} {PILL_CY - PILL_H // 2} C{LX} {C1 + 30} {LX + 8} {C1} {X0 - 8} {C1}"))

    pill = (f'<g class="flow-node flow-node--lit" data-step="feedback" tabindex="0" role="button" aria-pressed="false" '
            f'aria-label="Customer feedback, back to the start"><rect x="{LX - PILL_W // 2}" y="{PILL_CY - PILL_H // 2}" '
            f'width="{PILL_W}" height="{PILL_H}" rx="{PILL_H // 2}"/><text x="{LX}" y="{PILL_CY}" text-anchor="middle" '
            f'dominant-baseline="central">↻ Customer feedback</text></g>')

    def divx(d):  # between column floor(d) and ceil(d)
        a = X[int(d)] + NW; b = X[int(d) + 1]; return (a + b) // 2
    td, bd = divx(m["top_divider"]), divx(m["bottom_divider"])
    phases = "".join(f'<text class="flow-phase" x="{X[c]}" y="50">{p}</text>' for p, c in m["top_phases"])
    phases += "".join(f'<text class="flow-phase" x="{X[c]}" y="{Y2 + NH + 52}">{p}</text>' for p, c in m["bottom_phases"])
    return f'''<svg class="flow-svg" viewBox="0 0 1230 450" role="group" aria-label="{html.escape(m["tab"])}: {n * 2} steps across two tracks, looped by customer feedback">
              <defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" class="flow-arrowhead"/></marker></defs>
              <line class="flow-divider" x1="{td}" y1="22" x2="{td}" y2="{Y1 + NH + 70}"/>
              <line class="flow-divider" x1="{bd}" y1="{Y2 - 70}" x2="{bd}" y2="428"/>
              {phases}
              <text class="flow-track" x="0" y="{C1 - 10}">Research &amp;</text>
              <text class="flow-track" x="0" y="{C1 + 12}">User Experience design</text>
              <text class="flow-track" x="0" y="{C2}" dominant-baseline="central">User Interface design</text>
              {"".join(edges)}
              {"".join(node(s) for s in m["top"] + m["bottom"])}
              {pill}
            </svg>'''


def steps_of(m):
    return m["top"] + m["bottom"] + [FEEDBACK]


def build_list(m):
    out = []
    for sid, label, phase, track, ai, _ in steps_of(m):
        cls = "flow-item" + (" flow-item--lit" if sid == "feedback" else "")
        ai_tag = '<span class="flow-item__ai">AI</span>' if ai else ""
        out.append(f'              <li><button class="{cls}" type="button" data-step="{sid}" aria-pressed="false">'
                   f'<span class="flow-item__label">{html.escape(label)}</span>{ai_tag}</button></li>')
    return "\n".join(out)


panels, data = [], {}
for i, key in enumerate(ORDER):
    m = MODES[key]
    hidden = "" if i == 0 else " hidden"
    panels.append(f'''          <div class="flow-mode" data-flow-mode="{key}"{hidden}>
            {build_svg(key, m)}
            <ol class="flow-list" aria-label="{html.escape(m["tab"])} steps">
{build_list(m)}
            </ol>
          </div>''')
    data[key] = {"intro": m["intro"], "steps": [
        {"id": s[0], "label": s[1], "phase": s[2], "track": s[3], "ai": s[4], "text": s[5]} for s in steps_of(m)]}

first = MODES[ORDER[0]]
f0 = steps_of(first)[0]
tabs = "".join(f'<button type="button" data-flow-tab="{k}" aria-pressed="{"true" if i == 0 else "false"}">{MODES[k]["tab"]}</button>'
               for i, k in enumerate(ORDER))
n_ai, n_old = len(steps_of(MODES["ai"])) - 1, len(steps_of(MODES["old"])) - 1

section = f'''    <section class="section section--spot" id="process" aria-labelledby="process-title">
      <div class="wrap">
        <h2 class="display reveal" id="process-title">End-to-end, <span class="lit">looped</span> by customers</h2>
        <div class="flow reveal" data-flow>
          <div class="flow-head">
            <p class="body-l flow-intro" data-flow-intro>{html.escape(first["intro"])}</p>
            <div class="flow-switch">
              <div class="seg" role="group" aria-label="Compare processes">{tabs}</div>
            </div>
          </div>
          <hr class="beam" style="margin-top:40px">
{chr(10).join(panels)}
          <div class="flow-panel">
            <div class="flow-detail" aria-live="polite">
              <h3 class="flow-detail__title" data-flow-title>{html.escape(f0[1])}</h3>
              <p class="body" data-flow-text>{html.escape(f0[5])}</p>
            </div>
            <div class="flow-controls">
              <button class="btn btn--ghost" type="button" data-flow-play>Play the loop</button>
            </div>
          </div>
          <ul class="flow-changes" data-flow-only="ai">
            <li><p>More time in research. AI helps analyse interviews, tickets and usage data at scale, so decisions start from evidence.</p></li>
            <li><p>Ideas become testable prototypes faster, so customers see them sooner and steer the design.</p></li>
            <li><p>Clear specs speed delivery to engineering and cut the back-and-forth of separate handoff and QA rounds.</p></li>
          </ul>
          <script type="application/json" data-flow-steps>{json.dumps(data, ensure_ascii=False)}</script>
        </div>
      </div>
    </section>
'''

s = open(P, encoding="utf-8").read()
mm = re.search(r'    <section class="section section--spot" id="process".*?</section>\n', s, re.S)
assert mm, "process section not found"
s = s[:mm.start()] + section + s[mm.end():]
open(P, "w", encoding="utf-8").write(s)
print("process section replaced:", n_old, "->", n_ai, "steps")
