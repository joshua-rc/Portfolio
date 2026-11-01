"""
Rebuild the project pages and project lists from the content spreadsheet.

Usage (from the Portfolio folder):
    python tools/build_from_sheet.py path/to/Projects.xlsx

Reads the "Main Projects" tab (one column per project, one row per section)
and the "Mini Projects" tab, then writes:
  - projects/<slug>.html          one page per Main Project column with content
  - assets/js/projects.js          card blurbs (Hook row) + More Projects list

Text conventions in the sheet:
  - Blank line                    -> new paragraph
  - A line ending in ":"          -> the lines after it become a bullet list
                                      (in "At a glance", it becomes a small label)
  - "Matlab script:" / "Code:"    -> everything after it is shown as a
                                      collapsible code block
  - [NEEDS INPUT ...] [CONFIRM ...] -> highlighted yellow so drafts are easy to spot
Requires: pip install openpyxl
"""
import html
import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent

# Sheet column title -> page slug (must match SELECTED_WORK slugs)
SLUGS = {
    "PearCat": "pearcat",
    "Synthia": "synthia",
    "Cantilevered DeltaXY": "cantilevered-deltaxy",
    "TwoFold": "twofold",
    "Layer by Layer": "layer-by-layer",
    "Small-scale Pool Boiling Facility": "pool-boiling",
    "MochiMash": "mochimash",
    "YubbaYubba": "yubbayubba",
    "en clair": "en-clair",
    "Unit Cell Tessellation": "unit-cell-tessellation",
    "Archetype": "archetype-ai",
    "Discover Mechanical Engineering (DME)": "dme-2026",
}

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
TODO_RE = re.compile(r"\[(?:NEEDS INPUT|CONFIRM)[^\]]*\]|^\[[^\]]+\]$", re.M)
CODE_START_RE = re.compile(r"^(matlab script|matlab|code|python script)[^:]*:\s*$", re.I)


def esc(s):
    return html.escape(s, quote=False)


def inline(text):
    """Escape text and highlight [NEEDS INPUT]/[CONFIRM] notes."""
    out, last = [], 0
    for m in TODO_RE.finditer(text):
        out.append(esc(text[last:m.start()]))
        out.append(f'<span class="todo">{esc(m.group(0))}</span>')
        last = m.end()
    out.append(esc(text[last:]))
    return "".join(out)


def is_equation(line):
    return ("=" in line or "³" in line) and len(line.split()) < 14 and not line.rstrip().endswith(".")


# ---------- Equation callouts ----------
# In the sheet, put an equation on its own line in this form and it becomes a box:
#   Label: equation, where X is ..., Y is ..., and Z is ...
# Variables: write subscripts as X_y (or Unicode like Rᵢ); ^ for powers (L^3) or Unicode (L³).
EQ_LINE_RE = re.compile(r"^(?P<label>[A-Z][^:=]{0,60}):\s*(?P<eq>(?:[^,]|,(?=\d{3}))*=(?:[^,]|,(?=\d{3}))*?)(?:,\s*where\s+(?P<where>.+?))?\.?$")

