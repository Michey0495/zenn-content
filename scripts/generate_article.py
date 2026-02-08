"""
記事生成スクリプト

Anthropic APIを使用して、キャラクター「椎名しおり」として記事を生成する。
"""
import json
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    CHARACTER,
    CHARACTER_PROMPT,
    ARTICLES_DIR,
    ZENN_TOPICS,
    DEFAULT_EMOJI,
)


# 絵文字候補
EMOJI_MAP = {
    "tips": ["💡", "✨", "🎯"],
    "experiment": ["🧪", "🔬", "🚀"],
    "automation": ["⚙️", "🤖", "🔄"],
    "workflow": ["📋", "🛠️", "🔧"],
    "mcp": ["🔌", "🔗", "🌐"],
    "skill": ["📚", "🎓", "🏆"],
    "productivity": ["⚡", "🏃", "📈"],
    "tmux": ["🖥️", "📺", "🪟"],
    "pptx": ["📊", "🎨", "📝"],
    "default": ["🤖", "💻", "🔥"],
}


def get_emoji_for_topic(tags: list[str]) -> str:
    """タグに応じた絵文字を選択"""
    for tag in tags:
        if tag in EMOJI_MAP:
            return random.choice(EMOJI_MAP[tag])
    return random.choice(EMOJI_MAP["default"])


def generate_slug(title: str) -> str:
    """タイトルからslugを生成"""
    # 日本語を除去し、英数字とハイフンのみに
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')

    # 短すぎる場合は日付を追加
    if len(slug) < 5:
        slug = f"claude-code-tips-{datetime.now().strftime('%Y%m%d')}"

    return slug[:50]  # 最大50文字


def create_article_prompt(topic: dict[str, Any]) -> str:
    """記事生成用プロンプトを作成"""
    title = topic.get("title", "")
    description = topic.get("description", "")
    tags = topic.get("tags", [])
    source = topic.get("source", "")

    return f"""
{CHARACTER_PROMPT}

---

## 今回のお題

タイトル: {title}
補足情報: {description}
抽出元: {source}
タグ: {', '.join(tags)}

---

## 執筆依頼

上記のお題で、Zennに投稿する技術記事を書いてください。

要件:
1. 文字数: 1500〜3000文字程度
2. 構成: 見出しを3〜5個程度使用
3. コード例: 必要に応じて含める
4. トーン: {CHARACTER['nickname']}らしい口調で

注意:
- フロントマター（---で囲まれた部分）は含めないでください
- 見出し（##）から始めてください
- 最初の見出しは「## はじめに」や「## 結論から言うと」など

記事本文のみを出力してください。
"""


def generate_article(topic: dict[str, Any]) -> dict[str, Any]:
    """Anthropic APIで記事を生成"""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = create_article_prompt(topic)

    print(f"📝 記事を生成中: {topic.get('title')}")

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    content = message.content[0].text

    return {
        "title": topic.get("title", ""),
        "content": content,
        "tags": topic.get("tags", ZENN_TOPICS[:3]),
        "emoji": get_emoji_for_topic(topic.get("tags", [])),
        "generated_at": datetime.now().isoformat(),
    }


def save_article(article: dict[str, Any], published: bool = False) -> Path:
    """記事をZenn形式で保存"""
    ARTICLES_DIR.mkdir(exist_ok=True)

    slug = generate_slug(article["title"])
    filename = f"{slug}.md"
    filepath = ARTICLES_DIR / filename

    # Zennフロントマター
    frontmatter = f"""---
title: "{article['title']}"
emoji: "{article['emoji']}"
type: "tech"
topics: {json.dumps(article['tags'][:5], ensure_ascii=False)}
published: {str(published).lower()}
---

"""

    full_content = frontmatter + article["content"]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)

    print(f"✅ 記事を保存: {filepath}")
    return filepath


def generate_and_save(
    topic: dict[str, Any],
    published: bool = False
) -> tuple[dict[str, Any], Path]:
    """記事を生成して保存する（メイン関数）"""
    article = generate_article(topic)
    filepath = save_article(article, published)
    return article, filepath


if __name__ == "__main__":
    # テスト用
    test_topic = {
        "title": "Claude Codeの履歴ファイルを活用する方法",
        "description": "history.jsonlを分析して使用パターンを把握する",
        "tags": ["claudecode", "tips", "productivity"],
        "priority": 5,
    }

    try:
        article, path = generate_and_save(test_topic, published=False)
        print(f"\n生成完了: {path}")
    except Exception as e:
        print(f"エラー: {e}")
