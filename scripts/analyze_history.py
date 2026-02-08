"""
Claude Code履歴分析スクリプト

履歴データから記事ネタを抽出する。
機密情報は自動的にフィルタリングされる。
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from collections import Counter

from config import (
    CLAUDE_HISTORY,
    CLAUDE_STATS,
    CLAUDE_PROJECTS,
    ZSH_HISTORY,
    SENSITIVE_KEYWORDS,
    EXCLUDED_PATH_PATTERNS,
    DAYS_TO_ANALYZE,
)


def sanitize_text(text: str) -> str:
    """機密情報を除去する"""
    result = text

    # パスパターンを除去
    for pattern in EXCLUDED_PATH_PATTERNS:
        result = re.sub(pattern, "[REDACTED_PATH]/", result)

    # キーワードを置換
    for keyword in SENSITIVE_KEYWORDS:
        result = re.sub(
            rf'\b{re.escape(keyword)}\b',
            '[企業名]',
            result,
            flags=re.IGNORECASE
        )

    # 絶対パスを相対パス風に変換
    result = re.sub(
        r'/Users/[^/]+/',
        '~/',
        result
    )

    return result


def load_claude_history(days: int = DAYS_TO_ANALYZE) -> list[dict[str, Any]]:
    """Claude Code履歴を読み込む"""
    if not CLAUDE_HISTORY.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    cutoff_ts = cutoff.timestamp() * 1000  # ミリ秒

    entries = []
    with open(CLAUDE_HISTORY, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get('timestamp', 0) >= cutoff_ts:
                    # 機密情報をサニタイズ
                    entry['display'] = sanitize_text(entry.get('display', ''))
                    entry['project'] = sanitize_text(entry.get('project', ''))
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

    return entries


def load_stats_cache() -> dict[str, Any]:
    """使用統計を読み込む"""
    if not CLAUDE_STATS.exists():
        return {}

    with open(CLAUDE_STATS, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_zsh_history(days: int = DAYS_TO_ANALYZE) -> list[str]:
    """zsh履歴を読み込む（Claude Code関連のみ）"""
    if not ZSH_HISTORY.exists():
        return []

    # Claude Code関連のキーワード
    keywords = ['claude', 'npx', 'mcp', 'anthropic', 'zenn', 'git push']

    commands = []
    with open(ZSH_HISTORY, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # zsh履歴形式: : timestamp:0;command
            if ';' in line:
                cmd = line.split(';', 1)[1].strip()
            else:
                cmd = line.strip()

            # フィルタリング
            if any(kw in cmd.lower() for kw in keywords):
                sanitized = sanitize_text(cmd)
                if sanitized not in commands:
                    commands.append(sanitized)

    return commands[-100:]  # 直近100件


def extract_features_from_history(entries: list[dict]) -> dict[str, Any]:
    """履歴から特徴を抽出する"""
    features = {
        "commands_used": Counter(),
        "skills_used": Counter(),
        "patterns": [],
        "heavy_usage_days": [],
        "unique_workflows": [],
    }

    for entry in entries:
        display = entry.get('display', '')

        # スラッシュコマンドの抽出
        commands = re.findall(r'/(\w+)', display)
        for cmd in commands:
            features["commands_used"][cmd] += 1

        # スキル/ワークフローの検出
        if 'agent team' in display.lower():
            features["patterns"].append("Agent Teams使用")
        if 'tmux' in display.lower():
            features["patterns"].append("tmux分割")
        if 'スライド' in display or 'slide' in display.lower():
            features["patterns"].append("スライド生成")
        if 'mcp' in display.lower():
            features["patterns"].append("MCP連携")

    return features


def extract_topic_candidates(
    history: list[dict],
    stats: dict,
    zsh_commands: list[str]
) -> list[dict[str, Any]]:
    """記事ネタ候補を抽出する"""
    candidates = []
    features = extract_features_from_history(history)

    # 1. よく使うコマンドからネタを生成
    for cmd, count in features["commands_used"].most_common(5):
        if count >= 2:
            candidates.append({
                "type": "command_usage",
                "title": f"/{cmd}コマンドを使い倒してみた",
                "source": f"使用回数: {count}回",
                "priority": min(count, 10),
                "tags": ["claudecode", "cli", "tips"],
            })

    # 2. 使用統計からネタを生成
    daily_activity = stats.get("dailyActivity", [])
    for day in daily_activity:
        if day.get("messageCount", 0) > 1000:
            candidates.append({
                "type": "heavy_usage",
                "title": f"Claude Codeで{day['messageCount']}メッセージ送った日の記録",
                "source": f"日付: {day['date']}",
                "priority": 8,
                "tags": ["claudecode", "productivity", "experiment"],
            })

    # 3. パターンからネタを生成
    unique_patterns = list(set(features["patterns"]))
    pattern_topics = {
        "Agent Teams使用": {
            "title": "Agent Teamsで並列開発してみた話",
            "tags": ["claudecode", "agentteams", "automation"],
        },
        "tmux分割": {
            "title": "tmux×Claude Codeで画面分割運用のコツ",
            "tags": ["claudecode", "tmux", "workflow"],
        },
        "スライド生成": {
            "title": "Claude Codeでスライド自動生成する方法",
            "tags": ["claudecode", "pptx", "automation"],
        },
        "MCP連携": {
            "title": "MCP連携で広がるClaude Codeの可能性",
            "tags": ["claudecode", "mcp", "integration"],
        },
    }

    for pattern in unique_patterns:
        if pattern in pattern_topics:
            topic = pattern_topics[pattern]
            candidates.append({
                "type": "pattern",
                "title": topic["title"],
                "source": f"検出パターン: {pattern}",
                "priority": 7,
                "tags": topic["tags"],
            })

    # 4. zshコマンドからネタを生成
    if any('skill' in cmd.lower() for cmd in zsh_commands):
        candidates.append({
            "type": "skill_creation",
            "title": "Claude Codeスキル作成のベストプラクティス",
            "source": "スキル関連コマンド検出",
            "priority": 6,
            "tags": ["claudecode", "skill", "customization"],
        })

    # 重複除去と優先度ソート
    seen_titles = set()
    unique_candidates = []
    for c in sorted(candidates, key=lambda x: -x["priority"]):
        if c["title"] not in seen_titles:
            seen_titles.add(c["title"])
            unique_candidates.append(c)

    return unique_candidates


def analyze() -> dict[str, Any]:
    """メイン分析関数"""
    print("📊 履歴分析を開始...")

    # データ読み込み
    history = load_claude_history()
    print(f"  - Claude Code履歴: {len(history)}件")

    stats = load_stats_cache()
    daily_count = len(stats.get("dailyActivity", []))
    print(f"  - 使用統計: {daily_count}日分")

    zsh_commands = load_zsh_history()
    print(f"  - zsh履歴: {len(zsh_commands)}件")

    # ネタ抽出
    candidates = extract_topic_candidates(history, stats, zsh_commands)
    print(f"  - ネタ候補: {len(candidates)}件")

    return {
        "analyzed_at": datetime.now().isoformat(),
        "history_count": len(history),
        "stats_days": daily_count,
        "candidates": candidates,
    }


if __name__ == "__main__":
    result = analyze()
    print("\n📝 抽出されたネタ候補:")
    for i, c in enumerate(result["candidates"], 1):
        print(f"  {i}. {c['title']} (優先度: {c['priority']})")