# Extra equations shown under a decision, for math that lives in your scripts rather than the
# sheet text. Keyed by (page slug, decision title). Same line format as above.
EXTRA_EQUATIONS = {
    ("layer-by-layer", "Standardizing test samples"): [
        "Rectangular beam: I_rect = b·h^3 / 12 ≈ 4,345 mm⁴, where b = 19 mm is the beam width, and h = 14 mm is the beam height.",
        "Wide-flange beam (parallel axis theorem): I_WF = Σ (I_i + A_i·d_i^2), where I_i is the moment of inertia of each flange and the web about its own centroid, A_i is its area, and d_i is the distance from its centroid to the beam's centroid.",
        "Matching the two, solved for web width: b_w = [I_rect − Σ_flanges (I_i + A_i·d_i^2)] / (t_w^3/12 + t_w·d_w^2) ≈ 2.55 mm, where t_w = 9 mm is the web height, and d_w is the distance from the web's centroid to the beam's centroid.",
    ],
    ("yubbayubba", "Interference fit analysis and validation"): [
        "Impact speed from the drop test: v_impact = √(2·g·h_drop) ≈ 16.05 ft/s, where g = 32.2 ft/s² is gravitational acceleration, and h_drop = 4 ft is the drop height.",
        "Force the joint must survive: F_escape = m·v_impact / t_stop ≈ 26.96 lb, where m = 0.00336 slug is the mass of the yo-yo assembly, and t_stop = 0.002 s is the stopping time on impact.",
        "Contact pressure from the interference fit: P = (E / r_i)·δ·[(r_o^2 − r_i^2)(r_i^2 − r_e^2)] / [2r_i^2(r_o^2 − r_e^2)] ≈ 139.6 psi nominal / 46.5 psi minimum, where E = 217,557 psi is the elastic modulus, δ = 0.0075 in nominal / 0.0025 in minimum is the interference, r_o = 1.18 in is the outer radius, r_i = 1.08 in is the interface radius, and r_e = 0.98 in is the inner radius.",
        "Holding force: F_hold = μ·P·2π·r_i·L ≈ 37.9 lb nominal (SF ≈ 1.41) / 12.6 lb minimum (SF ≈ 0.47), where μ = 0.2 is the friction coefficient, and L = 0.200 in is the length of engagement.",
    ],
    ("pool-boiling", "Sizing the bubble generation"): [
        "Critical gas flow rate per hole (Oguz & Prosperetti, 1993): Q_c = π·(16 / 3g^2)^(1/6)·(σ·r_n / ρ)^(5/6) ≈ 18–125 mL/min, where r_n = 0.1–1 mm is the needle (hole) radius, σ = 0.0679 N/m is the surface tension of water at 50 °C, ρ = 988 kg/m³ is its density, and g is gravitational acceleration.",
        "Bubble radius at detachment (buoyancy vs. surface tension): R_b = (3σ·r_n / 2ρg)^(1/3) ≈ 1.0–2.2 mm, where r_n = 0.1–1 mm is the needle (hole) radius, σ is the surface tension, ρ is the water density, and g is gravitational acceleration.",
    ],
    ("layer-by-layer", "Automating the analysis"): [
        "Flexural modulus (three-point bending): E = L^3·m / 48I, where L = 120 mm is the support span, m is the slope of the linear regime of the load–displacement curve, and I is the beam's measured moment of inertia.",
    ],
}


def math_html(expr):
    """Escape and typeset simple math: X_y -> subscript, ^n -> superscript."""
    t = esc(expr.strip())
    # Unicode subscripts (Rᵢ, Eₛ, σᵧₛ) -> real subscripts so they match X_y ones
    sub = {"ᵢ": "i", "ₛ": "s", "ᵧ": "y", "ₓ": "x", "ₙ": "n", "ₘ": "m", "ₜ": "t", "ₐ": "a", "ₑ": "e", "ₒ": "o",
           "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4"}
    t = re.sub("[" + "".join(sub) + "]+", lambda m: "<sub>" + "".join(sub[c] for c in m.group(0)) + "</sub>", t)
    t = re.sub(r"\^\(([^)]+)\)", r"<sup>\1</sup>", t)
    t = re.sub(r"\^([0-9A-Za-z]+)", r"<sup>\1</sup>", t)
    t = re.sub(r"(?<=[A-Za-zΣ])_([A-Za-z0-9]+)", r"<sub>\1</sub>", t)
    return t


def split_where(where):
    """'Rᵢ and R_f are the radii, Y is yield strength, and t is thickness' -> [(vars, meaning)]"""
    items = re.split(r",\s+(?:and\s+)?", where.strip().rstrip("."))  # "217,557" stays whole
    out, i = [], 0
    while i < len(items):
        it = items[i]
        m = re.match(r"^(?P<v>.+?)\s+(?:is|are)\s+(?P<m>.+)$", it)
        if m:
            out.append((m.group("v"), m.group("m")))
        elif out:  # continuation of the previous meaning (a comma inside it)
            out[-1] = (out[-1][0], out[-1][1] + ", " + it)
        i += 1
    return out


