import json
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
path = max((BASE_DIR / "data" / "raw").glob("speeches_*.json"))
with path.open(encoding="utf-8") as f:
    records = json.load(f)

print(f"ファイル: {path}")
print(f"件数: {len(records)}")
print()

groups = Counter(r.get("speakerGroup", "(なし)") for r in records)
print("所属会派の内訳:")
for group, count in groups.most_common():
    print(f"  {group}: {count}")

print()
print("発言文字数の分布:")
lengths = [len(r.get("speech", "")) for r in records]
print(f"  最小: {min(lengths)}  最大: {max(lengths)}  平均: {sum(lengths)/len(lengths):.0f}")
