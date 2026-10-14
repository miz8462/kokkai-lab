"""
【目的】
論点別の「議員の発言者数」と「政府の応答回数(答弁ブロック数)」を1つにまとめ、
記事のチャート(Nivo)に渡すJSONを作る。
議員と政府は単位が違う(人数と回数)ので、混ぜずに別のキーで持つ。
政党別の発言者数も同梱する(議員のみ)。

【使い方】
python scripts/analysis/build_article_data.py
(先に issue_groups.py と answer_blocks.py を実行しておくこと)

【入力】 output/issue_groups.csv, output/answer_blocks_summary.csv
【出力】 data/article/issue_data.json
"""

import json
import re
from pathlib import Path

import pandas as pd

ISSUES = "output/issue_groups.csv"
BLOCKS = "output/answer_blocks_summary.csv"
OUT = Path("data/article/issue_data.json")

issues = pd.read_csv(ISSUES)
blocks = pd.read_csv(BLOCKS).set_index("論点")

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
