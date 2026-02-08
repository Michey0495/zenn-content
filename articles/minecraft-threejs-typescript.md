---
title: "Three.js + TypeScriptでブラウザで動くマインクラフト風サバイバルゲームを作った"
emoji: "⛏️"
type: "tech"
topics: ["threejs", "typescript", "gamedev", "vite", "webgl"]
published: true
---

## 作ったもの

Three.jsとTypeScriptを使って、ブラウザ上で動作するマインクラフト風のサバイバルゲームを作りました。

主な機能：
- Perlinノイズによる地形生成（山、洞窟、木）
- ブロックの破壊・設置
- インベントリとホットバー
- 昼夜サイクル
- 敵モブ（ゾンビ、スケルトン）と友好モブ（豚、牛）
- 体力・空腹度システム
- ダブルタップダッシュ、ジャンプ中の足場設置

## 技術スタック

| 項目 | 技術 |
|------|------|
| 3D描画 | Three.js |
| 言語 | TypeScript |
| ビルド | Vite |
| 操作 | Pointer Lock API |

ワールドサイズは128x128x64ブロック固定。データは`Uint8Array`で約1MBに収まります。

## プロジェクト構造

```
minecraft-survival/
├── src/
│   ├── main.ts           # エントリーポイント
│   ├── Game.ts           # ゲームメインループ
│   ├── core/             # エンジン、入力管理
│   ├── world/            # ワールド、チャンク、地形生成
│   ├── player/           # プレイヤー、インベントリ
│   ├── entities/         # モブ、AI
│   ├── rendering/        # 昼夜サイクル
│   └── ui/               # HUD、アイテムレンダラー
└── index.html
```

## 実装のポイント

### 1. Perlinノイズによる地形生成

地形生成の核となるのがPerlinノイズです。2Dノイズを組み合わせて自然な地形を作ります。

```typescript
// TerrainGenerator.ts より抜粋
private getHeight(x: number, z: number): number {
  // 複数のオクターブを重ねる
  let height = 0
  let amplitude = 1
  let frequency = 0.02

  for (let i = 0; i < 4; i++) {
    height += this.noise.noise2D(x * frequency, z * frequency) * amplitude
    amplitude *= 0.5
    frequency *= 2
  }

  // 基本の高さ + ノイズによる変動
  return Math.floor(this.baseHeight + height * 15)
}
```

洞窟生成には3Dノイズを使用。閾値を超えた箇所を空洞にします。

```typescript
private generateCaves(x: number, y: number, z: number): boolean {
  const caveNoise = this.noise.noise3D(
    x * 0.05,
    y * 0.08,
    z * 0.05
  )
  return caveNoise > 0.6  // この値を超えると洞窟
}
```

### 2. チャンクメッシュ生成

1ブロックごとにキューブを描画すると重すぎるので、隣接ブロックに面している面は描画しません。

```typescript
// ChunkMesher.ts より
for (let faceIndex = 0; faceIndex < FACES.length; faceIndex++) {
  const face = FACES[faceIndex]
  const [dx, dy, dz] = face.dir

  const neighborBlock = world.getBlock(
    worldX + dx,
    y + dy,
    worldZ + dz
  )

  // 隣が透明なブロックなら面を描画
  if (isBlockTransparent(neighborBlock)) {
    this.addFace(positions, normals, colors, indices, ...)
  }
}
```

この最適化により、描画するポリゴン数を大幅に削減できます。

### 3. DDAレイキャスト

プレイヤーの視線がどのブロックを指しているかを判定するのにDDA（Digital Differential Analyzer）アルゴリズムを使います。

```typescript
private raycastBlock(getAdjacent: boolean): { x, y, z } | null {
  // 視線の方向ベクトル
  const direction = new THREE.Vector3(0, 0, -1)
    .applyAxisAngle(new THREE.Vector3(1, 0, 0), this.pitch)
    .applyAxisAngle(new THREE.Vector3(0, 1, 0), this.yaw)

  // DDAで1ブロックずつ進む
  let x = Math.floor(eyePos.x)
  let y = Math.floor(eyePos.y)
  let z = Math.floor(eyePos.z)

  const stepX = direction.x > 0 ? 1 : -1
  const stepY = direction.y > 0 ? 1 : -1
  const stepZ = direction.z > 0 ? 1 : -1

  // tMaxは次の境界までの距離
  let tMaxX = direction.x > 0
    ? (x + 1 - eyePos.x) / direction.x
    : (eyePos.x - x) / (-direction.x)
  // ...

  for (let i = 0; i < maxSteps; i++) {
    const block = world.getBlock(x, y, z)
    if (block !== BlockType.AIR) {
      return getAdjacent
        ? { x: lastX, y: lastY, z: lastZ }
        : { x, y, z }
    }
    // 最も近い境界の方向に進む
    if (tMaxX < tMaxY && tMaxX < tMaxZ) {
      x += stepX
      tMaxX += tDeltaX
    } else if (tMaxY < tMaxZ) {
      y += stepY
      tMaxY += tDeltaY
    } else {
      z += stepZ
      tMaxZ += tDeltaZ
    }
  }
  return null
}
```

`getAdjacent`フラグで、ブロック破壊（選択したブロック自体）かブロック設置（選択したブロックの手前）を切り替えます。

### 4. 昼夜サイクル

ゲーム内時間を0〜1の値で管理し、太陽の位置と空の色を連動させます。

