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
        "Contact pressure from the interference fit: P = E·δ·(r_o^2 − r_i^2)(r_i^2 − r_e^2) / [2r_i^3(r_o^2 − r_e^2)] ≈ 139.6 psi nominal / 46.5 psi minimum, where E = 217,557 psi is the elastic modulus, δ = 0.0075 in nominal / 0.0025 in minimum is the interference, r_o = 1.18 in is the outer radius, r_i = 1.08 in is the interface radius, and r_e = 0.98 in is the inner radius.",
        "Holding force: F_hold = μ·P·2π·r_i·L ≈ 37.9 lb nominal (SF ≈ 1.41) / 12.6 lb minimum (SF ≈ 0.47), where μ = 0.2 is the friction coefficient, and L = 0.200 in is the length of engagement.",
    ],
    ("pool-boiling", "Sizing the bubble generation"): [
        "Critical gas flow rate per hole (Oguz & Prosperetti, 1993): Q_c = π·(16 / 3g^2)^(1/6)·(σ·r_n / ρ)^(5/6) ≈ 18–125 mL/min, where r_n = 0.1–1 mm is the needle (hole) radius, σ = 0.0679 N/m is the surface tension of water at 50 °C, ρ = 988 kg/m³ is its density, and g is gravitational acceleration.",
        "Bubble radius at detachment (buoyancy vs. surface tension): R_b = (3σ·r_n / 2ρg)^(1/3) ≈ 1.0–2.2 mm, where r_n = 0.1–1 mm is the needle (hole) radius, σ is the surface tension, ρ is the water density, and g is gravitational acceleration.",
    ],
    ("cantilevered-deltaxy", "Z-axis linkage stiffness"): [
        "Bearing radial compliance: c_r = δ / C_0 ≈ 0.020 µm/N, where δ = 8.2 µm is the bearing's deflection at its static load rating, taken as 0.5% of the ball diameter (rule of thumb), d_b = 1.64 mm is the ball diameter, and C_0 = 400 N is the static load rating.",
        "Pitch compliance of one bearing set: c_θ = 2c_r / S^2, where S = 70.6–102.6 mm is the span between the set's two bearings.",
        "Compliance at the toolhead: c_tool = L^2·(c_θ1 + c_θ2 + c_θ3) ≈ 0.90 µm/N vs. 2.42 µm/N originally, where L = 210 mm (linkage in front) vs. 323 mm (linkage in back) is the lever arm to the toolhead, and c_θ1–c_θ3 are the top, middle, and lower bearing sets.",
    ],
    ("pearcat", "Diagnosing the gearbox shortfall"): [
        "Torque requirements: T_req = F_req·(D_gear / 2) = (F_gear + m_robot·g·sin θ)·(D_gear / 2), where F_req is the force needed at the gear, F_gear is the force to turn the gear (measured with a force meter), m_robot is the expected robot mass, θ is the ramp angle (the hot air balloon is the θ = 90° case), and D_gear is the gear diameter.",
    ],
    ("unit-cell-tessellation", "Designing for stiffness"): [
        "Normalized stiffness: E*/E_s = 362.5 / 1,713 ≈ 0.212, where E* = 362.5 MPa is the tessellation's measured effective modulus, and E_s = 1,713 MPa is the modulus of the base resin.",
    ],
    ("unit-cell-tessellation", "Validating with FEA"): [
        "FEA vs. experiment: (E_FEA − E*) / E* = (370.5 − 362.5) / 362.5 ≈ 2.2%, where E_FEA = 370.5 MPa is the modulus predicted for the full 2×2×2 tessellation, and E* = 362.5 MPa is the measured modulus.",
    ],
    ("unit-cell-tessellation", "Testing in situ"): [
        "Engineering stress: σ = F / L^2, where F is the load measured by the nanoindenter, and L = 167.9 µm is the side of the square footprint.",
        "Engineering strain: ε = δ / H, where δ is the indenter displacement, and H = 146.09 µm is the sample height.",
        "Effective modulus: E* = Δσ / Δε ≈ 362.5 MPa, where Δσ / Δε is the slope of the steepest linear fit over any 1% strain window of the loading curve.",
        "Toughness (area under the loading curve, up to peak stress): W = ∫ σ dε ≈ 6.47 MJ/m³.",
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
    t = re.sub(r"(?<=[A-Za-zΣ])_([A-Za-z0-9α-ωΑ-Ω]+)", r"<sub>\1</sub>", t)
    return t


# ---------- Stacked fractions for equation boxes ----------
OPEN, CLOSE = "([", ")]"


def _leaf(s):
    """math_html, but keep the spaces around the piece (math_html strips them)."""
    if not s.strip():
        return s
    lead = " " if s[0] == " " else ""
    trail = " " if s[-1] == " " else ""
    return lead + math_html(s) + trail


def _top_level(s):
    """Yield (index, char) for characters not inside ( ) or [ ] groups."""
    depth = 0
    for i, ch in enumerate(s):
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth -= 1
        elif depth == 0:
            yield i, ch


def _split_top(s, seps):
    """Split on any of the spaced operators in seps (e.g. ' = '), only at the top level. Keeps the operators."""
    parts, last, i = [], 0, 0
    idx = {i for i, _ in _top_level(s)}
    while i < len(s):
        hit = next((sep for sep in seps if s.startswith(sep, i) and all(j in idx for j in range(i, i + len(sep)))), None)
        if hit:
            parts.append(s[last:i]); parts.append(hit); i += len(hit); last = i
        else:
            i += 1
    parts.append(s[last:])
    return parts


def _strip_wrap(s):
    """'(a + b)' -> 'a + b' when one pair of brackets wraps the whole string."""
    s = s.strip()
    if len(s) > 1 and s[0] in OPEN:
        depth = 0
        for i, ch in enumerate(s):
            depth += ch in OPEN
            depth -= ch in CLOSE
            if depth == 0:
                return s[1:-1].strip() if i == len(s) - 1 else s
    return s


def _frac(num, den):
    return (f'<span class="frac"><span class="frac__num">{_expr(_strip_wrap(num))}</span>'
            f'<span class="frac__den">{_expr(_strip_wrap(den))}</span></span>')


def _seq(s):
    """A term with no top-level fraction: typeset bracket groups that contain a fraction with tall fences."""
    out, buf, i = [], "", 0
    while i < len(s):
        ch = s[i]
        if ch in OPEN and not (i > 0 and s[i - 1] == "^"):
            depth, j = 0, i
            while j < len(s):
                depth += s[j] in OPEN
                depth -= s[j] in CLOSE
                if depth == 0:
                    break
                j += 1
            inner = s[i + 1:j]
            if any(c == "/" for _, c in _top_level(inner)):
                out.append(_leaf(buf)) if buf else None
                buf = ""
                out.append(f'<span class="fence">{ch}</span>{_expr(inner)}<span class="fence">{s[j]}</span>')
                i = j + 1
                continue
            buf += s[i:j + 1]
            i = j + 1
            continue
        buf += ch
        i += 1
    if buf:
        out.append(_leaf(buf))
    return "".join(out)


def _term(t):
    slash = next((i for i, c in _top_level(t) if c == "/"), None)
    if slash is None:
        return _seq(t)
    return _frac(t[:slash], t[slash + 1:])


def _expr(s):
    parts = _split_top(s, [" + ", " − ", " - "])
    return "".join(_leaf(p) if p in (" + ", " − ", " - ") else _term(p.strip()) for p in parts)


def eq_math_html(expr):
    """Equation-box math with stacked fractions. Anything after the first '≈' (a result, which may
    contain 'nominal / minimum' or units like mL/min) stays on one line."""
    expr = expr.strip()
    sym, approx = expr, ""
    cut = next((i for i, c in _top_level(expr) if expr.startswith(" ≈ ", i)), None)
    if cut is not None:
        sym, approx = expr[:cut], expr[cut:]
    sides = [p.strip() for p in _split_top(sym, [" = "]) if p != " = "]
    # each "= …" step stays in one piece, so a long chain wraps only at its equals signs
    res = f' <span class="eq__res">{math_html(approx)}</span>' if approx else ""
    if len(sides) > 2:
        # a chain of steps: one step per line, with the equals signs lined up under each other
        rows = "".join(f'<span class="eq__lhs">{_expr(sides[0]) if k == 0 else ""}</span>'
                       f'<span class="eq__step">= {_expr(p)}{res if k == len(sides) - 2 else ""}</span>'
                       for k, p in enumerate(sides[1:]))
        return f'<span class="eq__align">{rows}</span>'
    html_ = _expr(sides[0]) + "".join(f' <span class="eq__step">= {_expr(p)}</span>' for p in sides[1:])
    return html_ + res


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
            f'<div class="eq__math">{eq_math_html(m.group("eq"))}</div>{rows}</figure>')


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
    if item.get("stack"):        # images stacked in one column, sharing the row's height
        inner = "".join(media_el(it, "media", f' style="aspect-ratio:{item_ar(it):.3f}"') for it in item["stack"])
        return f'<div class="{cls.replace("media ", "")} media-stack"{style}>{inner}</div>'
    if not item.get("src"):      # gray placeholder until the image file exists
        label = html.escape(item.get("label", ""))
        return f'<figure class="{cls}"{style}>' + (f'<span class="media__label">{label}</span>' if label else "") + "</figure>"
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
    TARGET = float(IMAGES.get(slug, {}).get("gallery_target", 3.4))   # lower = taller rows
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
    if it.get("stack"):          # a column of images: widths equal, heights add up
        return 1 / sum(1 / item_ar(x) for x in it["stack"])
    return float(it.get("ar", 1))


