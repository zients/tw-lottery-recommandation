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
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans TC',sans-serif;background:#f5f5f0;color:#111;min-height:100vh}
header{background:#111;color:#fff;padding:2.5rem 1.5rem 2rem;text-align:center}
header h1{font-size:1.5rem;font-weight:900;letter-spacing:.18em;text-transform:uppercase}
header .date-stamp{margin-top:.75rem;font-size:.72rem;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.4)}
main{max-width:680px;margin:2rem auto;padding:0 1.25rem;display:flex;flex-direction:column;gap:.75rem}
.card{background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.card-band{padding:.85rem 1.25rem;display:flex;align-items:center;justify-content:space-between}
.card-band-title{color:#fff;font-size:.95rem;font-weight:700;letter-spacing:.02em}
.card-band-badge{color:rgba(255,255,255,.65);font-size:.62rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase}
.card-body{padding:1.1rem 1.25rem 1.25rem}
.combo{display:flex;align-items:center;gap:.35rem;margin-bottom:.65rem;flex-wrap:wrap}
.combo:last-child{margin-bottom:0}
.combo-label{font-size:.65rem;color:#c8c8c8;width:1.2rem;flex-shrink:0;text-align:center;font-variant-numeric:tabular-nums}
.ball{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.88rem;flex-shrink:0;color:#fff}
.ball-n,.ball-d{background:#bbb}
.ball-s{background:#fff;border:2.5px solid #b8962e;color:#b8962e;font-weight:800}
.ball-d{font-size:.94rem}
.plus{color:#ddd;margin:0 .1rem;font-size:.85rem}
footer{text-align:center;padding:2.5rem 1.5rem;color:#bbb;font-size:.72rem;letter-spacing:.02em;line-height:2;margin-top:.5rem}
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
    badge_text = pred.method
    is_digit = pred.lottery_type in ("3d", "4d")
    rows = "\n    ".join(
        _combo_row(c, pred.special, i + 1, is_digit, accent)
        for i, c in enumerate(pred.combos)
    )
    return (
        f'<div class="card">\n'
        f'  <div class="card-band" style="background:{accent}">'
        f'<span class="card-band-title">{pred.name}</span>'
        f'<span class="card-band-badge">{badge_text}</span>'
        f'</div>\n'
        f'  <div class="card-body">\n'
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
