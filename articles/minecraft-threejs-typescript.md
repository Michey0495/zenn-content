---
title: "Claude Codeに「マイクラ作って」と言ったら本当に作ってくれた話"
emoji: "⛏️"
type: "tech"
topics: ["claudecode", "threejs", "typescript", "ai", "gamedev"]
published: true
---

## はじめに

Claude Code（Anthropic公式のCLIツール）に「ブラウザで遊べるマインクラフトの完全版ゲームを作って」と指示したら、本当に遊べるゲームが完成した。この記事では、AIとの対話でどのようにゲームが構築されていったのかを記録する。

![完成したゲーム画面](/images/minecraft-gameplay.png)
*完成したゲーム画面。木、地形、ホットバー、体力ゲージが表示されている*

## 最初の指示

最初に与えた指示はシンプルだった。

```
ブラウザで遊べるマインクラフトの完全版ゲームを作って。
```

するとClaudeから質問が返ってきた。

> ゲームモードは？（サバイバル or クリエイティブ）
> ワールドサイズは？（無限生成 or 固定サイズ）
> 必要な機能は？

回答：
- サバイバルモード（体力、空腹度、インベントリ、クラフト、敵モブあり）
- 固定サイズ128x128ブロック
- 地形生成、クラフトシステム、モブ（動物・モンスター）すべて必要

## Claudeが提示した実装計画

Claudeはまず実装計画を立てた。

| フェーズ | 内容 | 主要ファイル |
|---------|------|-------------|
| 1 | 基盤構築 | Engine.ts, GameLoop.ts, InputManager.ts |
| 2 | ワールド生成 | PerlinNoise.ts, TerrainGenerator.ts, ChunkMesher.ts |
| 3 | プレイヤー操作 | Player.ts, Physics.ts, Raycast.ts |
| 4 | サバイバル要素 | Inventory.ts, HUD.ts |
| 5 | クラフト | Recipe.ts, CraftingSystem.ts |
| 6 | モブ | Entity.ts, AIController.ts, MobSpawner.ts |
| 7 | 仕上げ | DayNightCycle.ts, 効果音 |

技術スタックはThree.js + TypeScript + Viteで確定。

## 実装の流れ

### Phase 1: 基盤（約5分）

Claudeはまずプロジェクトを初期化し、Three.jsのシーン・カメラ・レンダラーを設定した。Pointer Lock APIでFPS視点を実現。

```typescript
// Engine.ts - Claudeが生成したコード
export class Engine {
  readonly scene: THREE.Scene
  readonly camera: THREE.PerspectiveCamera
  readonly renderer: THREE.WebGLRenderer

  constructor() {
    this.scene = new THREE.Scene()
    this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    this.renderer = new THREE.WebGLRenderer({ antialias: true })
    // ...
  }
}
```

### Phase 2: ワールド生成（約10分）

Perlinノイズで地形を生成。山、洞窟、木が自動配置される。

```typescript
// TerrainGenerator.ts - 地形の高さ計算
private getHeight(x: number, z: number): number {
  let height = 0
  let amplitude = 1
  let frequency = 0.02

  for (let i = 0; i < 4; i++) {
    height += this.noise.noise2D(x * frequency, z * frequency) * amplitude
    amplitude *= 0.5
    frequency *= 2
  }

  return Math.floor(this.baseHeight + height * 15)
}
```

128x128x64ブロックのワールドデータは`Uint8Array`で管理。約1MBでメモリ効率が良い。

### Phase 3: プレイヤー操作（約10分）

WASD移動、マウス視点、ジャンプ、衝突判定。DDAアルゴリズムでブロックの選択と破壊・設置を実装。

### Phase 4-5: インベントリとHUD（約10分）

36スロットのインベントリ、ホットバー、体力・空腹度ゲージ。アイテムアイコンはCanvas APIで16x16のピクセルアートを動的生成。

### Phase 6: モブ（約15分）

ゾンビ、スケルトン（敵）、豚、牛（友好）を実装。状態機械でAIを制御。

```typescript
// Zombie.ts - AI状態遷移
switch (this.aiState) {
  case AIState.IDLE:
    if (distToPlayer < 16) this.aiState = AIState.CHASE
    break
  case AIState.CHASE:
    if (distToPlayer < this.attackRange) this.aiState = AIState.ATTACK
    else this.moveTowards(player.position, this.moveSpeed)
    break
  case AIState.ATTACK:
    this.attackPlayer(player)
    break
}
```