def render_equation(line):
    m = EQ_LINE_RE.match(line.strip())
    if not m:
        return None
    rows = ""
    if m.group("where"):
        # "b = 19 mm is the width" -> variable "b", meaning "the width (19 mm)"
        defs = []
        for v, meaning in split_where(m.group("where")):
            val = ""
            vm = re.match(r"^(.+?)\s*=\s*(.+)$", v)
            if vm:
                v, val = vm.group(1), vm.group(2)
            vars_html = ", ".join(f'<var>{math_html(x)}</var>' for x in re.split(r"\s+and\s+|,\s*", v) if x.strip())
            extra = f' <span class="eq__val">({esc(val)})</span>' if val else ""
            defs.append(f"<dt>{vars_html}</dt><dd>{esc(meaning)}{extra}</dd>")
        rows = f'<dl class="eq__vars">{"".join(defs)}</dl>'
    return (f'<figure class="eq"><figcaption class="eq__label">{esc(m.group("label"))}</figcaption>'
            f'<div class="eq__math">{math_html(m.group("eq"))}</div>{rows}</figure>')


def render_body(text, para_class="body-text", split_code=False):
    """Turn a cell into HTML paragraphs / lists / code blocks."""
    if not text:
        return ("", "") if split_code else ""
    lines = text.replace("\r", "").split("\n")
    # split off a trailing code block
    code = None
    for i, ln in enumerate(lines):
        if CODE_START_RE.match(ln.strip()):
            code = "\n".join(lines[i + 1:]).strip("\n")
            label = ln.strip().rstrip(":")
            lines = lines[:i]
            break
    parts, i = [], 0
    while i < len(lines):
        ln = lines[i].strip()
        if not ln:
            i += 1
            continue
        if ln.endswith(":") and i + 1 < len(lines) and lines[i + 1].strip():
            parts.append(f'<p class="{para_class}">{inline(ln)}</p>')
            items = []
            i += 1
            while i < len(lines) and lines[i].strip():
                items.append(f"<li>{inline(re.sub(r'^[-•*]\s+', '', lines[i].strip()))}</li>")
                i += 1
            parts.append(f'<ul class="body-list">{"".join(items)}</ul>')
            continue
        eq = render_equation(ln)
        if eq:
            parts.append(eq)
            i += 1
            continue
        foot = re.match(r"^(.*=.*?)\s+(\*\S.*)$", ln)
        if foot:  # "formula *footnote"
            parts.append(f'<p class="equation">{inline(foot.group(1))}</p>')
            parts.append(f'<p class="footnote">{inline(foot.group(2))}</p>')
        else:
            cls = "equation" if is_equation(ln) else para_class
            parts.append(f'<p class="{cls}">{inline(ln)}</p>')
        i += 1
    code_html = (f'<details class="code"><summary>View {esc(label)}</summary>'
                 f"<pre><code>{esc(code)}</code></pre></details>") if code else ""
    if split_code:
        return "\n          ".join(parts), code_html
    return "\n          ".join(parts + ([code_html] if code_html else []))


def render_glance(text):
    """'At a glance' panel: blank-line groups; 'Label:' lines become small labels."""
    groups = [g for g in re.split(r"\n\s*\n", text.strip()) if g.strip()]
    out = []
    for g in groups:
        rows = []
        for ln in g.split("\n"):
            ln = ln.strip()
            if not ln:
                continue
            if ln.endswith(":"):
                continue  # header line ("Tools:", "Design methodology:") — labels hidden for now
            if ":" in ln and not ln.startswith("[") and ln.index(":") < 24:
                ln = ln.split(":", 1)[1].strip()  # "Course: 2.007 ..." -> "2.007 ..."
            rows.append(inline(ln))
        out.append("<p>" + "<br>".join(rows) + "</p>")
    return "\n          ".join(out)


