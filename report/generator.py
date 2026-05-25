from dataclasses import dataclass
from datetime import date
from pathlib import Path

_CSS = """\
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f7fa;color:#1a1a2e}
header{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:2rem;text-align:center}
header h1{font-size:1.8rem;font-weight:700;letter-spacing:.05em}
header p{margin-top:.5rem;opacity:.7;font-size:.9rem}
main{max-width:860px;margin:2rem auto;padding:0 1rem;display:grid;gap:1.5rem}
.card{background:#fff;border-radius:16px;padding:1.5rem;box-shadow:0 2px 12px rgba(0,0,0,.08)}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem}
.card-title{font-size:1.1rem;font-weight:700}
.badge{font-size:.7rem;font-weight:600;padding:.2rem .6rem;border-radius:20px}
.badge-ml{background:#e8f5e9;color:#2e7d32}
.badge-freq{background:#e3f2fd;color:#1565c0}
.combo{display:flex;align-items:center;gap:.45rem;margin-bottom:.7rem;flex-wrap:wrap}
.combo-label{font-size:.8rem;color:#999;width:3.5rem;flex-shrink:0}
.ball{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;flex-shrink:0}
.ball-n{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
.ball-s{background:linear-gradient(135deg,#f093fb,#f5576c);color:#fff}
.ball-d{background:linear-gradient(135deg,#4facfe,#00f2fe);color:#fff;font-size:1.1rem}
.plus{font-weight:700;color:#ccc;margin:0 .1rem}
footer{text-align:center;padding:2rem;color:#bbb;font-size:.78rem;line-height:1.8}
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
  <p>{date}</p>
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


def _ball(n: int, kind: str) -> str:
    return f'<span class="ball ball-{kind}">{n}</span>'


def _combo_row(combo: list[int], special: int | None, idx: int, is_digit: bool) -> str:
    kind = "d" if is_digit else "n"
    balls = "".join(_ball(n, kind) for n in combo)
    if special is not None:
        balls += '<span class="plus">+</span>' + _ball(special, "s")
    return f'<div class="combo"><span class="combo-label">組合 {idx}</span>{balls}</div>'


def _card(pred: LotteryPrediction) -> str:
    badge = "badge-ml" if pred.method == "ML" else "badge-freq"
    is_digit = pred.lottery_type in ("3d", "4d")
    rows = "\n".join(
        _combo_row(c, pred.special, i + 1, is_digit)
        for i, c in enumerate(pred.combos)
    )
    return (
        f'<div class="card">\n'
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
