# Sollumz Model Prepper — 設計レビュー

> v0.2（Codex レビュー反映）  
> 更新日: 2026-06-29

---

## 1. 設計上のリスク

### 1.1 SAFE_AUTO の範囲を厳しく絞った理由

**旧設計の問題:** `normals_make_consistent`・`remove_doubles`・`dissolve_degenerate` を SAFE_AUTO に含めていたが、これらはトポロジーを変更する処理であり「本当に安全」とは言えない。

**リスク例:**
- `remove_doubles`: UV シーム頂点やハードエッジ境界の意図的な重複頂点をマージしてしまう
- `normals_make_consistent`: 建築物内側の壁面（正常な内向き面）を誤って反転させる
- `dissolve_degenerate`: 細長いが意図的なポリゴンを削除してしまう可能性がある

**新設計の対応:**
- `SAFE_AUTO` は `uv_missing` のみ（`uv_layers.new()` はデータ追加のみで既存データへの変更ゼロ）
- 上記 3 処理はすべて `SAFE_MANUAL`（確認ダイアログ付きの個別 Operator）に格下げ
- `REVIEW_REQUIRED` は Fix ボタンなし・警告表示のみ

### 1.2 fix_type の 3 段階整合性

**旧設計の不整合:**
- `transform_scale` の適用が `SAFE_MANUAL` なのに、`normal_flip` や `dupe_vertex` が `SAFE_AUTO` になっていた
- Scale 適用より法線再計算や重複頂点マージのほうが危険なケースが多い（Armature を持たないモデルなら Scale 適用のほうが安全なことすらある）

**新設計での整合性確認:**

| fix_type | 処理例 | 安全の根拠 |
|---|---|---|
| SAFE_AUTO | `uv_layers.new()` | 追加のみ・既存データ無変更 |
| SAFE_MANUAL | `apply_scale`, `normals_make_consistent`, `remove_doubles` | 通常安全だが Armature・UV シーム・内部ジオメトリで例外あり。確認ダイアログで対応。 |
| REVIEW_REQUIRED | `non_manifold`, `uv_out_of_bounds`, `apply_rotation`, マテリアル系 | 意図と自動判定が区別できない・座標系・アニメーションへの影響が大きい |

`SAFE_MANUAL` の基準: 「通常のポリゴンモデル（Armature・形状キーなし）では安全だが、特定状況で破綻する」。

### 1.3 Undo の信頼性

**リスク:** Python から直接 `bpy.data` を操作した場合（`obj.data.uv_layers.new()` 等）は Undo スタックに自動登録されない。

**対応:**
- Fix Operator には必ず `bl_options = {'REGISTER', 'UNDO'}` を付与（Operator 自体が Undo スタックに積まれる）
- `bpy.ops.mesh.*` 経由の操作は `bl_options = {'REGISTER', 'UNDO'}` があれば自動的に Undo に乗る
- `obj.data.uv_layers.new()` のような低レベル操作は、`{'REGISTER', 'UNDO'}` の付いた Operator 内から呼ぶことで Undo が機能する

**注意:** `bpy.ops.ed.undo_push` を手動で呼ぶと Undo スタックが二重になる場合があるため、Fix Operator 内では **使用しない**。`{'REGISTER', 'UNDO'}` の Operator フラグで十分。

### 1.4 bmesh のメモリ管理

**リスク:** `bmesh.new()` は明示的に `bm.free()` しないとメモリリークする。例外発生時も解放が必要。

**対応:** すべての bmesh 使用箇所で `try / finally` を徹底する。

```python
bm = bmesh.new()
try:
    bm.from_mesh(obj.data)
    # ... 処理 ...
finally:
    bm.free()
```

### 1.5 Normal チェックの精度問題

**リスク:** 重心ベースの内向き/外向き判定は近似であり、建築物の内部ジオメトリ・複雑な形状で誤検出が生じる。

**対応:**
- `normal_flip` は **ERROR でなく WARN 止まり** にする（設計書に記載済み）
- message に「内側の壁は意図的な場合があります」の注記を必ず含める
- 誤検出を避けるため `SAFE_AUTO` から外し `SAFE_MANUAL` に

### 1.6 check_results の永続化問題

**リスク:** `check_results` は `.blend` ファイルに保存されるため、古いチェック結果が次のセッションでも表示される。

**対応:**
- `check_status == 'NONE'` または `last_check_time == 0.0` の場合は結果リストを描画しない
- UI に "Run Preflight Check to see results." を表示して再実行を促す
- `.blend` ロード時に `check_status` を自動リセットしない（余計なハックを避ける）