def render_outcome(text):
    items = [re.sub(r"^[-•]\s+", "", ln.strip()) for ln in text.split("\n") if ln.strip()]
    return '<ul class="outcome-list">' + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>"


# ---------- Images (tools/images.json) ----------
IMAGES = {}


def load_images():
    f = ROOT / "tools" / "images.json"
    if f.exists():
        IMAGES.update({k: v for k, v in json.loads(f.read_text()).items() if not k.startswith("_")})


def media_el(item, cls="media", style=""):
    """<figure> for one image or video from images.json."""
    src = "../" + item["src"]
    fit = item.get("fit", "cover")
    alt = html.escape(item.get("alt") or "")
    if src.lower().endswith((".mp4", ".webm", ".mov")):
        inner = (f'<video src="{src}" autoplay muted loop playsinline preload="metadata"'
                 + (f' poster="../{item["poster"]}"' if item.get("poster") else "") + "></video>")
    else:
        inner = f'<img src="{src}" alt="{alt}" loading="lazy">'
    return f'<figure class="{cls} media--{fit}"{style}>{inner}</figure>'


def decision_media(slug, n):
    item = (IMAGES.get(slug, {}).get("decisions", {}) or {}).get(str(n))
    if item:
        ar = max(0.75, min(float(item.get("ar", 1)), 1.6)) if item.get("fit", "cover") == "cover" \
            else max(0.6, min(float(item.get("ar", 1)), 2.4))
        return media_el(item, style=f' style="aspect-ratio:{ar:.3f}"')
    if slug in IMAGES:          # this page has images, just not for this decision -> text only
        return ""
    return '<figure class="media"></figure>'   # no images yet -> gray placeholder


def gallery_html(slug):
    items = IMAGES.get(slug, {}).get("gallery")
    if not items:
        return """<div class="gallery">
          <div class="gallery__row gallery__row--3">
            <figure class="media"></figure><figure class="media"></figure><figure class="media"></figure>
          </div>
          <div class="gallery__row gallery__row--2">
            <figure class="media"></figure><figure class="media"></figure>
          </div>
          <div class="gallery__row gallery__row--4">
            <figure class="media"></figure><figure class="media"></figure><figure class="media"></figure><figure class="media"></figure>
          </div>
        </div>"""
    # Fill each row until its images' combined width/height ratio reaches ~3.4, so every
    # row is about the same height; images in a row share one height and keep their shape.
    TARGET = 3.4
    rows, row, total = [], [], 0.0
    for it in items:
        row.append(it); total += float(it.get("ar", 1))
        if total >= TARGET:
            rows.append(row); row, total = [], 0.0
    if row:
        rows.append(row)
    out = []
    for row in rows:
        figs = "".join(media_el(it, "media gallery__item",
                                f' style="flex:{float(it.get("ar", 1)):.3f} 1 0;aspect-ratio:{float(it.get("ar", 1)):.3f}"')
                       for it in row)
        ar_sum = sum(float(it.get("ar", 1)) for it in row)
        cap = "" if ar_sum >= TARGET else f' style="max-width:calc(100% * {ar_sum / TARGET:.3f})"'  # short last row keeps row height
        out.append(f'<div class="gallery__row gallery__row--flex"{cap}>{figs}</div>')
    return '<div class="gallery">\n          ' + "\n          ".join(out) + "\n        </div>"


def item_ar(it):
    return float(it.get("ar", 1))


def media_row(items):
    """One justified row: images share a height and keep their shape (or the "ar" you give them)."""
    figs = "".join(media_el(it, "media gallery__item",
                            f' style="flex:{item_ar(it):.3f} 1 0;aspect-ratio:{item_ar(it):.3f};--ar:{item_ar(it):.3f}"')
                   for it in items)
    return f'<div class="gallery__row gallery__row--flex">{figs}</div>'


EQ_FIG_RE = re.compile(r'<figure class="eq">.*?</figure>', re.S)


