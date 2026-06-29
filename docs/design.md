# Sollumz Model Prepper — アドオン設計書

> バージョン: MVP 0.2（Codex レビュー反映）  
> 対象: Blender 5.x / Sollumz 最新安定版  
> 更新日: 2026-06-29

---

## 1. アドオン概要

### 目的

Sollumz (GTA V / FiveM 向け Blender アドオン) によるエクスポート前に、ユーザーが自前で用意した建物・内装モデルを整理・検査・半自動変換する補助アドオン。

### 設計原則

| 原則 | 内容 |
|---|---|
| 非破壊優先 | 自動修正は「本当に安全」な処理のみ。それ以外は明示的ワンクリックで実行 |
| 半自動 | SAFE_AUTO はゼロに近くて良い。確認ダイアログのある SAFE_MANUAL を標準とする |
| Sollumz 非依存 MVP | MVP では Sollumz がインストールされていなくても動作する |
| 1 Operator 1 責務 | 各 Operator は単一の目的を持ち、副作用を最小化する |
| bmesh ベース実装 | メッシュ操作は可能な限り bmesh で行い、`bpy.ops.mesh.*` への依存を最小化する |
| 明示的エラー表示 | チェック結果はすべて UI に色分けで表示し、ユーザーが判断できるようにする |

### Sollumz との関係

```
[ユーザーモデル]
      │
      ▼
[Sollumz Model Prepper]  ← このアドオン
  ・Collection 構築補助
  ・Preflight Check
  ・安全な自動修正（範囲を限定）
  ・Collision Base Copy 生成
      │
      ▼
[Sollumz]
  ・固有 Property 設定
  ・Export (.ymap / .ydr / .ybn 等)
```

---

## 2. ファイル構成

```
sollumz_model_prepper/
├── __init__.py               # アドオン登録・bl_info
├── preferences.py            # AddonPreferences
│
├── properties/
│   ├── __init__.py           # 登録・解除（順序厳守）
│   ├── check_result.py       # SMPCheckResult
│   ├── scene_props.py        # SMPSceneProperties
│   └── object_props.py       # SMPObjectProperties
│
├── operators/
│   ├── __init__.py
│   ├── collection_ops.py     # MLO Collection 作成系
│   ├── check_ops.py          # Preflight Check 実行系
│   ├── fix_ops.py            # 修正系（SAFE_MANUAL / SAFE_AUTO）
│   └── collision_ops.py      # Collision Base Copy 生成（Post-MVP）
│
├── checks/
│   ├── __init__.py           # run_all_checks() エントリポイント
│   ├── result.py             # CheckResult dataclass
│   ├── transform_check.py    # Transform 未適用チェック
│   ├── normal_check.py       # Normal 方向チェック
│   ├── geometry_check.py     # 重複頂点 / 非多様体 / ゼロ面積チェック
│   ├── uv_check.py           # UV マップチェック
│   └── material_check.py     # マテリアル / テクスチャチェック（Post-MVP）
│
├── ui/
│   ├── __init__.py
│   ├── panel_main.py         # メインパネル (N パネル > SMP タブ)
│   ├── panel_collection.py   # Collection セクション
│   ├── panel_preflight.py    # Preflight Check セクション
│   └── panel_collision.py    # Collision セクション（Post-MVP）
│
└── utils/
    ├── __init__.py
    ├── bmesh_utils.py        # BMesh 操作ユーティリティ（コンテキスト管理込み）
    ├── collection_utils.py   # Collection 操作ユーティリティ
    └── context_utils.py      # モード保存・復元ユーティリティ
```

---

## 3. UI 構成

### 配置

3D Viewport サイドバー (N パネル) > **「SMP」タブ**

### MVP パネル階層

```
[SMP] タブ
│
├── [Collection Setup]
│   ├── MLO 名入力フィールド
│   └── [Create MLO Collection] ボタン
│
└── [Preflight Check]
    ├── [Run Preflight Check] ボタン  ← 選択オブジェクト対象
    ├── チェック済みオブジェクト数・実行時刻の表示
    ├── チェック結果リスト
    │   ├── ✅ UV Map: OK
    │   ├── ⚠️  Normals: 12 faces may be flipped  [Fix (要確認)]
    │   ├── ⚠️  Duplicate Vertices: 8 found        [Fix (要確認)]
    │   └── ❌ Scale Not Applied                   [Apply Scale]
    └── [Fix Safe Issues] ボタン  ← SAFE_AUTO のみ（MVP では uv_missing 相当）
```

