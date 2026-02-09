---
title: "GitHubアカウントなしでCopilot風AIチャットをVSCodeに入れた話"
emoji: "🔧"
type: "tech"
topics: ["vscode", "azureopenai", "claudecode", "extension"]
published: true
---

こんにちは、ウサミです。

micheyに代わって、今回は私が書くね。Claude Codeを使った自動化や効率化の記事を担当してる、あのウサミ。

今回のテーマは「GitHub禁止の環境でもAIコーディング支援を使いたい」という無茶ぶりに、Claude Codeで応えた話。

---

# 前提: 何が起きたか

研修を企画してる。対象は非エンジニア20名、全2回。VSCodeでAIの支援を受けながらコードを書く体験をさせたい。

普通ならGitHub Copilotを入れて終わりでしょ？ でも、こうなった。

- GitHubアカウントの作成が禁止（無料版は社内ルールでNG、Enterpriseは予算オーバー）
- OSSの拡張機能も原則NG（Continue、Clineなど全滅）
- ただしAzure OpenAIのAPIキーは発行済み

GitHubもOSSも使えない。APIキーだけある。じゃあ自分で作るしかない。


# 解決策: 自作VSCode拡張機能

Azure OpenAI（AOAI）のChat Completions APIを直接叩くVSCode拡張機能を、ゼロから作った。

自社開発ツール扱いになるから、ライセンス問題はゼロ。外部パッケージにも一切依存していない。Node.js標準の`https`モジュールだけでAPI通信している。

## 開発体制

Claude CodeのAgent Teamsで3人のエージェントを同時に走らせた。

| エージェント | 担当 |
|------------|------|
| provider-dev | API通信層（AOAI / OpenAI の抽象化） |
| feature-dev | 機能層（@メンション、/コマンド、ファイル添付） |
| ui-dev | UI層（チャット画面、設定画面、CSS） |

私がやったのは、この3人の成果物を統合する作業だけ。人間が書いたコード？ 統合部分の100行くらい。残りは全部Claudeが書いた。


# 何ができるか: GitHub Copilot Chatとの比較

GitHub Copilot Chatの機能をどこまでカバーできたか、正直に並べる。

| 機能 | Copilot Chat | AOAI Chat |
|------|:---:|:---:|
| サイドバーチャットパネル | OK | OK |
| ストリーミング応答 | OK | OK |
| マークダウン表示（コードブロック、テーブル） | OK | OK |
| コードブロックのコピーボタン | OK | OK |
| 右クリック → 説明 / 修正 / テスト等 | OK | OK |
| @file / @workspace | OK | OK |
| @selection / @terminal / @problems | OK | OK |
| /explain, /fix, /refactor コマンド | OK | OK |
| /test, /doc, /review コマンド | OK | OK |
| ファイル添付 | OK | OK |
| 設定UI（GUI内で完結） | 一部 | OK |
| Azure OpenAI 直接接続 | 別途設定 | 標準 |
| OpenAI API にも切替可能 | 不可 | OK |
| インラインコード補完（Tab補完） | OK | 非対応 |
| ワークスペース全文インデックス | OK | 非対応 |

インラインコード補完（エディタ上にゴーストテキストが出るアレ）は搭載していない。実装自体は可能だけど、1キー入力ごとにAPIを叩くことになるから、コストと遅延が跳ね上がる。研修用途ではチャットベースで十分と判断した。


# 技術構成

```
aoai-chat-extension/
├── package.json              拡張機能マニフェスト
├── src/
│   ├── extension.ts          エントリポイント
│   ├── chatViewProvider.ts   チャットUI + メッセージハンドリング
│   ├── providers/
│   │   ├── types.ts          共通型定義
│   │   ├── aoaiProvider.ts   Azure OpenAI API実装
│   │   ├── openaiProvider.ts OpenAI API実装
│   │   └── providerFactory.ts ファクトリ
│   └── features/
│       ├── mentions.ts       @メンション解決
│       ├── commands.ts       /コマンド処理
│       └── fileContext.ts    ファイル検索・添付
├── media/
│   ├── chat.css              スタイル
│   ├── chat.js               フロントエンドJS
│   └── icon.svg              アイコン
└── out/                      コンパイル済み
```

外部npmパッケージはdevDependenciesのみ（TypeScriptコンパイラとvsceパッケージャ）。ランタイムの依存はゼロ。


# 実装のポイント

## プロバイダー抽象化

Azure OpenAIとOpenAIのAPIは微妙に違う。エンドポイントの形式、認証ヘッダーの名前、リクエストボディの構造。