def media_row(items):
    """One justified row: images share a height and keep their shape (or the "ar" you give them).
    An item with "w" (e.g. 0.4) takes that share of the row's width instead, and the row is centered."""
    def style(it):
        if it.get("w"):
            return f' style="flex:0 0 {float(it["w"]) * 100:.1f}%;max-width:{float(it["w"]) * 100:.1f}%;aspect-ratio:{item_ar(it):.3f};--ar:{item_ar(it):.3f}"'
        return f' style="flex:{item_ar(it):.3f} 1 0;aspect-ratio:{item_ar(it):.3f};--ar:{item_ar(it):.3f}"'
    figs = "".join(media_el(it, "media gallery__item", style(it)) for it in items)
    center = ' style="justify-content:center"' if any(it.get("w") for it in items) else ""
    return f'<div class="gallery__row gallery__row--flex"{center}>{figs}</div>'


EQ_FIG_RE = re.compile(r'<figure class="eq">.*?</figure>', re.S)


def media_rows(rows, eq_html=""):
    """Rows of media for custom layouts. A row containing {"eq": true} becomes an image beside the equation box(es)."""
    out = []
    for row in rows:
        if isinstance(row, dict) and row.get("groups"):
            # labeled groups side by side, e.g. 1. Original / 2. Offset plane / 3. No lead-in
            gs = []
            for g in row["groups"]:
                w = sum(item_ar(it) for it in g["items"])
                gs.append(f'<div class="media-group" style="flex:{w:.3f} 1 0">'
                          f'<p class="media-group__label">{inline(g.get("label", ""))}</p>{media_row(g["items"])}</div>')
            out.append('<div class="media-groups">' + "".join(gs) + "</div>")
            continue
        if any(it.get("eq") for it in row):
            pics = [it for it in row if not it.get("eq")]
            left = "".join(media_el(it, "media media--inset", f' style="aspect-ratio:{item_ar(it):.3f}"') for it in pics)
            out.append(f'<div class="media-pair"><div class="media-pair__pic">{left}</div><div class="media-pair__eq">{eq_html}</div></div>')
        else:
            out.append(media_row(row))
    return '<div class="media-rows">' + "".join(out) + "</div>"