### Post-MVP パネル（追加予定）

```
└── [Collision]
    ├── 複製モード選択 (Full Copy のみ推奨)
    └── [Create Collision Base Copy] ボタン
```

### 色分けルール

| 状態 | アイコン | 意味 |
|---|---|---|
| OK | `CHECKMARK` | 問題なし |
| Warning | `ERROR` | 修正推奨・動作はする |
| Error | `CANCEL` | Export 前に修正必須 |
| Info | `INFO` | 情報のみ・修正不要 |

---

## 4. PropertyGroup 設計

### 4.1 登録順序（厳守）

`register()` では以下の順に登録する。`unregister()` は**逆順**。

```python
# register()
bpy.utils.register_class(SMPCheckResult)       # 1. 要素型を先に
bpy.utils.register_class(SMPSceneProperties)   # 2. CollectionProperty が SMPCheckResult を参照
bpy.utils.register_class(SMPObjectProperties)  # 3.
bpy.types.Scene.smp  = PointerProperty(type=SMPSceneProperties)   # 4. 最後にポインタ登録
bpy.types.Object.smp = PointerProperty(type=SMPObjectProperties)  # 4.

# unregister() — 逆順
del bpy.types.Object.smp
del bpy.types.Scene.smp
bpy.utils.unregister_class(SMPObjectProperties)
bpy.utils.unregister_class(SMPSceneProperties)
bpy.utils.unregister_class(SMPCheckResult)
```

### 4.2 SMPCheckResult

```python
class SMPCheckResult(PropertyGroup):
    check_id:     StringProperty()
    check_name:   StringProperty()
    status:       EnumProperty(items=[('OK','OK',''), ('WARN','Warning',''), ('ERROR','Error','')])
    message:      StringProperty()
    fix_type:     EnumProperty(items=[
        ('NONE',            'No Fix',          ''),
        ('SAFE_AUTO',       'Safe Auto',       '確認不要で自動修正可能（非常に限定的）'),
        ('SAFE_MANUAL',     'Safe Manual',     '確認ダイアログ付きで実行'),
        ('REVIEW_REQUIRED', 'Review Required', 'ユーザーが手動で対応・自動修正なし'),
    ])
    detail_count: IntProperty()
```

### 4.3 SMPSceneProperties

```python
class SMPSceneProperties(PropertyGroup):
    mlo_name: StringProperty(
        name="MLO Name",
        default="MyMLO"
    )
    # last_check_object は廃止。複数選択対応のため以下に変更。
    last_check_time:          FloatProperty(default=0.0)   # time.time() の値
    checked_object_count:     IntProperty(default=0)
    check_results:            CollectionProperty(type=SMPCheckResult)
    check_status:             EnumProperty(
        items=[('NONE','Not Run',''), ('PASS','Pass',''), ('WARN','Warning',''), ('FAIL','Fail','')],
        default='NONE'
    )
    remove_doubles_threshold: FloatProperty(
        name="Merge Distance",
        description="重複頂点をマージする距離閾値（0.01 超は要注意）",
        default=0.0001,
        min=0.00001,
        max=0.1,
        precision=5,
        step=1
    )
    # collision_link_mode は Post-MVP まで保留
```

**`remove_doubles_threshold` の運用ルール:**
- デフォルト: `0.0001`（モデリング精度の範囲内）
- UI 上の "安全域" 表示: `0.0001 〜 0.01`
- `0.01` 超: UI に `⚠ 大きな値はモデルを破壊する可能性があります` の警告ラベルを表示
- 閾値の変更は Fix 実行直前にのみ反映（プレビューなし）

### 4.4 SMPObjectProperties

```python
class SMPObjectProperties(PropertyGroup):
    is_collision_base_copy:  BoolProperty(
        name="Is Collision Base Copy",
        description="このオブジェクトが Collision Base Copy であることを示す",
        default=False
    )
    source_object_name:      StringProperty(
        name="Source Object",
        description="Collision Base Copy の複製元オブジェクト名"
    )
    preflight_passed:        BoolProperty(default=False)
    preflight_timestamp:     FloatProperty(default=0.0)
```

