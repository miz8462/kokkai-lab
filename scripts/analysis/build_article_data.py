# scripts/analysis/build_article_data.py
#
# 【目的】
# 論点別の「議員の発言者数」と「政府の応答回数(答弁ブロック数)」を1つにまとめ、
# 記事のチャート(Nivo)に渡すJSONを作る。
# 議員と政府は単位が違う(人数と回数)ので、混ぜずに別のキーで持つ。
# 発言者が少ない論点は minor=true として、別枠表示用に印をつける。
# 政党別の発言者数も同梱する(議員のみ)。
#
# 【使い方】
# python scripts/analysis/build_article_data.py
# (先に issue_groups.py と answer_blocks.py を実行しておくこと)
#
# 【入力】 output/issue_groups.csv, output/answer_blocks_summary.csv
# 【出力】 data/article/issue_data.json

import json
import re
from pathlib import Path

import pandas as pd

ISSUES = "output/issue_groups.csv"
BLOCKS = "output/answer_blocks_summary.csv"
OUT = Path("data/article/issue_data.json")
MINOR_MAX_SPEAKERS = 5  # この人数以下の論点は別枠(暫定)

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
        "minor": int(r["議員の発言者"]) <= MINOR_MAX_SPEAKERS,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{len(items)}論点を {OUT} に書き出しました")
for it in items:
    print(f"{it['id']} {it['label']}: 議員{it['member']['speakers']}人 / 政府{it['gov']['responses']}回")