### 1.7 複数オブジェクトチェック時の結果集約

**旧設計の問題:** `last_check_object` は単一オブジェクト名を文字列で持つため、複数選択チェックに対応できなかった。

**新設計:**
- `last_check_object` を廃止
- `last_check_time: FloatProperty`（`time.time()` の値）
- `checked_object_count: IntProperty`
- チェック結果は全選択オブジェクトの結果を flatten して `check_results` に格納
- 同一 check_id が複数オブジェクトから出た場合は、全件格納する（オブジェクト名を message に含める）

---

## 2. Blender API 上の注意点

### 2.1 bpy.ops.mesh.* の壊れやすさ

`bpy.ops.mesh.*` は以下の条件に依存するため、スクリプトから直接呼ぶと壊れやすい。

| 依存条件 | 問題 |
|---|---|
| `context.mode == 'EDIT_MESH'` が必須 | Object モードから呼ぶとエラー |
| `context.active_object` が設定済み | active が None だとエラー |
| 対象オブジェクトが選択状態 | 選択されていない頂点は操作されない |
| `context.area.type == 'VIEW_3D'` | スクリプト実行環境によっては context が VIEW_3D でない |

**対応: `mesh_edit_context` コンテキストマネージャの使用を必須化**

```python
# utils/context_utils.py
@contextmanager
def mesh_edit_context(obj):
    prev_active   = bpy.context.view_layer.objects.active
    prev_mode     = obj.mode
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
                pass  # 処理中に削除されたオブジェクトへのアクセスをガード
        if prev_mode not in ('OBJECT', 'EDIT'):
            bpy.ops.object.mode_set(mode=prev_mode)
```

**可能な処理は bmesh で代替する:**

| bpy.ops 呼び出し | bmesh での代替 |
|---|---|
| `remove_doubles(threshold=t)` | `bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=t)` |
| 重複頂点の検出（読み取り） | `bmesh.ops.find_doubles(bm, verts=bm.verts, dist=t)` |
| ゼロ面積の検出 | `face.calc_area() < 1e-8` |
| 法線再計算（読み取り） | `bm.normal_update()` |
| 法線再計算（書き込み） | `bmesh.ops.recalc_face_normals(bm, faces=bm.faces)` + `bm.to_mesh()` |

チェック処理（読み取り）はすべて bmesh で行い、`bpy.ops.mesh.*` はゼロ依存にする。Fix 処理（書き込み）で `bpy.ops.mesh.*` が必要な場合のみ `mesh_edit_context` を使う。

### 2.2 PropertyGroup の登録順序

`SMPSceneProperties` は `check_results: CollectionProperty(type=SMPCheckResult)` を持つため、`SMPCheckResult` が先に登録されていなければならない。登録順を誤ると `AttributeError` が発生する。

```python
# 正しい登録順
bpy.utils.register_class(SMPCheckResult)       # 1
bpy.utils.register_class(SMPSceneProperties)   # 2（SMPCheckResult を参照）
bpy.utils.register_class(SMPObjectProperties)  # 3
bpy.types.Scene.smp  = PointerProperty(type=SMPSceneProperties)
bpy.types.Object.smp = PointerProperty(type=SMPObjectProperties)

# 正しい解除順（登録と逆順）
del bpy.types.Object.smp
del bpy.types.Scene.smp
bpy.utils.unregister_class(SMPObjectProperties)
bpy.utils.unregister_class(SMPSceneProperties)
bpy.utils.unregister_class(SMPCheckResult)
```

### 2.3 `bpy.ops.object.duplicate` の動作

複製後に `context.active_object` が新オブジェクトになるため、以下の順序で操作する。

```python
original = context.active_object
original_name = original.name
bpy.ops.object.duplicate(linked=False)
col_obj = context.active_object  # 複製後は active が新オブジェクトになっている
assert col_obj.name != original_name
```

Linked Duplicate (`linked=True`) は元メッシュへの編集が連動するため、Collision 専用の簡略化編集ができない。Full Copy のみを提供する。

### 2.4 Collection 間のオブジェクト移動

`unlink` → `link` の順序を守る。`link` を先に行うと同じオブジェクトが複数 Collection に属する状態が発生する。

```python
def move_to_collection(obj, target_collection):
    for col in list(obj.users_collection):  # list() でコピーしてからイテレート
        col.objects.unlink(obj)
    target_collection.objects.link(obj)
```

`obj.users_collection` を直接イテレートしながら `unlink` すると、イテレータが壊れる。必ず `list()` でコピーしてからイテレートする。

### 2.5 Blender 5.x 固有の注意点

