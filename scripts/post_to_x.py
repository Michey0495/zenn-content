"""
X（Twitter）投稿スクリプト

Twitter API v2を使用して記事の告知を投稿する。
"""
import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from requests_oauthlib import OAuth1

from config import (
    TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_BEARER_TOKEN,
    TWEET_TEMPLATES,
    DATA_DIR,
    CHARACTER,
)


# Twitter API v2エンドポイント
TWITTER_API_URL = "https://api.twitter.com/2/tweets"


def get_oauth1() -> OAuth1:
    """OAuth1認証オブジェクトを取得"""
    return OAuth1(
        TWITTER_CONSUMER_KEY,
        TWITTER_CONSUMER_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET,
    )


def truncate_text(text: str, max_length: int = 280) -> str:
    """ツイート文字数制限に収める"""
    if len(text) <= max_length:
        return text

    # URLを保持しつつ短縮
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, text)

    # URL以外の部分を短縮
    text_without_urls = re.sub(url_pattern, '{{URL}}', text)

    # 短縮
    available = max_length - sum(23 for _ in urls)  # URLは23文字カウント
    if len(text_without_urls) > available:
        text_without_urls = text_without_urls[:available - 3] + "..."

    # URLを戻す
    for url in urls:
        text_without_urls = text_without_urls.replace('{{URL}}', url, 1)

    return text_without_urls


def generate_tweet_text(
    title: str,
    url: str,
    summary: str = ""
) -> str:
    """ツイート文を生成"""
    # テンプレートをランダム選択
    template = random.choice(TWEET_TEMPLATES)

    # サマリーがない場合はキャラの口癖を使う
    if not summary:
        summary = random.choice(CHARACTER["catchphrases"])

    tweet = template.format(
        title=title,
        url=url,
        summary=summary,
    )

    return truncate_text(tweet)


def post_tweet(text: str) -> dict[str, Any]:
    """ツイートを投稿"""
    if not all([
        TWITTER_CONSUMER_KEY,
        TWITTER_CONSUMER_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET,
    ]):
        raise ValueError("Twitter API認証情報が設定されていません")

    auth = get_oauth1()

    payload = {"text": text}

    response = requests.post(
        TWITTER_API_URL,
        auth=auth,
        json=payload,
    )

    if response.status_code != 201:
        raise Exception(f"ツイート投稿失敗: {response.status_code} - {response.text}")

    result = response.json()
    tweet_id = result.get("data", {}).get("id")

    print(f"✅ ツイート投稿完了: https://twitter.com/i/status/{tweet_id}")

    return result


def save_tweet_record(
    article_title: str,
    tweet_text: str,
    tweet_id: str,
    article_url: str
) -> None:
    """投稿記録を保存"""
    DATA_DIR.mkdir(exist_ok=True)
    records_file = DATA_DIR / "tweet_records.json"

    records = []
    if records_file.exists():
        with open(records_file, 'r', encoding='utf-8') as f:
            records = json.load(f)

    records.append({
        "article_title": article_title,
        "tweet_text": tweet_text,
        "tweet_id": tweet_id,
        "article_url": article_url,
        "posted_at": datetime.now().isoformat(),
    })

    with open(records_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def post_article_announcement(
    title: str,
    url: str,
    summary: str = ""
) -> dict[str, Any]:
    """記事告知ツイートを投稿（メイン関数）"""
    tweet_text = generate_tweet_text(title, url, summary)

    print(f"📢 ツイート投稿中...")
    print(f"   {tweet_text[:50]}...")

    result = post_tweet(tweet_text)

    tweet_id = result.get("data", {}).get("id", "")
    save_tweet_record(title, tweet_text, tweet_id, url)

    return {
        "tweet_id": tweet_id,
        "tweet_text": tweet_text,
        "tweet_url": f"https://twitter.com/i/status/{tweet_id}",
    }


def get_tweet_performance(tweet_id: str) -> dict[str, Any] | None:
    """ツイートのパフォーマンスを取得"""
    if not TWITTER_BEARER_TOKEN:
        return None

    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
    }

    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {
        "tweet.fields": "public_metrics",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return None

    data = response.json().get("data", {})
    metrics = data.get("public_metrics", {})

    return {
        "tweet_id": tweet_id,
        "likes": metrics.get("like_count", 0),
        "retweets": metrics.get("retweet_count", 0),
        "replies": metrics.get("reply_count", 0),
        "impressions": metrics.get("impression_count", 0),
    }


def analyze_tweet_performance() -> list[dict[str, Any]]:
    """過去のツイートパフォーマンスを分析"""
    records_file = DATA_DIR / "tweet_records.json"
    if not records_file.exists():
        return []

    with open(records_file, 'r', encoding='utf-8') as f:
        records = json.load(f)

    results = []
    for record in records:
        tweet_id = record.get("tweet_id")
        if tweet_id:
            perf = get_tweet_performance(tweet_id)
            if perf:
                perf["article_title"] = record.get("article_title")
                results.append(perf)

    # エンゲージメント順にソート
    results.sort(
        key=lambda x: x.get("likes", 0) + x.get("retweets", 0) * 2,
        reverse=True
    )

    return results


if __name__ == "__main__":
    # テスト（実際には投稿しない）
    test_title = "Claude Codeの履歴ファイルを活用する方法"
    test_url = "https://zenn.dev/michey0495/articles/test-article"

    tweet_text = generate_tweet_text(test_title, test_url)
    print("生成されたツイート:")
    print(tweet_text)
    print(f"\n文字数: {len(tweet_text)}")
