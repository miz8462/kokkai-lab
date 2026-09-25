"""
年別・政党別の集計を行うスクリプト。

入力: data/interim/speeches_extracted.csv, data/interim/tokens.csv
出力: data/interim/
  - speech_count_by_party.csv   (政党別発言数)
  - word_freq_by_party.csv      (政党別頻出語トップ30)
  - word_freq_by_year.csv       (年別頻出語トップ30)
"""
import sys
from pathlib import Path

import pandas as pd

# count_words.py は scripts/analysis/ にあるため、パスを追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))
from count_words import STOPWORDS

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INTERIM_DIR = BASE_DIR / "data" / "interim"
EXTRACTED = INTERIM_DIR / "speeches_extracted.csv"
TOKENS = INTERIM_DIR / "tokens.csv"


def main():
    speeches = pd.read_csv(EXTRACTED)
    tokens = pd.read_csv(TOKENS)

    # ストップワード除外
    words = tokens.loc[:, "word"]
    tokens = tokens.loc[~words.isin(list(STOPWORDS))]

    # 政党別発言数
    speech_count = speeches.loc[:, "party"].value_counts().reset_index()
    speech_count.columns = ["party", "count"]
    speech_count.to_csv(INTERIM_DIR / "speech_count_by_party.csv", index=False, encoding="utf-8")

    # 政党別頻出語 (各政党トップ30)
    by_party = tokens.groupby(["party", "word"]).size().reset_index()
    by_party.columns = ["party", "word", "count"]
    by_party = by_party.sort_values(["party", "count"], ascending=[True, False])
    by_party = by_party.groupby("party").head(30)
    by_party.to_csv(INTERIM_DIR / "word_freq_by_party.csv", index=False, encoding="utf-8")

    # 年別頻出語 (各年トップ30)
    tokens["year"] = tokens.loc[:, "date"].str[:4].astype(int)
    by_year = tokens.groupby(["year", "word"]).size().reset_index()
    by_year.columns = ["year", "word", "count"]
    by_year = by_year.sort_values(["year", "count"], ascending=[True, False])
    by_year = by_year.groupby("year").head(30)
    by_year.to_csv(INTERIM_DIR / "word_freq_by_year.csv", index=False, encoding="utf-8")

    print("=== 政党別発言数 ===")
    print(speech_count.to_string(index=False))
    print()
    print("=== 政党別頻出語トップ5 ===")
    print(by_party.groupby("party").head(5).to_string(index=False))
    print()
    print("=== 年別頻出語トップ5 ===")
    print(by_year.groupby("year").head(5).to_string(index=False))


if __name__ == "__main__":
    main()