夜間のみ敵モブがスポーンする昼夜サイクルも実装。

## 途中のフィードバックと修正

最初のビルド後、実際にプレイして問題を報告した。

**報告内容：**
> 床の判定はあるが見えない。ブロックを壊してもアイテム化しない。インベントリに何があるかわからない。

Claudeは即座に修正。ブロックの面が表示されない問題は頂点の巻き順が原因で、`THREE.DoubleSide`で解決した。

**2回目の報告：**
> 上面のテクスチャがない。

**3回目の報告：**
> 横のテクスチャが消えた。あとW2回でダッシュ、ジャンプ中に真下にブロックを置けるようにして。攻撃も実装して。

すべて対応された。追加された機能：

- Wキーダブルタップでダッシュ
- 真下を向いてジャンプ中に右クリックで足場設置
- 左クリックでモブを攻撃（剣でダメージ増加）

## 最終的なプロジェクト構造

```
minecraft-survival/
├── src/
│   ├── main.ts
│   ├── Game.ts
│   ├── core/
│   │   ├── Engine.ts
│   │   ├── GameLoop.ts
│   │   └── InputManager.ts
│   ├── world/
│   │   ├── World.ts
│   │   ├── Chunk.ts
│   │   ├── ChunkMesher.ts
│   │   └── terrain/
│   │       ├── TerrainGenerator.ts
│   │       └── PerlinNoise.ts
│   ├── player/
│   │   ├── Player.ts
│   │   └── Inventory.ts
│   ├── entities/
│   │   ├── Entity.ts
│   │   ├── EntityManager.ts
│   │   ├── mobs/
│   │   │   ├── Mob.ts
│   │   │   ├── Zombie.ts
│   │   │   ├── Skeleton.ts
│   │   │   ├── Pig.ts
│   │   │   └── Cow.ts
│   │   └── spawner/
│   │       └── MobSpawner.ts
│   ├── rendering/
│   │   └── DayNightCycle.ts
│   ├── ui/
│   │   ├── HUD.ts
│   │   └── ItemRenderer.ts
│   └── types.ts
├── index.html
└── package.json
```

総コード量は約2500行。

## 実装された機能一覧

| カテゴリ | 機能 |
|---------|------|
| ワールド | Perlinノイズ地形生成、洞窟、木、鉱石配置 |
| 操作 | WASD移動、マウス視点、ジャンプ、ダブルタップダッシュ |
| ブロック | 破壊、設置、ジャンプ中足場設置 |
| インベントリ | 36スロット、ホットバー、スタッキング |
| サバイバル | 体力20、空腹度20、自動回復 |
| モブ | ゾンビ、スケルトン、豚、牛 |
| AI | IDLE→WANDER→CHASE→ATTACK状態遷移 |
| 戦闘 | 左クリック攻撃、武器ダメージ、ノックバック |
| 昼夜 | 10分サイクル、空の色変化、夜間敵スポーン |
| UI | ホットバー、体力ゲージ、空腹度、デバッグ情報 |

## 所要時間

トータルで約1時間。内訳：

- 初期実装: 約40分
- フィードバック対応: 約20分

人間が書いたコードは0行。すべてClaudeが生成した。

## 学んだこと

### Claude Codeの得意なこと
- 大規模なコードベースの一貫した構築
- 複数ファイルにまたがるリファクタリング
- エラーの特定と修正

### 人間が担うべきこと
- 仕様の決定と優先順位付け
- 実際にプレイしてのフィードバック
- 「何が足りないか」の判断

「マイクラ作って」という曖昧な指示でも、対話を重ねることで本格的なゲームができた。AIは道具だが、使い方次第で驚くほどの成果が出る。

## 動かし方

```bash
git clone https://github.com/Michey0495/minecraft-survival.git
cd minecraft-survival
npm install
npm run dev
```

http://localhost:5173 でゲームが起動する。

## おわりに

Claude Codeは「プログラミングの民主化」を体現している。ゲーム開発の経験がなくても、作りたいものを言語化できれば形になる。

次は何を作らせようか。
