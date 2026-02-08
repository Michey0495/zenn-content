"""
ネタ管理スクリプト

10日分のネタストックを管理し、投稿済みネタを追跡する。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATA_DIR, TOPIC_STOCK_MIN
from analyze_history import analyze


def load_topics() -> list[dict[str, Any]]:
    """ネタストックを読み込む"""
    topics_file = DATA_DIR / "topics.json"
    if not topics_file.exists():
        return []

    with open(topics_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_topics(topics: list[dict[str, Any]]) -> None:
    """ネタストックを保存する"""
    DATA_DIR.mkdir(exist_ok=True)
    topics_file = DATA_DIR / "topics.json"

    with open(topics_file, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)


def load_posted_topics() -> list[dict[str, Any]]:
    """投稿済みネタを読み込む"""
    posted_file = DATA_DIR / "posted_topics.json"
    if not posted_file.exists():
        return []

    with open(posted_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_posted_topic(topic: dict[str, Any]) -> None:
    """投稿済みネタを追加する"""
    DATA_DIR.mkdir(exist_ok=True)
    posted_file = DATA_DIR / "posted_topics.json"

    posted = load_posted_topics()
    topic["posted_at"] = datetime.now().isoformat()
    posted.append(topic)

    with open(posted_file, 'w', encoding='utf-8') as f:
        json.dump(posted, f, ensure_ascii=False, indent=2)


def is_already_posted(title: str) -> bool:
    """すでに投稿済みか確認する"""
    posted = load_posted_topics()
    posted_titles = {p.get("title", "").lower() for p in posted}
    return title.lower() in posted_titles


def add_manual_topic(
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    priority: int = 5
) -> dict[str, Any]:
    """手動でネタを追加する"""
    topic = {
        "type": "manual",
        "title": title,
        "description": description,
        "source": "手動追加",
        "priority": priority,
        "tags": tags or ["claudecode"],
        "added_at": datetime.now().isoformat(),
    }

    topics = load_topics()
    topics.append(topic)
    save_topics(topics)

    return topic


def refresh_topics() -> list[dict[str, Any]]:
    """ネタストックを更新する（履歴から新規抽出）"""
    current_topics = load_topics()
    current_titles = {t.get("title", "").lower() for t in current_topics}

    # 履歴から新規ネタを抽出
    analysis = analyze()
    new_candidates = analysis.get("candidates", [])

    added = 0
    for candidate in new_candidates:
        title = candidate.get("title", "")
        # 重複チェック
        if title.lower() not in current_titles and not is_already_posted(title):
            candidate["added_at"] = datetime.now().isoformat()
            current_topics.append(candidate)
            current_titles.add(title.lower())
            added += 1

    save_topics(current_topics)
    print(f"✅ {added}件の新規ネタを追加")

    return current_topics


def get_next_topic() -> dict[str, Any] | None:
    """次に投稿するネタを取得する"""
    topics = load_topics()

    # 未投稿で優先度が高い順
    available = [t for t in topics if not is_already_posted(t.get("title", ""))]

    if not available:
        return None

    # 優先度でソート
    available.sort(key=lambda x: -x.get("priority", 0))

    return available[0]


def mark_as_posted(title: str) -> None:
    """ネタを投稿済みとしてマークする"""
    topics = load_topics()

    for topic in topics:
        if topic.get("title") == title:
            save_posted_topic(topic)
            break

    # ストックから削除
    topics = [t for t in topics if t.get("title") != title]
    save_topics(topics)


def get_stock_status() -> dict[str, Any]:
    """ネタストックの状態を取得する"""
    topics = load_topics()
    posted = load_posted_topics()

    available = [t for t in topics if not is_already_posted(t.get("title", ""))]

    return {
        "total_stock": len(topics),
        "available": len(available),
        "posted_count": len(posted),
        "needs_refresh": len(available) < TOPIC_STOCK_MIN,
        "topics": available[:5],  # 上位5件
    }


def ensure_minimum_stock() -> None:
    """最低限のネタストックを確保する"""
    status = get_stock_status()

    if status["needs_refresh"]:
        print(f"⚠️ ネタが{status['available']}件しかありません。補充します...")
        refresh_topics()

        # 再確認
        new_status = get_stock_status()
        if new_status["available"] < TOPIC_STOCK_MIN:
            print("📝 自動抽出だけでは足りません。手動でネタを追加してください。")
            # デフォルトのネタを追加
            default_topics = [
                "Claude Code MAXプランを1週間使ってわかったこと",
                "Claude Codeの履歴ファイルを活用する方法",
                "/insightsコマンドで使い方を改善する",
                "Claude Codeのセッション管理術",
                "MCP連携でGoogleドライブを操作する",
            ]
            for title in default_topics:
                if not is_already_posted(title):
                    add_manual_topic(title)


if __name__ == "__main__":
    print("📦 ネタストック状況")
    status = get_stock_status()
    print(f"  - 総ストック: {status['total_stock']}件")
    print(f"  - 利用可能: {status['available']}件")
    print(f"  - 投稿済み: {status['posted_count']}件")

    if status["needs_refresh"]:
        print("\n🔄 ネタを補充中...")
        ensure_minimum_stock()

    print("\n📝 次の候補:")
    for i, t in enumerate(status["topics"], 1):
        print(f"  {i}. {t.get('title')}")