```typescript
// DayNightCycle.ts
update(deltaTime: number): void {
  // 10分で1日
  this._time += deltaTime / 600
  if (this._time >= 1) this._time -= 1

  // 太陽の位置を半円運動で計算
  const sunAngle = (this._time - 0.25) * Math.PI * 2
  const sunHeight = Math.sin(sunAngle)
  this.sunLight.position.set(
    Math.cos(sunAngle) * 100,
    sunHeight * 100 + 20,
    50
  )
}
```

空の色は時間帯で補間します。

```typescript
private calculateSkyColor(time: number): number {
  if (time < 0.2 || time > 0.85) {
    return 0x001122  // 夜
  } else if (time < 0.3) {
    // 日の出: 夜 → 朝焼け
    return this.lerpColor(0x001122, 0xffaa66, (time - 0.2) / 0.1)
  } else if (time < 0.4) {
    // 朝: 朝焼け → 昼
    return this.lerpColor(0xffaa66, 0x87ceeb, (time - 0.3) / 0.1)
  }
  // ...
}
```

### 5. モブのAI

モブは状態機械で行動を制御します。

```typescript
// Zombie.ts
updateAI(player: Player): void {
  const distToPlayer = this.distanceToPlayer(player)

  switch (this.aiState) {
    case AIState.IDLE:
      if (distToPlayer < 16) {
        this.aiState = AIState.CHASE
      } else if (this.stateTimer > 3) {
        this.aiState = AIState.WANDER
      }
      break

    case AIState.CHASE:
      if (distToPlayer > 20) {
        this.aiState = AIState.WANDER
      } else if (distToPlayer < this.attackRange) {
        this.aiState = AIState.ATTACK
      } else {
        this.moveTowards(player.position, this.moveSpeed)
      }
      break

    case AIState.ATTACK:
      if (distToPlayer > this.attackRange) {
        this.aiState = AIState.CHASE
      } else {
        this.attackPlayer(player)
      }
      break
    // ...
  }
}
```

夜間のみ敵モブがスポーンするようにMobSpawnerで制御しています。

### 6. ジャンプ中の足場設置

マインクラフトの定番テクニック「ジャンプしながら真下にブロックを置く」を実装。

```typescript
// Player.ts
if (input.isMouseButtonPressed(2)) {
  const lookingDown = this.pitch < -0.8
  const target = lookingDown
    ? this.getBlockBelowPlayer()
    : this.raycastBlock(true)

  if (target && blockType !== undefined) {
    // 真下を向いてジャンプ中なら衝突チェックをスキップ
    if (lookingDown && !this.isGrounded) {
      this.world.setBlockAndUpdate(target.x, target.y, target.z, blockType)
      this.inventory.decrementSlot(this.selectedSlot)
    }
    // 通常時は衝突チェック
    // ...
  }
}
```

### 7. ピクセルアート風アイテムアイコン

Canvas APIで16x16のピクセルアートを動的に生成しています。

```typescript
// ItemRenderer.ts
function createPickaxePattern(headColor: string, handleColor: string): PixelPattern {
  const pattern: PixelPattern = []
  for (let y = 0; y < 16; y++) {
    const row: (string | null)[] = []
    for (let x = 0; x < 16; x++) {
      // ヘッド部分
      if (y <= 4 && x >= 2 && x <= 13) {
        row.push(headColor)
      }
      // 柄
      else if (x >= 7 && x <= 8 && y >= 5 && y <= 14) {
        row.push(handleColor)
      } else {
        row.push(null)
      }
    }
    pattern.push(row)
  }
  return pattern
}
```

アイテムごとにパターンを定義し、キャッシュしてData URLとして返します。

## 苦労した点

### 頂点の巻き順

Three.jsはデフォルトで反時計回りを表面として扱います。最初これを理解せず、一部の面が表示されない問題に悩まされました。

結局`THREE.DoubleSide`で両面レンダリングにして解決。パフォーマンスへの影響は軽微でした。

```typescript
const material = new THREE.MeshLambertMaterial({
  vertexColors: true,
  side: THREE.DoubleSide,  // 両面レンダリング
})
```

### ブロック破壊とアイテムドロップの連携

ブロックを壊したときにアイテムをインベントリに追加する処理で、ブロックタイプとアイテムIDのマッピングが必要でした。

```typescript
const BLOCK_TO_ITEM: Partial<Record<BlockType, string>> = {
  [BlockType.GRASS]: 'dirt',   // 草ブロック → 土
  [BlockType.STONE]: 'cobblestone',  // 石 → 丸石
  [BlockType.COAL_ORE]: 'coal',
  // ...
}
```

## まとめ

Three.jsとTypeScriptを使えば、ブラウザ上でかなり本格的な3Dゲームが作れます。今回のプロジェクトは約2000行程度のコードで、基本的なマインクラフトの要素を再現できました。

今後追加したい機能：
- クラフトUI
- セーブ/ロード（LocalStorage）
- マルチプレイ（WebSocket）
- テクスチャアトラス

ソースコードはGitHubで公開予定です。

## 参考

- [Three.js Documentation](https://threejs.org/docs/)
- [Voxel.js](http://voxeljs.com/) - ボクセルゲームフレームワーク
- [Let's Make a Voxel Engine](https://sites.google.com/site/letsmakeavoxelengine/) - ボクセルエンジンの作り方