def media_rows(rows, eq_html=""):
    """Rows of media for custom layouts. A row containing {"eq": true} becomes an image beside the equation box(es)."""
    out = []
    for row in rows:
        if any(it.get("eq") for it in row):
            pics = [it for it in row if not it.get("eq")]
            left = "".join(media_el(it, "media media--inset", f' style="aspect-ratio:{item_ar(it):.3f}"') for it in pics)
            out.append(f'<div class="media-pair"><div class="media-pair__pic">{left}</div><div class="media-pair__eq">{eq_html}</div></div>')
        else:
            out.append(media_row(row))
    return '<div class="media-rows">' + "".join(out) + "</div>"


def custom_decision(cfg, title, body, code_html):
    """Per-page decision layouts set in images.json ("layout": "stack" | "tall")."""
    eqs = "".join(EQ_FIG_RE.findall(body))
    uses_eq = any(it.get("eq") for row in cfg.get("rows", []) for it in row)
    if uses_eq:
        body = EQ_FIG_RE.sub("", body)
    code = (chr(10) + "        " + code_html) if code_html else ""
    if cfg["layout"] == "stack":       # text across the top, rows of media underneath
        return f'''        <h3>{title}</h3>
        <div class="decision-stack">
          <div class="decision__text">
          {body}
          </div>
          {media_rows(cfg.get("rows", []), eqs if uses_eq else "")}
        </div>{code}'''
    if cfg["layout"] == "tall":        # tall media on the left; text, then a row of media, on the right
        tall = cfg["tall"]
        return f'''        <h3>{title}</h3>
        <div class="decision-tall">
          {media_el(tall, "media", f' style="aspect-ratio:{item_ar(tall):.3f}"')}
          <div class="decision-tall__side">
            <div class="decision__text">
            {body}
            </div>
            {media_rows(cfg.get("rows", []))}
          </div>
        </div>{code}'''
    raise ValueError("unknown layout " + cfg["layout"])


def page(slug, d):
    title = d["title"]
    sections = []

    if d.get("overview"):
        sections.append(f'''      <section id="overview" data-nav="Project Overview">
        <div class="project__summary">
          {render_body(d["overview"], "summary-text")}
        </div>
        {media_rows(IMAGES[slug]["overview_rows"]) if IMAGES.get(slug, {}).get("overview_rows") else ""}
      </section>''')

    pair = []
    for key, sid, nav, heading in [
        ("context", "context", "Context/ Motivation", "Context/Motivation"),
        ("framing", "problem", "Problem Framing", "Problem Framing"),
    ]:
        if d.get(key):
            pair.append(f'''      <section id="{sid}" data-nav="{nav}">
        <h2>{heading}</h2>
          {render_body(d[key])}
      </section>''')
    split = IMAGES.get(slug, {}).get("split_context")   # e.g. [528, 1123]: side by side, column widths from Figma
    if split and len(pair) == 2:
        sections.append(f'      <div class="section-split" style="grid-template-columns:{split[0]}fr {split[1]}fr">\n'
                        + "\n".join(pair) + "\n      </div>")
    else:
        sections.extend(pair)

    if d["decisions"]:
        blocks = []
        for n, dec in enumerate(d["decisions"]):
            first, _, rest = dec.strip().partition("\n")
            cfg = (IMAGES.get(slug, {}).get("decisions", {}) or {}).get(str(n + 1)) or {}
            if cfg.get("layout"):
                body, code_html = render_body(rest.strip(), split_code=True)
                extras = [render_equation(x) for x in EXTRA_EQUATIONS.get((slug, first.strip()), [])]
                body += "".join("\n          " + e for e in extras if e)
                blocks.append(custom_decision(cfg, inline(first.strip()), body, code_html))
                continue
            fig = decision_media(slug, n + 1)
            flip = " decision--flip" if n % 2 else ""
            if not fig:
                flip = " decision--textonly"
            body, code_html = render_body(rest.strip(), split_code=True)
            extras = [render_equation(x) for x in EXTRA_EQUATIONS.get((slug, first.strip()), [])]
            if extras:
                body += "\n          " + "\n          ".join(e for e in extras if e)
            blocks.append(f'''        <h3>{inline(first.strip())}</h3>
        <div class="decision{flip}">
          {fig}
          <div class="decision__text">
          {body}
          </div>
        </div>{chr(10) + "        " + code_html if code_html else ""}''')
        sections.append('      <section id="process" data-nav="Process">\n        <h2>Process</h2>\n\n'
                        + "\n\n".join(blocks) + "\n      </section>")

    if d.get("improve"):
        sections.append(f'''      <section id="improvement" data-nav="Room for Improvement">
        <h2>Room for Improvement</h2>
          {render_body(d["improve"])}
      </section>''')

    if d.get("outcome") and d["outcome"].strip().lower() not in ("n/a", "na"):
        gallery_only = d["outcome"].strip().lower().startswith("gallery")
        outcome_list = "" if gallery_only else render_outcome(d["outcome"])
        sections.append(f'''      <section id="outcome" data-nav="Outcome">
        <h2>Outcome</h2>
        {outcome_list}
        {gallery_html(slug)}
      </section>''')

    if d.get("reflection"):
        sections.append(f'''      <section id="reflection" data-nav="Reflection">
        <h2>Reflection</h2>
          {render_body(d["reflection"])}
      </section>''')

    desc = re.sub(r"\s+", " ", TODO_RE.sub("", d.get("hook") or title)).strip()
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — Joshua Rivera Camacho</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="stylesheet" href="../assets/css/style.css">
</head>
<!-- Generated from the content spreadsheet by tools/build_from_sheet.py.
     Re-running the script overwrites this file. -->
