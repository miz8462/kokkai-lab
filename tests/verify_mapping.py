import json
import sys
from collections import Counter
from pathlib import Path
from typing import cast

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from party_mapping import PARTY_MAPPING, normalize_party


def load_speeches(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return cast(list[dict[str, str]], json.load(f))


speeches = load_speeches(BASE_DIR / "data" / "raw" / "speeches_20260925.json")

groups = Counter(s["speakerGroup"] for s in speeches)

print("=== 会派名 -> 正規化後の政党名 ===")
unmapped: list[str] = []
for group, count in sorted(groups.items()):
    normalized = normalize_party(group)
    flag = "" if group in PARTY_MAPPING else "  ← 未登録"
    print(f"{group} ({count}件) -> {normalized}{flag}")
    if group not in PARTY_MAPPING:
        unmapped.append(group)

print("\n=== 集計結果 ===")
print(f"会派の種類: {len(groups)}")
print(f"未登録の会派名: {len(unmapped)}")
if unmapped:
    for g in unmapped:
        print(f" - {g} ({groups[g]}件)")

# 正規化後の政党別件数も確認しておく
print("\n=== 正規化後の政党別件数 ===")
party_counts = Counter(normalize_party(g) for g in [s["speakerGroup"] for s in speeches])
for party, count in party_counts.most_common():
    print(f"{party}: {count}件")