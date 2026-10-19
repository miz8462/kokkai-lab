"""
【目的】
分析対象の slug (テーマ識別子) から各パイプライン工程で利用するデータ・出力先パスを組み立てる共通部品、
および keyword や検索条件を定義した設定ファイル (config/<slug>.json) を読み込む機能を提供する。
"""

from pathlib import Path
import json
from typing import Any

# プロジェクトルートディレクトリ (scripts/ の1つ上)
BASE: Path = Path(__file__).resolve().parent.parent


def paths(slug: str) -> dict[str, Path]:
    """slug に基づき、各工程のデータ・出力ファイルのパスを辞書で返す。

    Returns:
        dict[str, Path]:
            - raw     : data/raw/<slug>
            - interim : data/interim/<slug>
            - output  : output/<slug>
            - groups  : data/issues/<slug>.json
            - article : data/article/<slug>.json
    """
    return {
        "raw": BASE / "data" / "raw" / slug,
        "interim": BASE / "data" / "interim" / slug,
        "output": BASE / "output" / slug,
        "groups": BASE / "data" / "issues" / f"{slug}.json",
        "article": BASE / "data" / "article" / f"{slug}.json",
    }


def load_config(slug: str) -> dict[str, Any]:
    """config/<slug>.json を読み込んで辞書形式で返す。

    Args:
        slug: 設定ファイル名に対応するスラッグ

    Returns:
        dict[str, Any]: 設定内容を格納した辞書

    Raises:
        FileNotFoundError: 設定ファイルが存在しない場合
    """
    config_file = BASE / "config" / f"{slug}.json"
    if not config_file.is_file():
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {config_file} (slug: {slug})"
        )

    with config_file.open("r", encoding="utf-8") as f:
        data: Any = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"設定ファイルの形式が不正です（辞書形式が期待されます）: {config_file}"
        )

    return data
