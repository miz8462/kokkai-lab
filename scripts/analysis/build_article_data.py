"""
【目的】
論点別の「議員の発言者数」と「政府の応答回数(答弁ブロック数)」を1つにまとめ、
記事のチャート(Nivo)に渡すJSONを作る。
議員と政府は単位が違う(人数と回数)ので、混ぜずに別のキーで持つ。
政党別の発言者数も同梱する(議員のみ)。

【使い方】
python scripts/analysis/build_article_data.py
(先に issue_groups.py と answer_blocks.py を実行しておくこと)

【入力】 output/consumption-tax-issues/issue_groups.csv, output/consumption-tax-issues/answer_blocks_summary.csv
【出力】 data/article/consumption-tax-issues.json
"""

import json
import re
from pathlib import Path

import pandas as pd

ISSUES = "output/consumption-tax-issues/issue_groups.csv"
BLOCKS = "output/consumption-tax-issues/answer_blocks_summary.csv"
OUT = Path("data/article/consumption-tax-issues.json")
PARAGRAPHS = "data/interim/consumption-tax-issues/paragraphs_clean.csv"
GROUPS = "data/issues/consumption-tax-issues.json"

issues = pd.read_csv(ISSUES)
blocks = pd.read_csv(BLOCKS).set_index("論点")

# 政党別の発言者名リストを paragraphs_clean.csv から集計
df_p = pd.read_csv(PARAGRAPHS)
df_p["exclude"] = df_p["exclude"].astype(str).str.lower().isin(["true", "1"])
df_p["kw_extended"] = df_p["kw_extended"].astype(str).str.lower().isin(["true", "1"])
df_p = df_p[df_p["kw_extended"] & (df_p["role"] != "委員長報告") & (~df_p["exclude"])].copy()

with open(GROUPS, encoding="utf-8") as f:
    groups = json.load(f)

speakers_map = {}
for g_name, words in groups.items():
    g_id, _, _ = g_name.partition(" ")
    pattern = "|".join(words)
    sub = df_p[df_p["text"].str.contains(pattern, na=False, regex=True)]
    mem = sub[sub["role"] == "議員"]
    parties_speakers = {}
    for party, grp in mem.groupby("party"):
        parties_speakers[party] = grp["speaker"].value_counts().index.tolist()
    speakers_map[g_id] = parties_speakers

items = []
for _, r in issues.iterrows():
    name = r["論点"]
    issue_id, _, label = name.partition(" ")
    parties = {}
    for m in re.finditer(r"(\S+?)(\d+)(?:\s|$)", str(r["政党別の発言者数"])):
        parties[m.group(1)] = int(m.group(2))
    b = blocks.loc[name] if name in blocks.index else None
    items.append({
        "id": issue_id,
        "label": label or issue_id,
        "member": {
            "speakers": int(r["議員の発言者"]),
            "paragraphs": int(r["議員段落"]),
            "top_speaker": r["議員の最多"],
            "top_share": float(r["最多の割合"]),
            "parties": parties,
            "party_speakers": speakers_map.get(issue_id, {}),
        },
        "gov": {
            "responses": int(b["答弁ブロック"]) if b is not None else 0,
            "paragraphs": int(r["政府段落"]),
        },
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "source": "国会会議録検索システム(国立国会図書館) 直近1年の本会議における発言。「消費税」「消費減税」「給付つき(付き)税額控除」のいずれかを含む段落294件(委員長報告・議長の議事進行・同一演説の再掲を除く)を集計",
    "note": "論点は、議論の中に出てきた語の組み合わせによる独自の分類。1つの段落が複数の論点に入るため、論点間の合計はできない。政府の応答回数は、見出し文(「〜についてお尋ねがありました」)で区切った答弁のうち、その論点の語を含むものの数",
    "issues": items,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{len(items)}論点を {OUT} に書き出しました")
for it in items:
    print(f"{it['id']} {it['label']}: 議員{it['member']['speakers']}人 / 政府{it['gov']['responses']}回")
