#!/usr/bin/env python3
"""
Zenn自動投稿システム - 日次実行スクリプト

毎日0:00に実行され、以下を行う:
1. Claude Code履歴を分析
2. ネタストックを確認・補充
3. 記事を生成
4. Zennに投稿（git push）
5. Xに告知
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# スクリプトディレクトリをパスに追加
SCRIPT_DIR = Path(__file__).parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from config import BASE_DIR, ARTICLES_DIR, DATA_DIR
from topic_manager import (
    get_next_topic,
    mark_as_posted,
    ensure_minimum_stock,
    get_stock_status,
)
from generate_article import generate_and_save
from post_to_x import post_article_announcement, analyze_tweet_performance


def log(message: str) -> None:
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def git_push_article(filepath: Path, title: str) -> bool:
    """記事をgit pushしてZennに公開"""
    try:
        # git add
        subprocess.run(
            ["git", "add", str(filepath)],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
        )

        # git commit
        commit_message = f"📝 新記事: {title}"
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
        )

        # git push
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=BASE_DIR,
            check=True,
            capture_output=True,
        )

        log(f"✅ Git push完了: {filepath.name}")
        return True

    except subprocess.CalledProcessError as e:
        log(f"❌ Git操作失敗: {e}")
        return False


def get_zenn_article_url(slug: str) -> str:
    """Zenn記事のURLを生成"""
    # GitHubリポジトリからユーザー名を取得
    username = "michey0495"  # TODO: git remote から動的に取得
    return f"https://zenn.dev/{username}/articles/{slug}"


def run_daily_pipeline() -> dict:
    """日次パイプラインを実行"""
    log("🚀 日次パイプライン開始")

    result = {
        "success": False,
        "article_title": None,
        "article_path": None,
        "tweet_url": None,
        "errors": [],
    }

    try:
        # 1. ネタストックを確認・補充
        log("📦 ネタストック確認中...")
        ensure_minimum_stock()
        status = get_stock_status()
        log(f"   利用可能ネタ: {status['available']}件")

        # 2. 次のネタを取得
        topic = get_next_topic()
        if not topic:
            log("⚠️ 投稿するネタがありません")
            result["errors"].append("ネタなし")
            return result

        log(f"📝 今日のネタ: {topic['title']}")

        # 3. 記事を生成
        log("✍️ 記事生成中...")
        article, filepath = generate_and_save(topic, published=True)
        result["article_title"] = article["title"]
        result["article_path"] = str(filepath)

        # 4. Git push
        log("📤 Zennに投稿中...")
        if git_push_article(filepath, article["title"]):
            mark_as_posted(topic["title"])
        else:
            result["errors"].append("Git push失敗")
            return result

        # 5. Zenn URLを生成
        slug = filepath.stem
        article_url = get_zenn_article_url(slug)

        # 6. Xに投稿
        log("📢 Xに告知中...")
        try:
            tweet_result = post_article_announcement(
                title=article["title"],
                url=article_url,
            )
            result["tweet_url"] = tweet_result.get("tweet_url")
        except Exception as e:
            log(f"⚠️ X投稿失敗: {e}")
            result["errors"].append(f"X投稿失敗: {e}")

        # 7. パフォーマンス分析（過去の投稿）
        log("📊 過去投稿のパフォーマンス分析...")
        try:
            performance = analyze_tweet_performance()
            if performance:
                top = performance[0]
                log(f"   最も反応の良い記事: {top.get('article_title')}")
                log(f"   いいね: {top.get('likes')}, RT: {top.get('retweets')}")
        except Exception as e:
            log(f"   分析スキップ: {e}")

        result["success"] = True
        log("🎉 日次パイプライン完了!")

    except Exception as e:
        log(f"❌ エラー発生: {e}")
        result["errors"].append(str(e))

    return result


def main():
    """エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Zenn自動投稿システム")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際には投稿せず、シミュレーションのみ行う"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="ネタストックの状況を表示"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="ネタストックを更新"
    )

    args = parser.parse_args()

    if args.status:
        status = get_stock_status()
        print("📦 ネタストック状況")
        print(f"  - 利用可能: {status['available']}件")
        print(f"  - 投稿済み: {status['posted_count']}件")
        print("\n📝 次の候補:")
        for i, t in enumerate(status["topics"], 1):
            print(f"  {i}. {t.get('title')}")
        return

    if args.refresh:
        log("🔄 ネタストック更新中...")
        ensure_minimum_stock()
        return

    if args.dry_run:
        log("🧪 ドライラン モード")
        topic = get_next_topic()
        if topic:
            print(f"次に投稿するネタ: {topic['title']}")
            print(f"タグ: {topic.get('tags')}")
        return

    # 本番実行
    result = run_daily_pipeline()

    if result["success"]:
        print(f"\n✅ 投稿完了: {result['article_title']}")
        if result["tweet_url"]:
            print(f"🐦 ツイート: {result['tweet_url']}")
    else:
        print(f"\n❌ 失敗: {result['errors']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
