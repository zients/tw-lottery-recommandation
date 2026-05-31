from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote

# Inline SVG favicon (a neon ball on a dark tile) embedded as a data URI so the
# report stays a single self-contained file with zero external requests.
_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<defs><radialGradient id="g" cx="38%" cy="32%" r="75%">'
    '<stop offset="0" stop-color="#9ec5ff"/>'
    '<stop offset=".55" stop-color="#3aa0ff"/>'
    '<stop offset="1" stop-color="#7b5cff"/>'
    "</radialGradient></defs>"
    '<rect width="32" height="32" rx="7" fill="#070a14"/>'
    '<circle cx="16" cy="16" r="9" fill="url(#g)"/>'
    "</svg>"
)
_FAVICON = "data:image/svg+xml," + quote(_FAVICON_SVG)

# Neon accent per lottery type. Drives the whole card via the CSS var --c:
# top glow line, name dot, badge border, and number-ball gradient/glow.
_ACCENT: dict[str, str] = {
    "539": "#2ee6a6",
    "649": "#3aa0ff",
    "638": "#ff9d42",
    "3d":  "#9b7bff",
    "4d":  "#ff6ec4",
}
_ACCENT_FALLBACK = "#6fb4ff"

_CSS = """\
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#070a14;--ink:#dfe6ff;--muted:#8793b8;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang TC','Noto Sans TC',sans-serif;
  --mono:ui-monospace,'SF Mono',Menlo,Consolas,'Roboto Mono',monospace;
}
body{font-family:var(--sans);background:var(--bg);color:var(--ink);min-height:100vh;background-image:radial-gradient(120% 70% at 50% -10%,#16203f 0%,#070a14 55%)}
.wrap{max-width:440px;margin:0 auto;padding:0 1.1rem 3rem;position:relative}
.wrap::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background-image:linear-gradient(rgba(120,160,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(120,160,255,.045) 1px,transparent 1px);background-size:30px 30px;-webkit-mask-image:radial-gradient(120% 80% at 50% 0%,#000 30%,transparent 80%);mask-image:radial-gradient(120% 80% at 50% 0%,#000 30%,transparent 80%)}
header{position:relative;z-index:1;text-align:center;padding:2.6rem 0 1.6rem}
.kicker{font-family:var(--mono);font-size:.64rem;letter-spacing:.34em;color:#5fa8ff;text-transform:uppercase}
header h1{margin-top:.55rem;font-size:1.55rem;font-weight:800;letter-spacing:.04em;background:linear-gradient(90deg,#fff 20%,#9ec5ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.date-stamp{margin-top:.6rem;display:inline-flex;align-items:center;gap:.45rem;font-family:var(--mono);font-size:.68rem;letter-spacing:.16em;color:var(--muted)}
.date-stamp::before{content:"";width:6px;height:6px;border-radius:50%;background:#2ee6a6;box-shadow:0 0 8px #2ee6a6;animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.35}}
main{position:relative;z-index:1;display:flex;flex-direction:column;gap:1rem}
.card{position:relative;border-radius:16px;overflow:hidden;background:linear-gradient(180deg,rgba(150,180,255,.08),rgba(150,180,255,.03));border:1px solid rgba(150,180,255,.16);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);box-shadow:0 10px 34px rgba(0,0,0,.45)}
.card::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:var(--c);box-shadow:0 0 14px var(--c)}
.card-head{display:flex;align-items:center;justify-content:space-between;padding:.95rem 1.15rem .7rem}
.card-name{display:flex;align-items:center;gap:.6rem;font-size:1.05rem;font-weight:700}
.card-name::before{content:"";width:9px;height:9px;border-radius:50%;background:var(--c);box-shadow:0 0 10px var(--c)}
.card-badge{font-family:var(--mono);font-size:.58rem;letter-spacing:.12em;text-transform:uppercase;color:var(--c);border:1px solid color-mix(in srgb,var(--c) 45%,transparent);border-radius:999px;padding:.22rem .55rem}
.card-body{padding:.2rem 1.15rem 1.1rem;display:flex;flex-direction:column;gap:.5rem}
.combo{display:flex;align-items:center;gap:.38rem;flex-wrap:wrap}
.combo-label{font-family:var(--mono);font-size:.6rem;color:var(--muted);width:1.1rem;flex-shrink:0}
.ball{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;flex-shrink:0;font-variant-numeric:tabular-nums;color:#06101f;background:radial-gradient(circle at 35% 28%,color-mix(in srgb,var(--c) 60%,#fff),var(--c) 75%);box-shadow:0 0 14px color-mix(in srgb,var(--c) 55%,transparent),inset 0 1px 2px rgba(255,255,255,.5)}
.ball-d{font-size:.95rem}
.plus{color:var(--muted);font-size:.9rem;margin:0 .05rem}
.ball-s{background:radial-gradient(circle at 35% 28%,#ffe89a,#f0b429 75%);color:#3a2800;box-shadow:0 0 16px rgba(240,180,40,.7),inset 0 1px 2px rgba(255,255,255,.6)}
footer{position:relative;z-index:1;text-align:center;margin-top:2.2rem;padding:1.4rem;font-size:.66rem;line-height:1.9;color:#5c6788;font-family:var(--mono);letter-spacing:.04em}
"""