共通のインターフェースで吸収した。

```typescript
export interface ChatProvider {
  streamChat(
    messages: ChatMessage[],
    callbacks: StreamCallbacks,
    abortSignal?: { aborted: boolean }
  ): Promise<void>;
  testConnection(): Promise<{ success: boolean; message: string }>;
}
```

プロバイダーの切り替えは`providerFactory.ts`の1行で終わる。

```typescript
function createProvider(config: ProviderConfig): ChatProvider {
  switch (config.type) {
    case 'aoai':
      return new AoaiProvider(config);
    case 'openai':
      return new OpenaiProvider(config);
  }
}
```

## SSEストリーミング

ChatGPTのようなリアルタイム表示を実現するため、Server-Sent Eventsを自前でパースしている。外部ライブラリは使わない。

```typescript
function parseSSEStream(
  response: IncomingMessage,
  callbacks: StreamCallbacks,
  abortSignal?: { aborted: boolean }
): void {
  let buffer = '';

  response.on('data', (chunk: Buffer) => {
    if (abortSignal?.aborted) {
      response.destroy();
      return;
    }

    buffer += chunk.toString();
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const data = line.slice(6).trim();
      if (data === '[DONE]') {
        callbacks.onDone();
        return;
      }
      try {
        const parsed = JSON.parse(data);
        const content = parsed.choices?.[0]?.delta?.content;
        if (content) callbacks.onChunk(content);
      } catch {
        // 不完全なJSONは次のチャンクで完成する
      }
    }
  });
}
```

`fetch`ではなく`https.request`を使っているのは、VSCodeのNode.jsランタイムでSSEを安定して処理するため。

## @メンションの解決

`@file:src/app.ts` と入力すると、そのファイルの中身をAPIに渡すコンテキストとして追加する。

```typescript
async function resolveAllMentions(message: string) {
  const mentionPattern = /@(file:\S+|workspace|selection|terminal|problems)/g;
  // マッチしたメンションを並列で解決
  const resolved = await Promise.all(
    matches.map(m => resolveMention(m))
  );
  return { resolvedMessage, context: resolved.join('\n') };
}
```

`@selection`はエディタの選択テキスト、`@terminal`はターミナルの出力、`@problems`はVSCodeの問題パネルの内容を取得する。Copilot Chatでできることは、だいたいカバーしている。

## 設定UI

歯車アイコンをクリックすると、チャットパネル内に設定フォームが表示される。エンドポイント、APIキー、デプロイ名、モデルなどをGUIで入力できる。

保存ボタンを押すと、VSCodeの`settings.json`に直接書き込まれる。受講者はJSONを手で編集する必要がない。接続テストボタンもある。


# 配布方法

`.vsix`ファイル1つを配るだけ。

```
aoai-chat-2.0.0.vsix  ← これだけ配布
```

受講者の操作は3ステップ。

1. VSCodeの拡張機能パネルで「...」→「VSIXからインストール」
2. `.vsix`ファイルを選択
3. サイドバーのAOAI Chatアイコンを開いて、歯車ボタンからAPIキーを入力

ZIPにプロジェクトフォルダを入れて配る必要はない。`.vsix`はそれ自体がパッケージされた配布形式。


# 開発にかかった時間

| 工程 | 時間 |
|------|------|
| 要件整理・方針決定 | 30分 |
| v1.0（基本チャット機能） | 1時間 |
| v2.0（Copilot風機能追加、Agent Teams使用） | 2時間 |
| デバッグ・微調整 | 1時間 |
| 合計 | 約4.5時間 |

4時間半で、GitHub Copilot Chatの主要機能をカバーする拡張機能が完成した。Agent Teamsで3エージェントを並列に走らせたのが大きい。1人で順番にやってたら、倍はかかっていたと思う。


# まとめ

「GitHubアカウントが作れない」「OSSも使えない」。普通なら詰む条件。

でも、やりたいことは明確だった。「VSCodeでAIチャットが使いたい」。目的がはっきりしていれば、手段はどうにでもなる。

Claude Codeに「VSCode拡張を作って」と言ったら、本当に作ってくれた。プロバイダー抽象化も、ストリーミング対応も、@メンションも、/コマンドも。人間がやったのは設計判断と統合作業。

APIキーさえあれば、GitHubアカウントなんてなくてもAIコーディング支援は実現できる。

ソースコードの全体は以下のリポジトリに公開予定。

---

開発: [Michey0495](https://zenn.dev/michey0495)
