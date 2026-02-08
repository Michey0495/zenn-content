# zenn-write

Zenn記事をキャラクターの口調で執筆するスキル。

## 使用方法

```
/zenn-write <カテゴリ> <タイトルまたは内容の概要>
```

### カテゴリ一覧

| カテゴリ | キャラクター | 用途 |
|---------|-------------|------|
| game | ミケ（ネコ） | ブラウザゲーム、Three.js、Canvas |
| training | ホウ先生（フクロウ） | 研修資料、入門記事、チュートリアル |
| tech | フェリ（フェレット） | 新技術検証、〜を試してみた系 |
| claude | ウサミ（うさぎ） | Claude Code、AI活用、自動化 |
| other | プラティ（カモノハシ） | その他全般 |

### 例

```
/zenn-write game Three.jsでテトリスを作った
/zenn-write training Git入門ハンズオン
/zenn-write tech Bun 2.0を試してみた
/zenn-write claude Claude Codeでブログ自動生成
/zenn-write other MCPサーバーの作り方
```

## 実行手順

1. キャラクター設定を読み込む
2. カテゴリに応じたキャラクターを選択
3. そのキャラクターの口調・文体で記事を執筆
4. `/Users/coelaqanth_006/Desktop/02forAI/09zenn-content/articles/` に保存
5. プレビューコマンドを案内

## キャラクター設定ファイル

詳細は以下を参照：
`/Users/coelaqanth_006/Desktop/02forAI/09zenn-content/.claude/zenn-characters.md`

---

## キャラクター別テンプレート

### ミケ（game）

```markdown
---
title: "<タイトル>"
emoji: "🎮"
type: "tech"
topics: ["threejs", "typescript", "gamedev"]
published: true
---

<導入：軽く、すぐ本題へ>

![完成イメージ](画像パス)
*キャプション*

## 作ったもの

<完成形を先に見せる>

## 動かし方

<すぐ試せるように>

## 仕組み

<必要最低限の技術解説>

## 遊んでみて

<締め：気軽に試してもらう>
```

### ホウ先生（training）

```markdown
---
title: "<タイトル>"
emoji: "📚"
type: "tech"
topics: ["初心者向け", "入門"]
published: true
---

## はじめに

<丁寧な導入、対象読者の明示>

## この記事で学べること

<箇条書きで明示>

## 前提知識

<必要な知識を明記>

## 本編

### 1. <セクション>

<段階的な説明>

### 2. <セクション>

<図解や具体例を交える>

## まとめ

<学んだポイントの振り返り>

## 次のステップ

<発展的な内容への誘導>
```

### フェリ（tech）

```markdown
---
title: "<タイトル>"
emoji: "🔬"
type: "tech"
topics: ["検証", "新機能"]
published: true
---

## TL;DR

<結論を先に>

## やってみた動機

<なぜ試したか>

## 環境

<バージョン情報>

## 試してみる

### インストール

<コマンドとその結果>

### 動かしてみる

<実際の出力、エラーも含む>

## 結果

<ベンチマーク、比較>

## 感想

<率直な感想>

## 次に試したいこと

<今後の展望>
```

### ウサミ（claude）

```markdown
---
title: "<タイトル>"
emoji: "🐰"
type: "tech"
topics: ["claudecode", "ai", "自動化"]
published: true
---

## 結論

<成果を先に見せる>

## Before / After

<何がどう変わったか>

## やったこと

### 1. 最初の指示

<実際のプロンプト>

### 2. Claudeとのやり取り

<対話の流れ>

### 3. フィードバックと修正

<改善の過程>

## 所要時間

<具体的な時間>

## 学んだこと

<AIとの協働のコツ>

## あなたも試してみて

<読者への呼びかけ>
```

### プラティ（other）

```markdown
---
title: "<タイトル>"
emoji: "🦆"
type: "tech"
topics: []
published: true
---

## そういえば

<雑談風の導入>

## 本題

<独自の切り口で解説>

## ちなみに

<関連する余談>

## まとめ的なもの

<ゆるく締める>
```

---

## 注意事項

- キャラクターの口調を徹底する
- 「〜にゃ」「〜ホー」などの安易な語尾は使わない
- 技術的な正確性は保つ
- 画像がある場合は `/images/` に配置
- slugはケバブケースで英語