def custom_decision(cfg, title, body, code_html):
    """Per-page decision layouts set in images.json ("layout": "stack" | "tall")."""
    if cfg.get("eq_grid"):   # equation boxes two per row instead of stacked
        found = EQ_FIG_RE.findall(body)
        if found:
            body = EQ_FIG_RE.sub("", body).rstrip() + '\n          <div class="eq-grid">' + "".join(found) + "</div>"
    eqs = "".join(EQ_FIG_RE.findall(body))
    uses_eq = any(it.get("eq") for row in cfg.get("rows", []) if isinstance(row, list) for it in row)
    if cfg["layout"] == "segments":
        uses_eq = False
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
    if cfg["layout"] == "segments":    # free-form: rows of text / images / equations, full width or two columns
        blocks = [b for b in body.split("\n          ") if b.strip()]
        eq_blocks = [b for b in blocks if b.startswith('<figure class="eq">')]
        text_blocks = [b for b in blocks if not b.startswith('<figure class="eq">')]

        def part(spec):
            out = ""
            if "text" in spec:
                out += '<div class="decision__text">' + "".join(text_blocks[i] for i in spec["text"] if i < len(text_blocks)) + "</div>"
            if spec.get("rows"):
                out += media_rows(spec["rows"])
            if spec.get("note"):     # small caption under the images
                centered = any(it.get("w") for row in spec.get("rows", []) if isinstance(row, list) for it in row)
                out += f'<p class="media-note"{" style=\"text-align:center\"" if centered else ""}>{inline(spec["note"])}</p>'
            if spec.get("eq"):   # true = every equation, or a list of indices to pick some
                picked = eq_blocks if spec["eq"] is True else [eq_blocks[i] for i in spec["eq"] if i < len(eq_blocks)]
                out += '<div class="seg__eq">' + "".join(picked) + "</div>"
            return out
        segs = []
        for seg in cfg["segments"]:
            if "full" in seg:
                segs.append(f'<div class="seg seg--full">{part(seg["full"])}</div>')
            else:
                a, b = seg.get("cols", [1, 1])
                align = f';align-items:{seg["align"]}' if seg.get("align") else ""   # e.g. "center"
                segs.append(f'<div class="seg seg--split" style="grid-template-columns:{a}fr {b}fr{align}">'
                            f'<div class="seg__col">{part(seg["left"])}</div><div class="seg__col">{part(seg["right"])}</div></div>')
        return f'''        <h3>{title}</h3>
        <div class="decision-segments">
          {"".join(segs)}
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
        {f'<p class="media-note">{esc(IMAGES[slug]["overview_note"])}</p>' if IMAGES.get(slug, {}).get("overview_note") else ""}
      </section>''')

    pair = []
    for key, sid, nav, heading in [
        ("context", "context", "Context/ Motivation", "Context/Motivation"),
        ("framing", "problem", "Problem Framing", "Problem Framing"),
    ]:
        if d.get(key):
            extra = (IMAGES.get(slug, {}).get("section_rows") or {}).get(sid)
            pair.append(f'''      <section id="{sid}" data-nav="{nav}">
        <h2>{heading}</h2>
          {render_body(d[key])}
          {media_rows(extra) if extra else ""}
      </section>''')
    # Context/Motivation and Problem Framing sit side by side (Synthia's Figma widths) unless a page sets
    # "split_context": false in images.json, or its own [left, right] column widths
    split = IMAGES.get(slug, {}).get("split_context", [528, 1123])
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
        sections.append('      <section id="process" data-nav="Design Process">\n        <h2>Design Process</h2>\n\n'
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
        <figure class="media"{f' style="aspect-ratio:{IMAGES[slug]["hero_ar"]}"' if IMAGES.get(slug, {}).get("hero_ar") else ""}><img src="../{IMAGES.get(slug, {}).get("hero", f"assets/img/covers/{slug}.jpg")}" alt="{html.escape(title)}"></figure>
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


MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]


