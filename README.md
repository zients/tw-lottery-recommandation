# tw-lottery-recommandation

台灣彩券開獎資料分析與號碼推薦工具，支援多種彩券。

資料來源：[台灣彩券官方 API](https://api.taiwanlottery.com)

## 支援彩種

| `--type` | 彩種 | 玩法 |
|----------|------|------|
| `539` | 今彩539 | 5 球，1-39 |
| `649` | 大樂透 | 6 球，1-49 |
| `638` | 威力彩 | 6 球（1-38）+ 特別號（1-8） |
| `3d` | 3星彩 | 3 位數，0-9 |
| `4d` | 4星彩 | 4 位數，0-9 |

## 安裝

```bash
uv sync
```

## 使用方式

### 更新資料

```bash
uv run lottery update --type 539              # DB 有資料則繼續，沒有則從最早期數開始
uv run lottery update --type 649 --from-month 2024-01  # 指定起始月份
```

### 統計分析

```bash
uv run lottery stats --type 539
```

輸出：
- 全期號碼頻率 Top 10
- 近 30 期熱號 / 冷號
- 638 額外顯示特別號頻率 Top 5

### 號碼推薦

```bash
uv run lottery recommend --type 638
```

輸出 3 組推薦號碼，依據：
- 歷史頻率（取 Top 20 候選）
- 奇偶比與總和範圍過濾（539 / 649 / 638）
- 638 附帶特別號推薦

### 執行測試

```bash
uv run pytest
```

## License

MIT
