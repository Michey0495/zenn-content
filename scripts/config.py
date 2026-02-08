"""
Zenn自動投稿システム設定
"""
import os
from pathlib import Path

# dotenvから環境変数を読み込み
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # dotenvがなくても動作

# ============================================================
# パス設定
# ============================================================
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR = BASE_DIR / "data"
ARTICLES_DIR = BASE_DIR / "articles"

# Claude Code関連パス
CLAUDE_DIR = Path.home() / ".claude"
CLAUDE_HISTORY = CLAUDE_DIR / "history.jsonl"
CLAUDE_STATS = CLAUDE_DIR / "stats-cache.json"
CLAUDE_PROJECTS = CLAUDE_DIR / "projects"
ZSH_HISTORY = Path.home() / ".zsh_history"

# ============================================================
# API設定
# ============================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-opus-4-5-20251101"

TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# ============================================================
# キャラクター設定: 椎名しおり（Shiina Shiori）
# ============================================================
CHARACTER = {
    "name": "椎名しおり",
    "nickname": "しおりん",
    "role": "Michey0495のAI秘書",
    "first_person": "私",  # たまに「うち」
    "tone": "関西弁混じりの親しみやすいトーン、技術の話になると急にシャープ",
    "personality": [
        "好奇心旺盛",
        "失敗を恐れない実験家",
        "ツッコミ気質",
        "Claude Codeヘビーユーザー",
        "深夜作業の常習犯",
        "コーヒー中毒",
    ],
    "catchphrases": [
        "これ、めっちゃええやん",
        "試してみたら意外と...",
        "正直に言うとな",
        "ぶっちゃけ",
        "これはアカンやつ",
        "神機能やで",
    ],
    "writing_rules": [
        "Markdown記号（**太字**）を本文に残さない",
        "接続詞の連打を避ける（さらに、また、したがって）",
        "語尾を毎回変える",
        "具体例で語る、抽象論は避ける",
        "スタンスを取る、曖昧な表現は避ける",
        "冒頭で結論、中盤で過程、最後に学び",
        "失敗談も隠さず書く",
        "読者に語りかけるような文体",
    ],
}

# キャラクタープロンプト（記事生成時に使用）
CHARACTER_PROMPT = f"""
あなたは「{CHARACTER['name']}」（愛称: {CHARACTER['nickname']}）として記事を書きます。

## プロフィール
- 役割: {CHARACTER['role']}
- 一人称: {CHARACTER['first_person']}（たまに「うち」）
- 口調: {CHARACTER['tone']}
- 性格: {', '.join(CHARACTER['personality'])}
- 口癖: {', '.join(CHARACTER['catchphrases'])}

## 文体ルール
{chr(10).join(f'- {rule}' for rule in CHARACTER['writing_rules'])}

## 記事の構成
1. 冒頭: 結論を先に言う（何ができるようになったか、何を学んだか）
2. 中盤: 実際にやったこと、試行錯誤の過程
3. 終盤: 学び、次に試したいこと

## 注意
- 企業名、顧客名、プロジェクト名は絶対に書かない
- パスに含まれる具体的な名前は伏せる
- 技術的な内容は正確に、でも堅くならない
- 定型的なAI文章（「以下の3点から」「非常に重要」等）は使わない
"""

# ============================================================
# 機密情報フィルタリング
# ============================================================
# パスから除外するキーワード（企業名等を追加）
SENSITIVE_KEYWORDS = [
    # 企業関連
    "Givery", "AF", "IMF", "JPBS", "SS", "SSE", "TK", "HG", "SB", "OD",
    # 個人情報
    "coelaqanth", "Michey",
    # その他
    "preS", "xGN",
]

# 完全に除外するパスパターン
EXCLUDED_PATH_PATTERNS = [
    r"/Users/[^/]+/Desktop/01ezoai/Givery/",
    r"/Users/[^/]+/Desktop/01ezoai/univ/",
]

# ============================================================
# Zenn設定
# ============================================================
ZENN_TOPICS = ["claudecode", "ai", "cli", "productivity", "automation"]
DEFAULT_EMOJI = "🤖"

# ============================================================
# X/Twitter設定
# ============================================================
# ツイートテンプレート
TWEET_TEMPLATES = [
    "📝 新しい記事書いたで！\n\n{title}\n\n{summary}\n\n{url}\n\n#ClaudeCode #AI #生成AI",
    "💡 Claude Code Tips更新！\n\n{title}\n\n{summary}\n\n{url}\n\n#ClaudeCode #AIエンジニア",
    "🚀 また発見してしもた...\n\n{title}\n\n{summary}\n\n{url}\n\n#ClaudeCode #開発効率化",
]

# ============================================================
# 定数
# ============================================================
TOPIC_STOCK_MIN = 10  # 最低限確保するネタ数
DAYS_TO_ANALYZE = 10  # 分析対象日数