- `wm.invoke_confirm` は Blender 4.2 で `message` 引数が追加されたため、5.x では使用可能
- `context.window_manager.invoke_confirm(self, event, message=...)` の形式で使う
- `bpy.ops.ed.undo_push` は 5.x でも機能するが、`{'REGISTER', 'UNDO'}` フラグがある Operator の内部では基本的に不要

### 2.6 `remove_doubles_threshold` の安全域

| 値の範囲 | 評価 |
|---|---|
| `0.00001 〜 0.001` | 安全。精度誤差レベルの重複のみマージ |
| `0.001 〜 0.01` | 概ね安全。UV シーム頂点に注意 |
| `0.01 〜 0.1` | 危険域。意図しない頂点マージの可能性大。UI に警告を表示する |
| `0.1 超` | 使用不可（max = 0.1 で上限を設定） |

デフォルト: `0.0001`。UI 上で `0.01` 超の場合はオレンジの警告ラベルを表示する。

---

## 3. Sollumz 依存を後回しにする理由

### 理由 1: Sollumz の内部 API は非安定

Sollumz はコミュニティ主導のアドオンであり、Property 名・Enum 値・Collection タイプの定義は変更頻度が高い。直接依存するとメンテナンスコストが跳ね上がる。

### 理由 2: MVP の価値は Sollumz 非依存でも成立する

Transform チェック・Geometry チェック・UV チェックは純粋な Blender メッシュ品質の問題であり、Sollumz と無関係に有用。「Sollumz を使う前の下準備」としての価値がそのまま提供できる。

### 理由 3: 段階的な依存追加が安全

`is_sollumz_available()` で分岐し、後から拡張できる。最初から依存を前提にすると、Sollumz のバージョン差異でアドオン全体が動かなくなるリスクがある。

```python
def is_sollumz_available() -> bool:
    return "sollumz" in bpy.context.preferences.addons

# 使用例（UI パネル内）
if is_sollumz_available():
    layout.operator("smp.set_sollumz_type", icon='SETTINGS')
```

---

## 4. MVP でやらないこと

| 項目 | 理由 |
|---|---|
| Material / Texture チェック詳細 | チェック数を増やす前に基盤チェックを安定させる |
| Fix Safe Issues 一括修正 | SAFE_AUTO が `uv_missing` だけなら優先度が低い。Post-MVP で追加 |
| Apply Scale / Rotation Operator | Preflight Check が先。Fix は後から追加 |
| Collision Base Copy 生成 | Collection 構造が確定してから実装する |
| Room Box / Portal Plane | Sollumz の Room / Portal API が安定するまで実装しない |
| Sollumz 固有 Property 設定 | API 不安定性リスクと MVP での必要性の低さ |
| Export Ready 判定バッジ | 全チェックが安定してから追加 |
| バッチ処理（シーン全体） | 安全確認の機会を減らす。選択オブジェクトへの個別実行を基本とする |
| Linked Duplicate による Collision 生成 | Full Copy のみに絞ってシンプルにする |

---

## 5. 今後の拡張方針

### フェーズ 2: Fix Operator 群（MVP 直後）

優先順位順:
1. T-011 `fix_safe_issues` — SAFE_AUTO の一括修正（uv_missing 対応）
2. T-012 `apply_scale` — Scale 適用（最も安全な SAFE_MANUAL）
3. T-013 `recalc_normals` — 法線再計算
4. T-014 `merge_doubles` — 重複頂点マージ（閾値警告付き）
5. T-015 `dissolve_degenerate` — ゼロ面積面削除

### フェーズ 3: Collision Base Copy（フェーズ 2 完了後）

- T-016 `create_collision_base_copy` — Full Copy のみ
- Collection 構造が T-003 で確立されていることが前提

### フェーズ 4: Sollumz 連携

- `is_sollumz_available()` で分岐
- Sollumz の Collection Type 自動設定
- Drawable Model タイプ設定補助
- Export Ready 判定バッジ

### フェーズ 5: Room / Portal（Sollumz API 安定後）

- Sollumz の Room / Portal API が安定したタイミングで実装
- それまでは Collection の `_portals` を空で確保しておくだけで十分

### 拡張ポイントの実装指針

- チェック関数の追加: `checks/` にファイルを追加して `CHECK_FUNCTIONS` リストに追加するだけ
- Fix Operator の追加: `fix_ops.py` に追加し、`fix_op_map` 辞書（UI パネル内）に check_id → operator_id の対応を追記
- Sollumz 連携コードは `integration/sollumz_bridge.py` に分離して本体コードへの汚染を防ぐ
