from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Accent color and ball gradient per lottery type
_ACCENT: dict[str, str] = {
    "539": "#10b981",
    "649": "#3b82f6",
    "638": "#f97316",
    "3d":  "#8b5cf6",
    "4d":  "#ec4899",
}
_BALL_GRAD: dict[str, str] = {
    "539": "linear-gradient(135deg,#34d399,#059669)",
    "649": "linear-gradient(135deg,#60a5fa,#2563eb)",
    "638": "linear-gradient(135deg,#fb923c,#ea580c)",
    "3d":  "linear-gradient(135deg,#a78bfa,#7c3aed)",
    "4d":  "linear-gradient(135deg,#f472b6,#db2777)",
}

_CSS = """\
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans TC',sans-serif;background:#f1f5f9;color:#0f172a;min-height:100vh}
header{background:linear-gradient(160deg,#0f172a 0%,#1e293b 60%,#0f172a 100%);color:#fff;padding:3.5rem 1.5rem;text-align:center;position:relative;overflow:hidden}
header::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% -20%,rgba(99,102,241,.35) 0%,transparent 65%);pointer-events:none}
header h1{font-size:2rem;font-weight:800;letter-spacing:.04em;position:relative}
header .tagline{margin-top:.5rem;opacity:.55;font-size:.88rem;position:relative}
header .date-pill{display:inline-block;margin-top:1.2rem;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:.38rem 1.1rem;font-size:.82rem;font-weight:600;letter-spacing:.06em;position:relative}
main{max-width:940px;margin:2.5rem auto;padding:0 1.25rem;display:grid;gap:1.25rem}
@media(min-width:600px){main{grid-template-columns:1fr 1fr}}
.card{background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06),0 6px 24px rgba(0,0,0,.07);transition:transform .18s ease,box-shadow .18s ease}
.card:hover{transform:translateY(-3px);box-shadow:0 4px 8px rgba(0,0,0,.08),0 16px 40px rgba(0,0,0,.12)}
.card-stripe{height:5px}
.card-body{padding:1.4rem}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem}
.card-title{font-size:1.05rem;font-weight:700}
.badge{font-size:.68rem;font-weight:700;padding:.25rem .7rem;border-radius:999px;letter-spacing:.04em}
.badge-ml{background:#dcfce7;color:#15803d}
.badge-freq{background:#dbeafe;color:#1d4ed8}
.combo{display:flex;align-items:center;gap:.42rem;margin-bottom:.8rem;flex-wrap:wrap}
.combo:last-child{margin-bottom:0}
.combo-label{font-size:.72rem;color:#94a3b8;width:3rem;flex-shrink:0;font-weight:500}
.ball{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.83rem;flex-shrink:0;color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.22)}
.ball-n,.ball-d{background:linear-gradient(135deg,#94a3b8,#64748b)}
.ball-s{background:linear-gradient(135deg,#fb7185,#e11d48)}
.ball-d{font-size:.95rem}
.plus{font-weight:700;color:#cbd5e1;margin:0 .18rem;font-size:1.1rem}
footer{text-align:center;padding:3rem 1.5rem 4rem;color:#94a3b8;font-size:.77rem;line-height:2.2}
"""

_HTML = """\
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>台灣彩券 AI 預測 {date}</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>台灣彩券 AI 預測</h1>
  <p class="tagline">Transformer model · Updated daily</p>
  <div class="date-pill">{date}</div>
</header>
<main>
{cards}
</main>
<footer>
  由 Transformer ML 模型預測，僅供娛樂參考，不構成任何投注建議。<br>
  Generated on {date}
</footer>
</body>
</html>"""


@dataclass
class LotteryPrediction:
    lottery_type: str
    name: str
    method: str
    combos: list[list[int]]
    special: int | None = None


def _ball(n: int, kind: str, grad: str = "") -> str:
    style = f' style="background:{grad}"' if grad else ""
    return f'<span class="ball ball-{kind}"{style}>{n:02d}</span>'


def _combo_row(
    combo: list[int], special: int | None, idx: int, is_digit: bool, grad: str
) -> str:
    kind = "d" if is_digit else "n"
    fmt = "{:d}" if is_digit else "{:02d}"
    balls = "".join(
        f'<span class="ball ball-{kind}" style="background:{grad}">{fmt.format(n)}</span>'
        for n in combo
    )
    if special is not None:
        balls += '<span class="plus">+</span>' + _ball(special, "s")
    return f'<div class="combo"><span class="combo-label">#{idx}</span>{balls}</div>'


def _card(pred: LotteryPrediction) -> str:
    accent = _ACCENT.get(pred.lottery_type, "#6366f1")
    grad = _BALL_GRAD.get(pred.lottery_type, "linear-gradient(135deg,#818cf8,#6366f1)")
    badge = "badge-ml" if pred.method == "ML" else "badge-freq"
    is_digit = pred.lottery_type in ("3d", "4d")
    rows = "\n    ".join(
        _combo_row(c, pred.special, i + 1, is_digit, grad)
        for i, c in enumerate(pred.combos)
    )
    return (
        f'<div class="card">\n'
        f'  <div class="card-stripe" style="background:{accent}"></div>\n'
        f'  <div class="card-body">\n'
        f'    <div class="card-header">'
        f'<span class="card-title">{pred.name}</span>'
        f'<span class="badge {badge}">{pred.method}</span>'
        f'</div>\n'
        f"    {rows}\n"
        f"  </div>\n"
        f"</div>"
    )


def generate_html(predictions: list[LotteryPrediction], report_date: str) -> str:
    cards = "\n".join(_card(p) for p in predictions)
    return _HTML.format(date=report_date, css=_CSS, cards=cards)


def write_report(
    predictions: list[LotteryPrediction],
    output_dir: Path,
    report_date: str | None = None,
) -> tuple[Path, Path]:
    if report_date is None:
        report_date = date.today().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    html = generate_html(predictions, report_date)
    dated = output_dir / f"{report_date}.html"
    index = output_dir / "index.html"
    dated.write_text(html, encoding="utf-8")
    index.write_text(html, encoding="utf-8")
    return dated, index