---

## 5. Operator 一覧

### 5.1 Collection Operators

| ID | クラス名 | 説明 |
|---|---|---|
| `smp.create_mlo_collection` | `SMP_OT_CreateMLOCollection` | MLO 用 Collection 階層を作成 |

**作成 Collection 構造:**
```
[MLO_{name}]
├── [MLO_{name}_entities]
├── [MLO_{name}_collision]
└── [MLO_{name}_portals]   # 空・将来用
```

### 5.2 Check Operators

| ID | クラス名 | 説明 |
|---|---|---|
| `smp.run_preflight` | `SMP_OT_RunPreflight` | 選択メッシュの Preflight Check 実行 |

### 5.3 Fix Operators（MVP: SAFE_AUTO + SAFE_MANUAL）

| ID | クラス名 | 対象 check_id | 分類 |
|---|---|---|---|
| `smp.fix_safe_issues` | `SMP_OT_FixSafeIssues` | SAFE_AUTO 全件 | SAFE_AUTO |
| `smp.apply_scale` | `SMP_OT_ApplyScale` | transform_scale | SAFE_MANUAL |
| `smp.recalc_normals` | `SMP_OT_RecalcNormals` | normal_flip | SAFE_MANUAL |
| `smp.merge_doubles` | `SMP_OT_MergeDoubles` | dupe_vertex | SAFE_MANUAL |
| `smp.dissolve_degenerate` | `SMP_OT_DissolveDegenerate` | zero_area_face | SAFE_MANUAL |

> REVIEW_REQUIRED 項目には Fix ボタンを表示しない。警告メッセージのみ。

### 5.4 Post-MVP Operators

| ID | クラス名 | 説明 |
|---|---|---|
| `smp.apply_rotation` | `SMP_OT_ApplyRotation` | Rotation 適用（Post-MVP） |
| `smp.create_collision_base_copy` | `SMP_OT_CreateCollisionBaseCopy` | Collision Base Copy 生成 |

---

## 6. Preflight Check 項目

### check_id ごとの定義

| check_id | 名称 | 検査内容 | 重大度 | fix_type |
|---|---|---|---|---|
| `transform_scale` | Scale Not Applied | scale != (1,1,1) | ERROR | SAFE_MANUAL |
| `transform_rotation` | Rotation Not Applied | rotation_euler != (0,0,0) | WARN | REVIEW_REQUIRED |
| `transform_location` | Non-zero Origin | location != (0,0,0) | INFO | REVIEW_REQUIRED |
| `normal_flip` | Flipped Normals | 内向き疑い面の数 | WARN | SAFE_MANUAL |
| `dupe_vertex` | Duplicate Vertices | 重複頂点数（bmesh find_doubles） | WARN | SAFE_MANUAL |
| `non_manifold` | Non-Manifold Geometry | 非多様体エッジ・頂点数 | ERROR | REVIEW_REQUIRED |
| `zero_area_face` | Zero Area Faces | 面積 < 1e-8 の面数 | WARN | SAFE_MANUAL |
| `uv_missing` | No UV Map | UV レイヤーが存在しない | ERROR | SAFE_AUTO |
| `uv_out_of_bounds` | UV Out of Bounds | [0,1]×[0,1] 外の UV 頂点数 | WARN | REVIEW_REQUIRED |
| `loose_geo` | Loose Geometry | 面に繋がっていない辺・頂点 | WARN | REVIEW_REQUIRED |
| `mat_missing` | No Material Slot | material_slots が空 | ERROR | REVIEW_REQUIRED |
| `mat_empty_slot` | Empty Material Slot | slot.material is None | WARN | REVIEW_REQUIRED |
| `tex_missing` | Missing Texture | Image Texture ノードに image なし | WARN | REVIEW_REQUIRED |

> `mat_missing` / `mat_empty_slot` / `tex_missing` は **Post-MVP** に分類（`material_check.py` は後から追加）。

### fix_type の 3 段階定義