def date_label(raw):
    """Sheet date -> display label. A date cell becomes "September 2026"; "(2nd)" order notes are dropped."""
    m = re.match(r"(\d{4})-(\d{2})-\d{2}", raw)
    if m:
        return f"{MONTHS[int(m.group(2)) - 1].capitalize()} {m.group(1)}"
    return re.sub(r"\s*\((\d+)(st|nd|rd|th)\)", "", raw).strip()


def date_key(label):
    """Sortable key. "January 2024 (2nd)" sorts after "(1st)" from the same month (newest first on the page)."""
    m = re.match(r"(\d{4})-(\d{2})-\d{2}", label)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    order = re.search(r"\((\d+)(?:st|nd|rd|th)\)", label)
    suffix = f".{order.group(1)}" if order else ""
    m = re.search(r"(" + "|".join(MONTHS) + r")\s+(\d{4})", label, re.I)
    if m:
        return f"{m.group(2)}-{MONTHS.index(m.group(1).lower()) + 1:02d}{suffix}"
    m = re.search(r"(winter|spring|summer|fall|autumn)\s+(\d{4})", label, re.I)
    return f"{m.group(2)}-{SEASON_MONTH[m.group(1).lower()]}{suffix}" if m else ""


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
        raw = TODO_RE.sub("", cell(ws, rows["date"], c)).strip()
        rank = cell(ws, rows["effort rank"], c) if "effort rank" in rows else ""
        material = TODO_RE.sub("", cell(ws, rows["material"], c)).strip() if "material" in rows else ""
        out.append({
            "title": TODO_RE.sub("", title).strip(),
            "blurb": material,          # the medium, art-label style; shown on hover and in the viewer
            "caption": TODO_RE.sub("", cell(ws, rows["one-liner"], c)).strip(),
            "date": date_key(raw),
            "dateLabel": date_label(raw),
            "effort": int(float(rank)) if rank else 0,   # 1 = most effort
            "image": cover_for(title),
            "link": "",
        })
        media = (IMAGES.get("more_projects") or {}).get(out[-1]["title"])
        if media:   # photos/videos for the viewer; the first one is the card's cover
            first = media[0]
            out[-1]["image"] = first.get("poster") or first["src"]
            out[-1]["coverFit"] = first.get("fit", "cover")
            out[-1]["media"] = [{k: v for k, v in it.items() if k in ("src", "poster", "fit", "ar", "cutout")} for it in media]
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
    opener = opener.rstrip().rstrip(".")   # masthead openers never end with a period
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
