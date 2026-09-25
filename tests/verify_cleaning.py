import json
import sys
from pathlib import Path
from typing import cast

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from clean_speech import clean_speech


def load_speeches(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return cast(list[dict[str, str]], json.load(f))


speeches = load_speeches(BASE_DIR / "data" / "raw" / "speeches_20260925.json")

print(f"件数: {len(speeches)}\n")

# 除去前後の冒頭・末尾を突き合わせて表示
print("=== 冒頭・末尾の除去確認(先頭5件) ===")
for s in speeches[:5]:
    before = s["speech"].replace("\r\n", " ")
    after = clean_speech(s["speech"])
    print(f"--- {s['speaker']}({s['speakerGroup']}) ---")
    print(f"[前 冒頭] {before[:60]}")
    print(f"[後 冒頭] {after[:60]}")
    print(f"[前 末尾] {before[-60:]}")
    print(f"[後 末尾] {after[-60:]}")
    print()

# 除去し残しの検出:除去後もノイズらしき文字列が末尾に残っていないかチェック
# (本文中の正当な言及を拾わないよう、末尾のみを対象にする)
suspect_patterns = ["○", "御清聴", "〔", "〕", "残余の質問", "以上、御報告申し上げます", "─", "―"]

print("=== 除去し残しチェック(末尾40文字) ===")
flagged: list[tuple[str, str, list[str]]] = []
for s in speeches:
    after = clean_speech(s["speech"])
    tail = after[-40:]
    hits = [p for p in suspect_patterns if p in tail]
    if hits:
        flagged.append((s["speaker"], s["speechID"], hits))
        
if flagged:
    for speaker, sid, hits in flagged:
        print(f" - {speaker} ({sid}): 残存パターン {hits}")
else:
    print("除去し残しなし。")

print(f"\n除去し残しのある発言数: {len(flagged)} / {len(speeches)}")

# 文字数の変化を確認(異常に短くなった/変化がない発言がないか)
print("\n=== 文字数変化の確認 ===")
no_change: list[str] = []
too_much_removed: list[tuple[str, int, int]] = []
for s in speeches:
    before_len = len(s["speech"])
    after_len = len(clean_speech(s["speech"]))
    diff = before_len - after_len
    if diff == 0:
        no_change.append(s["speaker"])
    if before_len > 0 and diff / before_len > 0.5:
        too_much_removed.append((s["speaker"], before_len, after_len))

print(f"除去による変化が全くない発言: {len(no_change)}件 {no_change[:10]}")
print(f"半分以上削られた発言(異常の疑い): {len(too_much_removed)}件")
for speaker, b, a in too_much_removed[:10]:
    print(f"  - {speaker}: {b}文字 → {a}文字")