<body data-page="project" data-root="../" data-slug="{slug}">
  <div class="page page--project">
    <aside class="sidebar" id="sidebar"></aside>

    <main class="project">
      <h1 class="project__title">{esc(title)}</h1>

      <div class="project__hero">
        <figure class="media"><img src="../{IMAGES.get(slug, {}).get("hero", f"assets/img/covers/{slug}.jpg")}" alt="{html.escape(title)}"></figure>
        <div class="project__info">
          {render_glance(d.get("glance") or "")}
        </div>
      </div>

{chr(10).join(sections)}
    </main>
  </div>
  <script src="../assets/js/projects.js"></script>
  <script src="../assets/js/site.js"></script>
</body>
</html>
'''


def cell(ws, r, c):
    v = ws.cell(r, c).value
    return str(v).strip() if v is not None else ""


def read_main(ws):
    # locate rows by their label in column A / B
    rows = {}
    for r in range(1, ws.max_row + 1):
        a, b = cell(ws, r, 1), cell(ws, r, 2)
        if a:
            rows.setdefault(a.strip('"').lower(), r)
        if re.match(r"^Decision \d+$", b):
            rows.setdefault("decisions", []).append(r)
    projects = {}
    for c in range(3, ws.max_column + 1):
        head = cell(ws, 1, c)
        if not head:
            continue
        key = next((k for k in SLUGS if head.lower().startswith(k.lower())), None)
        if not key:
            print(f"  ! no slug for column '{head}' — skipped")
            continue
        get = lambda name: cell(ws, rows[name], c) if name in rows else ""
        d = {
            "title": head,
            "hook": get("hook"),
            "overview": get("overview"),
            "glance": get("at a glance"),
            "context": get("context/motivation"),
            "framing": get("problem framing"),
            "decisions": [cell(ws, r, c) for r in rows.get("decisions", []) if cell(ws, r, c)],
            "improve": get("room for improvement"),
            "outcome": get("outcome"),
            "reflection": get("reflection"),
        }
        projects[SLUGS[key]] = d
    return projects


SEASON_MONTH = {"january": "01", "winter": "01", "spring": "03", "summer": "06", "fall": "09", "autumn": "09"}


def date_key(label):
    m = re.search(r"(january|winter|spring|summer|fall|autumn)\s+(\d{4})", label, re.I)
    return f"{m.group(2)}-{SEASON_MONTH[m.group(1).lower()]}" if m else ""


def cover_for(title):
    slug = re.sub(r"[^a-z0-9]+", "-", TODO_RE.sub("", title).lower()).strip("-")
    f = ROOT / "assets/img/covers" / f"{slug}.jpg"
    return f"assets/img/covers/{slug}.jpg" if f.exists() else ""


def read_opener(ws):
    return cell(ws, 2, 1) if cell(ws, 1, 1).lower() == "opener" else ""


def read_mini(ws):
    rows = {cell(ws, r, 2).lower(): r for r in range(1, ws.max_row + 1) if cell(ws, r, 2)}
    out = []
    for c in range(3, ws.max_column + 1):
        title = cell(ws, rows["title"], c)
        if not title:
            continue
        label = TODO_RE.sub("", cell(ws, rows["date"], c)).strip()
        out.append({
            "title": TODO_RE.sub("", title).strip(),
            "blurb": "",
            "caption": TODO_RE.sub("", cell(ws, rows["one-liner"], c)).strip(),
            "date": date_key(label),
            "dateLabel": label,
            "effort": 0,
            "image": cover_for(title),
            "link": "",
        })
    return out


def update_projects_js(main, mini):
    p = ROOT / "assets/js/projects.js"
    js = p.read_text()
    # remove Selected Work entries that are no longer columns in the sheet
    block = re.search(r"window\.SELECTED_WORK = \[\n(.*?)\n\];", js, re.S)
    entries = re.findall(r"  \{ slug: \"[^\"]+\".*?\},?(?=\n  \{ slug:|\s*$)", block.group(1), re.S)
    kept = []
    for e in entries:
        slug = re.match(r'  \{ slug: "([^"]+)"', e).group(1)
        if slug in main:
            kept.append(e.rstrip(","))
        else:
            print(f"  - removed {slug} from Selected Work (not in sheet)")
    js = js[:block.start(1)] + ",\n".join(kept) + js[block.end(1):]
    # card blurbs = Hook row
    for slug, d in main.items():
        if not d["hook"]:
            continue
        blurb = json.dumps(re.sub(r"\s+", " ", TODO_RE.sub("", d["hook"])).strip(), ensure_ascii=False)
        pat = re.compile(r'(\{ slug: "%s",.*?blurb: )".*?"(,)' % re.escape(slug), re.S)
        js, n = pat.subn(lambda m: m.group(1) + blurb + m.group(2), js, count=1)
        if not n:
            print(f"  ! couldn't set blurb for {slug}")
    # More Projects list
    items = ",\n".join("  " + json.dumps(x, ensure_ascii=False) for x in mini)
    js, n = re.subn(r"window\.MORE_PROJECTS = \[.*?\n\];",
                    "window.MORE_PROJECTS = [\n" + items + "\n];", js, count=1, flags=re.S)
    if not n:
        print("  ! couldn't find MORE_PROJECTS")
    p.write_text(js)


def main():
    xlsx = sys.argv[1]
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    load_images()
    projects = read_main(wb["Main Projects"])
    for slug, d in projects.items():
        has_content = any(d[k] for k in ("overview", "glance", "context", "framing", "decisions"))
        if not has_content:
            print(f"  - {slug}: no content in sheet, page left as is")
            continue
        (ROOT / "projects" / f"{slug}.html").write_text(page(slug, d))
        print(f"  ✓ projects/{slug}.html")
    mini = read_mini(wb["Mini Projects"]) if "Mini Projects" in wb.sheetnames else []
    update_projects_js(projects, mini)
    opener = read_opener(wb["Mini Projects"]) if "Mini Projects" in wb.sheetnames else ""
    if opener:
        for f in ("more-projects-by-date.html", "more-projects-by-effort.html"):
            fp = ROOT / f
            h = fp.read_text()
            h = re.sub(r"(<header class=\"masthead masthead--more\">\s*<h1>).*?(</h1>)",
                       lambda m: m.group(1) + esc(opener) + m.group(2), h, count=1, flags=re.S)
            fp.write_text(h)
        print("  ✓ More Projects opener")
    print(f"  ✓ assets/js/projects.js ({len(mini)} More Projects)")


if __name__ == "__main__":
    main()
