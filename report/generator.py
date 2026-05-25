from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Flat solid color per lottery type (accent = left border, ball fill)
_ACCENT: dict[str, str] = {
    "539": "#059669",
    "649": "#2563eb",
    "638": "#ea580c",
    "3d":  "#7c3aed",
    "4d":  "#db2777",
}

_CSS = """\
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans TC',sans-serif;background:#faf8f4;color:#111;min-height:100vh}
header{background:#111;color:#fff;padding:2.8rem 1.5rem;text-align:center}
header h1{font-size:1.75rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase}
header .date-stamp{display:inline-block;margin-top:1rem;border:1px solid rgba(255,255,255,.25);padding:.3rem 1rem;font-size:.72rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.5)}
main{max-width:720px;margin:2.5rem auto;padding:0 1.25rem;display:flex;flex-direction:column;gap:1rem}
.card{background:#fff;border-radius:6px;border-left:5px solid #ccc;padding:1.4rem 1.4rem 1.4rem 1.25rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem}
.card-title{font-size:1rem;font-weight:700;letter-spacing:.01em}
.badge{font-size:.62rem;font-weight:700;padding:.18rem .55rem;border-radius:3px;letter-spacing:.08em;text-transform:uppercase}
.badge-ml{background:#111;color:#fff}
.badge-freq{background:#e8e8e8;color:#555}
.combo{display:flex;align-items:center;gap:.38rem;margin-bottom:.75rem;flex-wrap:wrap}
.combo:last-child{margin-bottom:0}
.combo-label{font-size:.68rem;color:#ccc;width:1.4rem;flex-shrink:0;text-align:right;font-variant-numeric:tabular-nums}
.ball{width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.86rem;flex-shrink:0;color:#fff}
.ball-n,.ball-d{background:#aaa}
.ball-s{background:#faf8f4;border:2.5px solid #c9a84c;color:#c9a84c;font-weight:800}
.ball-d{font-size:.92rem}
.plus{color:#ddd;margin:0 .12rem;font-size:.9rem}
footer{text-align:center;padding:3rem 1.5rem;color:#ccc;font-size:.74rem;line-height:2;border-top:1px solid #ede9e3;margin-top:1.5rem}
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
  <div class="date-stamp">{date}</div>
</header>
<main>
{cards}
</main>
<footer>
  由 Transformer ML 模型預測，僅供娛樂參考，不構成任何投注建議。
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


def _ball(n: int, kind: str, color: str = "") -> str:
    style = f' style="background:{color}"' if color else ""
    return f'<span class="ball ball-{kind}"{style}>{n:02d}</span>'


def _combo_row(
    combo: list[int], special: int | None, idx: int, is_digit: bool, color: str
) -> str:
    kind = "d" if is_digit else "n"
    fmt = "{:d}" if is_digit else "{:02d}"
    balls = "".join(
        f'<span class="ball ball-{kind}" style="background:{color}">{fmt.format(n)}</span>'
        for n in combo
    )
    if special is not None:
        balls += '<span class="plus">+</span>' + _ball(special, "s")
    return f'<div class="combo"><span class="combo-label">{idx}</span>{balls}</div>'


def _card(pred: LotteryPrediction) -> str:
    accent = _ACCENT.get(pred.lottery_type, "#6366f1")
    badge = "badge-ml" if pred.method == "ML" else "badge-freq"
    is_digit = pred.lottery_type in ("3d", "4d")
    rows = "\n    ".join(
        _combo_row(c, pred.special, i + 1, is_digit, accent)
        for i, c in enumerate(pred.combos)
    )
    return (
        f'<div class="card" style="border-left-color:{accent}">\n'
        f'  <div class="card-header">'
        f'<span class="card-title">{pred.name}</span>'
        f'<span class="badge {badge}">{pred.method}</span>'
        f'</div>\n'
        f"  {rows}\n"
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