| 分類 | 定義 | 典型例 |
|---|---|---|
| **SAFE_AUTO** | トポロジー・テクスチャ・アニメーションへの影響がゼロまたはほぼゼロ。Undo ポイントを設定して自動実行可能。 | `uv_missing`（空 UV レイヤー追加のみ） |
| **SAFE_MANUAL** | 通常は安全だが、Armature・アニメーション・子オブジェクトなど特定状況で影響が出る可能性がある。確認ダイアログ付きで個別実行。 | `transform_scale`, `normal_flip`, `dupe_vertex`, `zero_area_face` |
| **REVIEW_REQUIRED** | トポロジー変更・意図との区別が不可能・座標系への影響など、アドオンが自動修正すべきでない処理。警告のみ、Fix ボタンなし。 | `non_manifold`, `uv_out_of_bounds`, `transform_rotation`, 全マテリアル系 |

---

## 7. SAFE_AUTO の範囲と根拠

### MVP で SAFE_AUTO に含めるもの

| check_id | 操作 | 安全と言える根拠 |
|---|---|---|
| `uv_missing` | `obj.data.uv_layers.new(name="UVMap")` | 既存データへの変更ゼロ。UV レイヤーを追加するだけで、既存 UV・頂点・面には触れない |

### MVP で SAFE_AUTO から外した理由

| 操作 | 外した理由 |
|---|---|
| `normals_make_consistent` | ダブルサイド面・内部ジオメトリ・インバートされた意図の面で誤動作する |
| `remove_doubles` | 隣接する意図的な重複頂点（ハードエッジ境界、UV シーム頂点）を誤マージする |
| `dissolve_degenerate` | 面積がほぼゼロの意図的な面（細長いポリゴン）を削除してしまう可能性がある |
| `apply_scale` / `apply_rotation` | Armature、形状キー、子オブジェクトがある場合に破綻する |

---

## 8. bpy.ops.mesh.* の扱い方針

### 基本方針: bmesh ベースを優先

チェック処理・読み取り操作はすべて bmesh で行い、`bpy.ops.mesh.*` に依存しない。

```python
import bmesh

bm = bmesh.new()
try:
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    # ... チェック処理 ...
finally:
    bm.free()
```

### bpy.ops.mesh.* を使う場合の必須ルール

Fix 処理で `bpy.ops.mesh.*` を使う場合（`normals_make_consistent` 等）は、以下のラッパーを経由して実行する。

```python
# utils/context_utils.py

import bpy
from contextlib import contextmanager

@contextmanager
def mesh_edit_context(obj):
    """
    オブジェクトを Edit モードに切り替えて処理し、
    終了後に元のモード・アクティブオブジェクト・選択状態を復元する。
    例外発生時も必ず復元を保証する。
    """
    prev_active = bpy.context.view_layer.objects.active
    prev_mode   = obj.mode
    prev_selected = [(o, o.select_get()) for o in bpy.context.view_layer.objects]

    try:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        yield
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = prev_active
        for o, sel in prev_selected:
            try:
                o.select_set(sel)
            except ReferenceError:
                pass  # オブジェクトが削除されている場合
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=prev_mode)
```

**使用例:**
```python
with mesh_edit_context(obj):
    bpy.ops.mesh.normals_make_consistent(inside=False)
```

### bmesh で直接修正できる操作

以下は `bpy.ops` を使わず bmesh だけで完結できる。

| 処理 | bmesh API |
|---|---|
| 重複頂点マージ | `bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=threshold)` |
| ゼロ面積面の検出 | `face.calc_area() < 1e-8` で列挙（削除は手動） |
| 法線再計算 | `bm.normal_update()` + `bmesh.ops.recalc_face_normals` |
| 空 UV レイヤー追加 | `bm.loops.layers.uv.new("UVMap")` または `obj.data.uv_layers.new()` |

bmesh で修正した場合は `bm.to_mesh(obj.data)` で反映し、`obj.data.update()` を呼ぶ。

---

## 9. Preflight Check 実行フローと結果初期化ルール

### 実行フロー

```
SMP_OT_RunPreflight.execute()
    │
    ├── poll(): active_object が MESH かつ Object モードであることを確認
    │
    ├── 1. bpy.ops.ed.undo_push(message="SMP: Run Preflight") は不要
    │      （チェックのみで破壊的操作なし）
    │
    ├── 2. scene.smp.check_results.clear()  ← 必ず古い結果を消す
    │
    ├── 3. 選択中の MESH オブジェクトを収集
    │      non-MESH は skip（INFO レポート）
    │
    ├── 4. 各オブジェクトに run_all_checks(obj) を呼ぶ
    │      → list[CheckResult] を受け取り check_results に格納
    │
    ├── 5. scene.smp.checked_object_count = len(checked_objects)
    │      scene.smp.last_check_time = time.time()
    │
    └── 6. check_status を集計して更新
           ERROR が 1 件以上 → FAIL
           WARN が 1 件以上  → WARN
           すべて OK         → PASS
```

