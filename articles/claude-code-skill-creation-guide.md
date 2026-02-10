---
title: "Claude Code Hooksで開発フローを自動化する実践ガイド"
emoji: "⚡"
type: "tech"
topics: ["claudecode", "hooks", "automation"]
published: true
---

## Hooksを仕込んだらClaude Codeが別物になった

Claude Codeにはhooksという仕組みがある。ツール実行の前後やセッション開始時に、自分で書いたシェルスクリプトを自動で走らせられる。

これ、使ってない人が多い。もったいない。

私はHooksを入れてから、保護すべきファイルの誤編集がゼロになった。Prettierの手動実行も消えた。通知も勝手に飛んでくる。設定ファイル1つでここまで変わるとは思わなかった。

## Hooksの基本構造

`.claude/settings.json` に書く。プロジェクト直下に置けばそのプロジェクト専用、`~/.claude/settings.json` に置けば全プロジェクト共通で効く。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

`PreToolUse`がイベント名。`matcher`でどのツールに反応するか正規表現で指定。`command`に実行するシェルコマンドを書く。

stdinにJSON形式でツールの入力情報が流れてくるから、jqで拾って判定する。exit 0で許可、exit 2でブロック。

## 使えるイベント一覧

全部で十数種あるけど、実際よく使うのはこの5つ。

- `PreToolUse` -- ツール実行前。ファイル保護やコマンドの検証に使う
- `PostToolUse` -- ツール実行後。フォーマッタの自動実行やログ記録に使う
- `Notification` -- 許可待ちや待機時の通知。デスクトップ通知を飛ばせる
- `Stop` -- Claudeが応答を終えようとした時。テスト実行を強制できる
- `SessionStart` -- セッション開始時。環境変数の設定やルールの再注入に使う

## 最初にやったこと: .envを守る

Hooks導入のきっかけは、Claude Codeが`.env`を書き換えようとしたこと。

APIキーが入ってるファイルをAIが触るのはまずい。手動で「いいえ」を押せばいいけど、見逃すリスクがある。

`.claude/hooks/protect-files.sh` を作った。

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

PROTECTED=(".env" "package-lock.json" ".git/" "credentials")

for pattern in "${PROTECTED[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Blocked: $FILE_PATH is protected" >&2
    exit 2
  fi
done

exit 0
```

settings.jsonはこう。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

exit 2を返すとClaude Codeがツール呼び出しを中止してくれる。stderrに理由を書けば、Claudeがそれを読んで「ブロックされました」と報告してくる。

導入してから、保護ファイルへの誤操作は完全にゼロ。安心感が段違い。

## Prettierの自動実行

次に入れたのがPostToolUseでのフォーマッタ自動実行。

EditやWriteでファイルを変更するたびにPrettierが走る。

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

これ入れる前は、Claude Codeが生成したコードを毎回手動でフォーマットしてた。地味にストレスだったのが消えた。

`|| true` を付けてるのがポイント。Prettierが対応してない拡張子のファイルでエラーが出ても、hookが失敗扱いにならない。

## ハマった話: matcherを空にして全ツールに適用したら地獄

最初、matcherを空文字にすると全ツールにマッチすることを知らなかった。

「全部のツールでログ取りたいな」と思って、PostToolUseのmatcherを空にした。Read、Glob、Grep、全部にフックが走る。

結果、ファイルを1個読むだけでフックが発火して、処理が重くなって、体感速度が半分に落ちた。

matcherは必ず必要なツールだけに絞る。`Edit|Write`や`Bash`みたいに、明示的に書くのが正解。

## デスクトップ通知: 許可待ちを見逃さない

Claude Codeが権限の許可を求めてくるとき、ターミナルを見てないと気づかない。

Notificationフックで解決した。

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude Codeが許可を待っています\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

macOSのosascriptでシステム通知を飛ばしてる。これで別のウィンドウで作業してても、許可待ちを見逃さなくなった。

## 危険なコマンドの自動ブロック

`rm -rf`をBashで実行しようとしたらブロックする。当たり前にやるべきなのに、意外と設定してない人が多い。

```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

DANGEROUS=("rm -rf" "drop table" "git push --force" "reset --hard")

for pattern in "${DANGEROUS[@]}"; do
  if echo "$COMMAND" | grep -qi "$pattern"; then
    echo "Blocked: dangerous command detected: $pattern" >&2
    exit 2
  fi
done

exit 0
```

PreToolUseのmatcherを`Bash`にして適用する。

## Stopフックでテストを強制する

一番気に入ってる使い方がこれ。Claudeが「完了しました」と言おうとした瞬間にテストを走らせる。

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npm test 2>&1 | tail -5; if [ ${PIPESTATUS[0]} -ne 0 ]; then echo 'Tests failed' >&2; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

exit 2を返すと、Claudeは停止せずに続行する。テストが落ちてるのに「完了」とは言わせない。

ただし注意点がある。テストが重いプロジェクトだと毎回待たされる。timeoutを設定するか、軽量なテストだけ回す工夫が要る。

## 自分のHooks構成

今の`.claude/settings.json`はこうなってる。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh" }]
      },
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous.sh" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write 2>/dev/null || true" }]
      }
    ],
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [{ "type": "command", "command": "osascript -e 'display notification \"Claude Codeが許可を待っています\" with title \"Claude Code\"'" }]
      }
    ]
  }
}
```

4つのフック。これだけで開発体験が相当変わる。

Hooksの設定は`.claude/settings.json`に書くだけ。スクリプトは`.claude/hooks/`配下に置いて実行権限を付ける。プロジェクトごとに違うルールにできるから、案件ごとに保護対象を変えるのも簡単。

Claude Codeをただのコード生成ツールとして使ってるなら、Hooksで一段階上の自動化に踏み込んでみてほしい。守りと攻めの両方が手に入る。
