"""
read_issue.py — 論点グループの該当段落を、読みやすいMarkdownにするスクリプト

目的:
  論点グループ(例: A 食料品ゼロの範囲)に入る段落を、日付ごとに
  「議員」と「政府」に分け、政党・発言者・前後の段落つきで出力する。
  論点の内部の対立(どの対策を選ぶか)を、手で読んで整理するための素材にする。

使い方:
  python scripts/analysis/read_issue.py A            # 前後1段落
  python scripts/analysis/read_issue.py C 2          # 前後2段落
  python scripts/analysis/read_issue.py E 1 インボイス  # 語を1つに絞る

入力:
  data/interim/paragraphs_clean.csv
  data/issues/issue_groups.json
出力:
  output/issue_<論点ID>.md
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PARAS = ROOT / "data/interim/paragraphs_clean.csv"
GROUPS = ROOT / "data/issues/issue_groups.json"

gid = sys.argv[1]
n_ctx = int(sys.argv[2]) if len(sys.argv) > 2 else 1
only_term = sys.argv[3] if len(sys.argv) > 3 else None

raw = json.load(open(GROUPS, encoding="utf-8"))
key = next(k for k in raw if k == gid or k.split()[0] == gid)
val = raw[key]
terms = (val.get("terms") or val.get("words") or []) if isinstance(val, dict) else val
if only_term:
    terms = [only_term]

df = pd.read_csv(PARAS)
df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
df["text"] = df["text"].fillna("")
df["party"] = df["party"].fillna("")
has_kw = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
by_pos = {(r.speechID, r.para_id): r for r in df.itertuples()}

hits = df[has_kw & (df["role"] != "委員長報告") & (~df["exclude"])].copy()
hits["matched"] = hits["text"].apply(lambda s: [t for t in terms if t in s])
hits = hits[hits["matched"].str.len() > 0]


def render(r, mark=False):
    who = f"{r.speaker}({r.party or r.speakerPosition or r.role})"
    head = f"**{who}**" if mark else f"{who}"
    return f"{head}: {r.text}"


lines = [f"# 論点 {key}(語: {' / '.join(terms)})", f"該当 {len(hits)} 段落\n"]
for date, day in hits.sort_values(["date", "speechID", "para_id"]).groupby("date"):
    lines.append(f"## {date}")
    for label, roles in [("議員", ["議員"]), ("政府", ["政府", "議長"])]:
        part = day[day["role"].isin(roles)]
        if part.empty:
            continue
        lines.append(f"### {label}({len(part)}段落)")
        for r in part.itertuples():
            matched = [str(t) for t in r.matched]  # pyright: ignore
            lines.append(f"- 一致語: {', '.join(matched)}")

            for off in range(-n_ctx, n_ctx + 1):
                p = by_pos.get((str(r.speechID), int(r.para_id) + off))  # pyright: ignore
                if p is None:
                    continue
                lines.append(("  - ▶ " if off == 0 else "  - ") + render(p, off == 0))
            lines.append("")

out = ROOT / f"output/issue_{gid}.md"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines), encoding="utf-8")
print(f"{out} に書き出しました({len(hits)}段落)")