### 保存ファイルでの古い結果の扱い

`check_results` は `bpy.types.Scene` に格納されるため .blend ファイルに残る。以下のルールで UI が古い結果を表示しないようにする。

- `check_status == 'NONE'` の場合は "Run Preflight Check to see results" を表示し、結果リストを描画しない
- `last_check_time` が 0.0 の場合も同様（初回起動・未実行扱い）
- .blend を開いた時点では `check_status` を `'NONE'` にリセットする必要はない（再実行を促す UI 文言で十分）
- チェック結果に依存した自動処理は行わない（ユーザーが必ず再実行してから Fix を使う）

---

## 10. Collision Base Copy の設計

### 用語の統一

| 旧表現（廃止） | 新表現 |
|---|---|
| Collision 生成 | Collision Base Copy 生成 |
| Generate Collision | Create Collision Base Copy |
| `generate_collision_base` | `create_collision_base_copy` |
| `is_collision_base` | `is_collision_base_copy` |
| Collision 複製元 | Collision Base Copy の Source |

### 目的と位置付け

- Collision Base Copy は「完成した Collision」ではなく、**Sollumz 側で Collision Material を設定するための下地**
- 生成したオブジェクトには `smp.is_collision_base_copy = True` を付与して識別
- Collision の最適化・LOD 設定は Sollumz が担当

### 生成フロー（Post-MVP 実装）

```
SMP_OT_CreateCollisionBaseCopy.execute()
    │
    ├── 前提チェック:
    │   ├── 選択オブジェクトが MESH であること
    │   ├── [MLO_{mlo_name}_collision] が存在すること（なければ WARN）
    │   └── 既に is_collision_base_copy == True でないこと
    │
    ├── bpy.ops.ed.undo_push(message="SMP: Create Collision Base Copy")
    ├── bpy.ops.object.duplicate(linked=False)  ← Full Copy のみ（Linked は廃止）
    ├── col_obj.name = f"{original.name}_col"
    ├── col_obj.smp.is_collision_base_copy = True
    ├── col_obj.smp.source_object_name = original.name
    └── move_to_collection(col_obj, collision_collection)
```

**Linked Duplicate を廃止した理由:** Linked Duplicate は元メッシュの編集が Collision 側に連動するため、Collision 専用の簡略化編集ができない。Full Copy のみを提供し、シンプルさを優先する。

---

## 11. Sollumz 連携の拡張ポイント（Post-MVP）

### Sollumz 検出

```python
def is_sollumz_available() -> bool:
    return "sollumz" in bpy.context.preferences.addons
```

Sollumz が存在しない場合は該当ボタンを非表示にする（エラーにしない）。

### 拡張ポイント一覧

| 拡張項目 | 連携方法 | 優先度 |
|---|---|---|
| Sollumz Collection タイプ自動設定 | `getattr(obj, 'sollumz_type', None)` 経由で書き込み | High |
| Export Ready 判定バッジ | 全 Preflight Check が PASS 以上であることを確認 | High |
| Drawable Model タイプ設定 | `drawable_model_type` Enum 書き込み | Medium |
| Collision Material 割当補助 | Sollumz の Collision Material Enum 読込 | Medium |
| Room Box 作成 | Room プロパティと連動 | Low |
| Portal Plane 作成 | Portal プロパティと連動 | Low |

---

## 12. 将来機能（MVP 外）

### Room / Portal（設計のみ・実装は後回し）

```
[MLO_Room]
├── Room Box Mesh（各部屋の境界）
├── Portal Plane Mesh（部屋間の開口部）
└── Portal Direction（法線で From/To を定義）
```

Sollumz の Room / Portal API が安定するまで実装しない。

### Export Ready 判定

- 全 Preflight Check が PASS または INFO
- Sollumz Collection タイプが設定済み
- Collision Base Copy が存在する（WARN レベル）
- UI の最上部にバッジとして表示