_HTML = """\
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{favicon}">
<title>台灣彩券 AI 預測 {date}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="kicker">Taiwan Lottery &middot; AI</div>
  <h1>台灣彩券 AI 預測</h1>
  <div class="date-stamp">{date}</div>
</header>
<main>
{cards}
</main>
<footer>
  由 Transformer ML 模型預測，僅供娛樂參考，不構成任何投注建議。
</footer>
</div>
</body>
</html>"""


@dataclass
class LotteryPrediction:
    lottery_type: str
    name: str
    method: str
    combos: list[list[int]]
    special: int | None = None


def _ball(value: str, kind: str) -> str:
    # kind: "n" normal / "d" digit-game / "s" special. Only .ball-d and .ball-s
    # have CSS overrides; "n" intentionally inherits the base .ball style.
    return f'<span class="ball ball-{kind}">{value}</span>'


def _combo_row(combo: list[int], special: int | None, idx: int, is_digit: bool) -> str:
    kind = "d" if is_digit else "n"
    # digit games (3d/4d) show bare single digits; number games zero-pad to 2 digits.
    fmt = "{:d}" if is_digit else "{:02d}"
    balls = "".join(_ball(fmt.format(n), kind) for n in combo)
    if special is not None:
        balls += '<span class="plus">+</span>' + _ball(f"{special:02d}", "s")
    return f'<div class="combo"><span class="combo-label">{idx:02d}</span>{balls}</div>'


def _card(pred: LotteryPrediction) -> str:
    accent = _ACCENT.get(pred.lottery_type, _ACCENT_FALLBACK)
    is_digit = pred.lottery_type in ("3d", "4d")
    rows = "\n      ".join(
        _combo_row(c, pred.special, i + 1, is_digit)
        for i, c in enumerate(pred.combos)
    )
    return (
        f'<div class="card" style="--c:{accent}">\n'
        f'  <div class="card-head">'
        f'<span class="card-name">{pred.name}</span>'
        f'<span class="card-badge">{pred.method}</span>'
        f'</div>\n'
        f'  <div class="card-body">\n'
        f"      {rows}\n"
        f"  </div>\n"
        f"</div>"
    )


def generate_html(predictions: list[LotteryPrediction], report_date: str) -> str:
    cards = "\n".join(_card(p) for p in predictions)
    return _HTML.format(date=report_date, css=_CSS, cards=cards, favicon=_FAVICON)


def write_report(
    predictions: list[LotteryPrediction],
    output_dir: Path,
    report_date: str | None = None,
) -> Path:
    if report_date is None:
        report_date = date.today().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    html = generate_html(predictions, report_date)
    index = output_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return index
