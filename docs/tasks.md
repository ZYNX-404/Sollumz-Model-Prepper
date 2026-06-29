# Sollumz Model Prepper — 実装タスク一覧

> Codex 渡し用（v0.2 Codex レビュー反映）  
> MVP = T-001 〜 T-009。Post-MVP = T-010 以降。  
> 更新日: 2026-06-29

---

## タスク依存グラフ

```
T-001 (アドオン骨格)
    └── T-002 (PropertyGroup 登録)
            ├── T-003 (Collection Operator)
            ├── T-004 (Preflight 基盤 + context_utils)
            │       ├── T-005 (Transform Check)
            │       ├── T-006 (Normal Check)
            │       ├── T-007 (Geometry Check)
            │       └── T-008 (UV Check)
            └── T-009 (MVP 最小 UI パネル)
                    [MVP 完成]

Post-MVP:
T-010 (Material/Texture Check)   ← T-004 後
T-011 (Fix Safe Issues Operator) ← T-008 後
T-012 (Apply Scale Operator)     ← T-011 後
T-013 (Recalc Normals Operator)  ← T-011 後
T-014 (Merge Doubles Operator)   ← T-011 後
T-015 (Dissolve Degenerate)      ← T-011 後
T-016 (Collision Base Copy)      ← T-003 後
T-017 (フル UI パネル)           ← T-011, T-016 後
T-018 (結合テスト)               ← T-017 後
```

---

## MVP タスク群

---

## T-001: アドオン骨格の作成

**目的:** Blender に登録できる最小限のアドオン構造を作成する。

**対象ファイル:**
- `sollumz_model_prepper/__init__.py`
- `sollumz_model_prepper/preferences.py`

**実装内容:**

`bl_info` 辞書:
```python
bl_info = {
    "name": "Sollumz Model Prepper",
    "author": "ZYNX-404",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "category": "Object",
    "description": "Prepare models for Sollumz (GTA V / FiveM) export",
}
```

`__init__.py`:
- サブパッケージ (`properties`, `operators`, `checks`, `ui`) の `register()` / `unregister()` を呼ぶ一括管理
- `register()` の呼び出し順: `properties` → `operators` → `ui`
- `unregister()` の呼び出し順: `ui` → `operators` → `properties`（逆順）

`preferences.py`:
- `SMPAddonPreferences(AddonPreferences)` のスタブ（設定項目は後続タスクで追加）

**完了条件:**
- Edit > Preferences > Add-ons にアドオンが表示される
- Enable/Disable でエラーが発生しない

**テスト方法:**
```python
import importlib, sollumz_model_prepper
importlib.reload(sollumz_model_prepper)
# エラーなく完了すること
```

---

## T-002: PropertyGroup の定義と登録

**目的:** チェック結果・設定値を保持する PropertyGroup を Blender のデータとして登録する。

**前提タスク:** T-001

**対象ファイル:**
- `sollumz_model_prepper/properties/check_result.py`
- `sollumz_model_prepper/properties/scene_props.py`
- `sollumz_model_prepper/properties/object_props.py`
- `sollumz_model_prepper/properties/__init__.py`

**実装内容:**

`check_result.py` — `SMPCheckResult(PropertyGroup)`:
```python
check_id:     StringProperty()
check_name:   StringProperty()
status:       EnumProperty(items=[('OK','OK',''), ('WARN','Warning',''), ('ERROR','Error','')])
message:      StringProperty()
fix_type:     EnumProperty(items=[
    ('NONE',            'No Fix',          ''),
    ('SAFE_AUTO',       'Safe Auto',       ''),
    ('SAFE_MANUAL',     'Safe Manual',     ''),
    ('REVIEW_REQUIRED', 'Review Required', ''),
])
detail_count: IntProperty()
```

`scene_props.py` — `SMPSceneProperties(PropertyGroup)`:
```python
mlo_name:                StringProperty(name="MLO Name", default="MyMLO")
last_check_time:         FloatProperty(default=0.0)
checked_object_count:    IntProperty(default=0)
check_results:           CollectionProperty(type=SMPCheckResult)
check_status:            EnumProperty(
    items=[('NONE','Not Run',''), ('PASS','Pass',''), ('WARN','Warning',''), ('FAIL','Fail','')],
    default='NONE'
)
remove_doubles_threshold: FloatProperty(
    name="Merge Distance",
    default=0.0001, min=0.00001, max=0.1, precision=5, step=1
)
```

`object_props.py` — `SMPObjectProperties(PropertyGroup)`:
```python
is_collision_base_copy: BoolProperty(default=False)
source_object_name:     StringProperty()
preflight_passed:       BoolProperty(default=False)
preflight_timestamp:    FloatProperty(default=0.0)
```

`properties/__init__.py` — **登録順序を厳守**:
```python
def register():
    bpy.utils.register_class(SMPCheckResult)       # 1. 要素型を先に
    bpy.utils.register_class(SMPSceneProperties)   # 2. CollectionProperty が SMPCheckResult を参照するため
    bpy.utils.register_class(SMPObjectProperties)  # 3.
    bpy.types.Scene.smp  = PointerProperty(type=SMPSceneProperties)
    bpy.types.Object.smp = PointerProperty(type=SMPObjectProperties)

def unregister():                                  # 登録と逆順
    del bpy.types.Object.smp
    del bpy.types.Scene.smp
    bpy.utils.unregister_class(SMPObjectProperties)
    bpy.utils.unregister_class(SMPSceneProperties)
    bpy.utils.unregister_class(SMPCheckResult)
```

**完了条件:**
- `bpy.context.scene.smp.mlo_name` → `"MyMLO"` が返る
- `bpy.context.object.smp.is_collision_base_copy` → `False` が返る
- `bpy.context.scene.smp.check_results` が空の CollectionProperty として存在する
- `unregister()` → `register()` を繰り返しても例外が出ない

**テスト方法:**
```python
scene = bpy.context.scene
assert scene.smp.mlo_name == "MyMLO"
assert scene.smp.check_status == 'NONE'
assert len(scene.smp.check_results) == 0
obj = bpy.context.object
if obj:
    assert obj.smp.is_collision_base_copy == False
```

---

## T-003: MLO Collection 作成 Operator

**目的:** ユーザー指定の名前で MLO 用 Collection 階層を 1 クリックで作成する。

**前提タスク:** T-002

**対象ファイル:**
- `sollumz_model_prepper/operators/collection_ops.py`
- `sollumz_model_prepper/utils/collection_utils.py`

**実装内容:**

`collection_utils.py`:
```python
def collection_exists(name: str) -> bool:
    return name in bpy.data.collections

def get_or_create_collection(name: str, parent=None):
    """
    name の Collection を取得または作成し、parent にリンクして返す。
    parent が None の場合は Scene の Master Collection にリンクする。
    """
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    parent_col = parent if parent else bpy.context.scene.collection
    parent_col.children.link(col)
    return col
```

`SMP_OT_CreateMLOCollection`:
- `bl_idname = "smp.create_mlo_collection"`
- `bl_options = {'REGISTER', 'UNDO'}`
- `execute()`:
  1. `scene.smp.mlo_name` を取得してトリミング（空白除去）
  2. 空文字の場合は `{'ERROR'}` で return
  3. 親 `MLO_{name}` を `get_or_create_collection` で作成
  4. 子 3 つ (`_entities`, `_collision`, `_portals`) を同様に作成
  5. 既存の場合は `{'INFO'}` で "Collection already exists, skipped." を報告（破壊しない）
  6. 新規作成の場合は `{'INFO'}` で作成した名前を報告
- `poll()`: `context.scene is not None`

**完了条件:**
- ボタン実行後に Outliner に 4 Collection が出現する
- 同名で再実行しても既存 Collection が壊れない
- Ctrl+Z で作成した Collection が消える（`bl_options = {'REGISTER', 'UNDO'}` による）
- `mlo_name` が空白の場合にエラーが表示される

**テスト方法:**
```python
bpy.context.scene.smp.mlo_name = "TestBuilding"
bpy.ops.smp.create_mlo_collection()
assert "MLO_TestBuilding" in bpy.data.collections
assert "MLO_TestBuilding_entities" in bpy.data.collections
assert "MLO_TestBuilding_collision" in bpy.data.collections
assert "MLO_TestBuilding_portals" in bpy.data.collections

# 再実行しても壊れないこと
bpy.ops.smp.create_mlo_collection()
assert len([c for c in bpy.data.collections if "MLO_TestBuilding" in c.name]) == 4
```

---

## T-004: Preflight Check 基盤と context_utils

**目的:** 各チェック関数を統一インターフェースで呼び出す基盤を作る。また bmesh 操作の安全なコンテキスト管理ユーティリティを実装する。

**前提タスク:** T-002

**対象ファイル:**
- `sollumz_model_prepper/checks/result.py`
- `sollumz_model_prepper/checks/__init__.py`
- `sollumz_model_prepper/operators/check_ops.py`
- `sollumz_model_prepper/utils/context_utils.py`

**実装内容:**

`checks/result.py`:
```python
from dataclasses import dataclass, field
from typing import Literal

FixType = Literal['NONE', 'SAFE_AUTO', 'SAFE_MANUAL', 'REVIEW_REQUIRED']
Status  = Literal['OK', 'WARN', 'ERROR']

@dataclass
class CheckResult:
    check_id:     str
    check_name:   str
    status:       Status
    message:      str
    fix_type:     FixType = 'NONE'
    detail_count: int = 0
```

`utils/context_utils.py` — `mesh_edit_context(obj)` コンテキストマネージャ:
- 現在の `view_layer.objects.active` と `obj.mode` を保存
- `try` ブロック内で `mode_set('EDIT')` して yield
- `finally` で必ず `mode_set('OBJECT')` → active 復元 → 元モード復元
- `ReferenceError` を catch して削除済みオブジェクトへのアクセスをガード

`checks/__init__.py`:
```python
from .transform_check import check_transform
from .normal_check    import check_normals
from .geometry_check  import check_geometry
from .uv_check        import check_uv
# from .material_check import check_materials  # Post-MVP

CHECK_FUNCTIONS = [check_transform, check_normals, check_geometry, check_uv]

def run_all_checks(obj) -> list:
    results = []
    for fn in CHECK_FUNCTIONS:
        results.extend(fn(obj))
    return results
```

`SMP_OT_RunPreflight`:
- `bl_idname = "smp.run_preflight"`
- `bl_options = {'REGISTER'}`（チェックのみで Undo 対象外）
- `poll()`: `context.active_object is not None and context.active_object.type == 'MESH' and context.mode == 'OBJECT'`
- `execute()`:
  1. `scene.smp.check_results.clear()`（古い結果を必ず消す）
  2. 選択中の MESH オブジェクトを収集（non-MESH は skip）
  3. 各オブジェクトに `run_all_checks(obj)` を実行
  4. 結果を `check_results` に格納
  5. `checked_object_count` と `last_check_time`（`time.time()`）を更新
  6. `check_status` を集計（ERROR があれば FAIL、WARN だけなら WARN、全 OK なら PASS）

**完了条件:**
- Cube を選択して `bpy.ops.smp.run_preflight()` を実行すると `check_results` に結果が入る
- MESH 以外を選択していると skip される
- 選択なしで実行すると `{'WARNING'}` が出る
- `check_results.clear()` が実行前に必ず呼ばれること（古い結果が残らない）

**テスト方法:**
```python
import time
bpy.ops.mesh.primitive_cube_add()
t0 = time.time()
bpy.ops.smp.run_preflight()
scene = bpy.context.scene
assert len(scene.smp.check_results) > 0
assert scene.smp.last_check_time >= t0
assert scene.smp.checked_object_count == 1
assert scene.smp.check_status in ('PASS', 'WARN', 'FAIL')
```

---

## T-005: Transform チェック

**目的:** Scale / Rotation / Location が未適用かどうかを検査する。

**前提タスク:** T-004

**対象ファイル:**
- `sollumz_model_prepper/checks/transform_check.py`

**実装内容:**

```python
import bpy
from mathutils import Vector, Euler
from .result import CheckResult

SCALE_TOL    = 1e-4
ROT_TOL      = 1e-4

def check_transform(obj) -> list[CheckResult]:
    results = []

    # Scale チェック
    scale_diff = (Vector(obj.scale) - Vector((1.0, 1.0, 1.0))).length
    if scale_diff > SCALE_TOL:
        results.append(CheckResult(
            check_id='transform_scale',
            check_name='Scale Not Applied',
            status='ERROR',
            message=f"Scale {tuple(round(v,4) for v in obj.scale)} is not (1,1,1). "
                    "Apply scale before export.",
            fix_type='SAFE_MANUAL',
        ))
    else:
        results.append(CheckResult('transform_scale', 'Scale', 'OK', 'Scale is applied.'))

    # Rotation チェック（Euler のみ。Quaternion モードは WARN で通知）
    if obj.rotation_mode == 'QUATERNION':
        results.append(CheckResult(
            'transform_rotation', 'Rotation Mode',
            'WARN',
            'Object uses Quaternion rotation mode. Cannot check rotation as Euler.',
            fix_type='REVIEW_REQUIRED',
        ))
    else:
        rot = obj.rotation_euler
        rot_diff = Euler(rot).to_quaternion().rotation_difference(
            Euler((0,0,0)).to_quaternion()
        ).angle
        if rot_diff > ROT_TOL:
            results.append(CheckResult(
                'transform_rotation', 'Rotation Not Applied',
                'WARN',
                f"Rotation {tuple(round(v,4) for v in rot)} is not (0,0,0). "
                "May affect export alignment.",
                fix_type='REVIEW_REQUIRED',
            ))
        else:
            results.append(CheckResult('transform_rotation', 'Rotation', 'OK', 'Rotation is applied.'))

    # Location チェック（INFO のみ）
    loc_len = Vector(obj.location).length
    if loc_len > SCALE_TOL:
        results.append(CheckResult(
            'transform_location', 'Non-zero Origin',
            'INFO',
            f"Object origin is at {tuple(round(v,4) for v in obj.location)}. "
            "Confirm this is intentional.",
            fix_type='REVIEW_REQUIRED',
        ))
    else:
        results.append(CheckResult('transform_location', 'Location', 'OK', 'Origin is at world zero.'))

    return results
```

**完了条件:**
- `obj.scale = (2,2,2)` のオブジェクトで `transform_scale` が ERROR になる
- `obj.scale = (1,1,1)` のオブジェクトで `transform_scale` が OK になる
- `rotation_mode == 'QUATERNION'` のオブジェクトで Quaternion の WARN が出る
- Location が (5, 0, 0) で INFO が出る

**テスト方法:**
```python
from sollumz_model_prepper.checks.transform_check import check_transform
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.object
obj.scale = (2, 2, 2)
r = check_transform(obj)
assert any(x.check_id == 'transform_scale' and x.status == 'ERROR' for x in r)
obj.scale = (1, 1, 1)
r = check_transform(obj)
assert any(x.check_id == 'transform_scale' and x.status == 'OK' for x in r)
```

---

## T-006: Normal チェック

**目的:** メッシュに内向き疑いの面がどれだけあるかを bmesh で検査する。

**前提タスク:** T-004

**対象ファイル:**
- `sollumz_model_prepper/checks/normal_check.py`

**実装内容:**

```python
import bmesh
from .result import CheckResult

def check_normals(obj) -> list[CheckResult]:
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.normal_update()

        if len(bm.faces) == 0:
            return [CheckResult('normal_flip', 'Normals', 'OK', 'No faces to check.')]

        # メッシュ重心（全面重心の平均）
        mesh_center = sum(
            (f.calc_center_median() for f in bm.faces),
            bm.faces[0].calc_center_median()
        ) / len(bm.faces)

        flipped = 0
        for face in bm.faces:
            to_face = face.calc_center_median() - mesh_center
            if to_face.length < 1e-8:
                continue
            dot = face.normal.dot(to_face.normalized())
            if dot < 0:
                flipped += 1

    finally:
        bm.free()

    if flipped == 0:
        return [CheckResult('normal_flip', 'Normals', 'OK', 'No obviously flipped faces.')]

    return [CheckResult(
        check_id='normal_flip',
        check_name='Possibly Flipped Normals',
        status='WARN',
        message=f"{flipped} face(s) may have inward normals. "
                "Note: interior walls may be intentional.",
        fix_type='SAFE_MANUAL',
        detail_count=flipped,
    )]
```

**注意事項（実装コメントとして残す）:**
- 重心ベースの判定は近似であり、内部構造を持つ建築物では誤検出がある
- このため ERROR ではなく WARN 止まりにすること
- ユーザーへの注意書き（"interior walls may be intentional"）を message に含める

**完了条件:**
- 外向き統一 Cube で `normal_flip` が OK
- `bpy.ops.mesh.flip_normals()` で反転した Cube で WARN になる
- `detail_count` が反転面数と一致する

---

## T-007: Geometry チェック（重複頂点 / 非多様体 / ゼロ面積 / Loose）

**目的:** メッシュの幾何学的問題を bmesh で検査する。

**前提タスク:** T-004

**対象ファイル:**
- `sollumz_model_prepper/checks/geometry_check.py`

**実装内容:**

```python
import bmesh
from .result import CheckResult

ZERO_AREA_THRESHOLD = 1e-8

def check_geometry(obj) -> list[CheckResult]:
    results = []
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # 重複頂点チェック（bmesh.ops.find_doubles は読み取り専用で安全）
        ret = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.0001)
        dupe_count = len(ret['targetmap'])
        if dupe_count > 0:
            results.append(CheckResult(
                'dupe_vertex', 'Duplicate Vertices', 'WARN',
                f"{dupe_count} duplicate vertex pair(s) found (dist < 0.0001).",
                fix_type='SAFE_MANUAL', detail_count=dupe_count,
            ))
        else:
            results.append(CheckResult('dupe_vertex', 'Duplicate Vertices', 'OK',
                                       'No duplicate vertices found.'))

        # 非多様体チェック
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
        nm_count = len(non_manifold_edges) + len(non_manifold_verts)
        if nm_count > 0:
            results.append(CheckResult(
                'non_manifold', 'Non-Manifold Geometry', 'ERROR',
                f"{len(non_manifold_edges)} non-manifold edge(s), "
                f"{len(non_manifold_verts)} non-manifold vert(s). Manual fix required.",
                fix_type='REVIEW_REQUIRED', detail_count=nm_count,
            ))
        else:
            results.append(CheckResult('non_manifold', 'Manifold', 'OK',
                                       'Mesh is manifold.'))

        # ゼロ面積チェック
        zero_faces = [f for f in bm.faces if f.calc_area() < ZERO_AREA_THRESHOLD]
        if zero_faces:
            results.append(CheckResult(
                'zero_area_face', 'Zero Area Faces', 'WARN',
                f"{len(zero_faces)} zero-area face(s) found.",
                fix_type='SAFE_MANUAL', detail_count=len(zero_faces),
            ))
        else:
            results.append(CheckResult('zero_area_face', 'Face Areas', 'OK',
                                       'No zero-area faces.'))

        # Loose Geometry チェック
        loose_verts  = [v for v in bm.verts if not v.link_edges]
        loose_edges  = [e for e in bm.edges if not e.link_faces]
        loose_count  = len(loose_verts) + len(loose_edges)
        if loose_count > 0:
            results.append(CheckResult(
                'loose_geo', 'Loose Geometry', 'WARN',
                f"{len(loose_verts)} loose vert(s), {len(loose_edges)} loose edge(s).",
                fix_type='REVIEW_REQUIRED', detail_count=loose_count,
            ))
        else:
            results.append(CheckResult('loose_geo', 'Loose Geometry', 'OK',
                                       'No loose geometry.'))

    finally:
        bm.free()

    return results
```

**完了条件:**
- 通常の Cube で `non_manifold` と `dupe_vertex` が OK
- `bmesh.ops.find_doubles` の返り値 `targetmap` の長さが重複頂点ペア数と一致する
- 手動で作った非多様体メッシュ（穴あき面など）で `non_manifold` が ERROR になる

---

## T-008: UV チェック

**目的:** UV マップの有無と UV 頂点の範囲外を検査する。

**前提タスク:** T-004

**対象ファイル:**
- `sollumz_model_prepper/checks/uv_check.py`

**実装内容:**

```python
import bmesh
from .result import CheckResult

def check_uv(obj) -> list[CheckResult]:
    results = []
    mesh = obj.data

    # UV マップ存在チェック（SAFE_AUTO: 空 UV レイヤー追加のみで安全）
    if len(mesh.uv_layers) == 0:
        results.append(CheckResult(
            'uv_missing', 'No UV Map', 'ERROR',
            'No UV map found. An empty UV map will be added by Fix Safe Issues.',
            fix_type='SAFE_AUTO',
        ))
        return results  # UV がなければ範囲チェック不要

    results.append(CheckResult('uv_missing', 'UV Map', 'OK',
                               f"{len(mesh.uv_layers)} UV layer(s) found."))

    # UV 範囲外チェック（bmesh で UV レイヤーを読む）
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            return results

        out_count = 0
        for face in bm.faces:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
                    out_count += 1
    finally:
        bm.free()

    if out_count > 0:
        results.append(CheckResult(
            'uv_out_of_bounds', 'UV Out of Bounds', 'WARN',
            f"{out_count} UV point(s) are outside [0,1] range. "
            "May be intentional tiling — review manually.",
            fix_type='REVIEW_REQUIRED',
            detail_count=out_count,
        ))
    else:
        results.append(CheckResult('uv_out_of_bounds', 'UV Bounds', 'OK',
                                   'All UVs are within [0,1] range.'))

    return results
```

**完了条件:**
- UV なしメッシュで `uv_missing` が ERROR / fix_type が SAFE_AUTO
- UV が (1.5, 0.5) を持つメッシュで `uv_out_of_bounds` が WARN / fix_type が REVIEW_REQUIRED
- 正常 UV のメッシュで両方 OK

---

## T-009: MVP 最小 UI パネル

**目的:** N パネルに SMP タブを作成し、MVP の全機能（Collection 作成・Preflight Check）を操作できる最小限の UI を実装する。Fix ボタン群・Collision パネルは Post-MVP。

**前提タスク:** T-002, T-003, T-004

**対象ファイル:**
- `sollumz_model_prepper/ui/panel_main.py`
- `sollumz_model_prepper/ui/panel_collection.py`
- `sollumz_model_prepper/ui/panel_preflight.py`
- `sollumz_model_prepper/ui/__init__.py`

**実装内容:**

`SMP_PT_MainPanel(Panel)`:
```python
bl_space_type  = 'VIEW_3D'
bl_region_type = 'UI'
bl_category    = 'SMP'
bl_label       = 'Sollumz Model Prepper'
```

`SMP_PT_CollectionPanel(Panel)` (parent = SMP_PT_MainPanel):
```
layout.prop(scene.smp, "mlo_name")
layout.operator("smp.create_mlo_collection", icon='COLLECTION_NEW')
```

`SMP_PT_PreflightPanel(Panel)` (parent = SMP_PT_MainPanel):
```
# ヘッダー行
layout.operator("smp.run_preflight", icon='VIEWZOOM')

# 実行済みの場合のみ結果を表示
if scene.smp.check_status == 'NONE' or scene.smp.last_check_time == 0.0:
    layout.label(text="Run Preflight Check to see results.", icon='INFO')
else:
    # チェック状態バッジ
    status_icon = {'PASS': 'CHECKMARK', 'WARN': 'ERROR', 'FAIL': 'CANCEL'}[scene.smp.check_status]
    layout.label(text=f"Status: {scene.smp.check_status}", icon=status_icon)
    layout.label(text=f"Checked: {scene.smp.checked_object_count} object(s)")

    # 結果リスト（template_list は使わず for ループで描画）
    for result in scene.smp.check_results:
        row = layout.row()
        icon = {'OK': 'CHECKMARK', 'WARN': 'ERROR', 'ERROR': 'CANCEL'}[result.status]
        row.label(text=f"{result.check_name}: {result.message[:60]}", icon=icon)
        # Fix ボタンは Post-MVP で追加
    
    # remove_doubles_threshold の UI（SAFE_MANUAL Fix 追加時に使う）
    # layout.prop(scene.smp, "remove_doubles_threshold")  # Post-MVP
```

**`remove_doubles_threshold` の警告ラベル（Post-MVP の Fix UI 追加時に実装）:**
```python
if scene.smp.remove_doubles_threshold > 0.01:
    layout.label(text="⚠ Large threshold may destroy geometry.", icon='ERROR')
```

**完了条件:**
- 3D Viewport の N パネルに "SMP" タブが表示される
- Collection Setup パネルから `smp.create_mlo_collection` が実行できる
- Preflight Check パネルから `smp.run_preflight` が実行できる
- チェック結果がアイコン付きで一覧表示される
- 未実行時は "Run Preflight Check to see results." が表示される

---

## Post-MVP タスク群

---

## T-010: Material / Texture チェック（Post-MVP）

**目的:** マテリアルスロットの有無と Image Texture ノードへの画像割当を検査する。

**前提タスク:** T-004

**対象ファイル:**
- `sollumz_model_prepper/checks/material_check.py`

**実装内容:**

```python
def check_materials(obj) -> list[CheckResult]:
    # mat_missing: len(obj.material_slots) == 0 → ERROR, REVIEW_REQUIRED
    # mat_empty_slot: slot.material is None → WARN, REVIEW_REQUIRED
    # tex_missing: node.type == 'TEX_IMAGE' and node.image is None → WARN, REVIEW_REQUIRED
    # Use Nodes が False のマテリアルは INFO として記録（WARN にしない）
```

`checks/__init__.py` の `CHECK_FUNCTIONS` に `check_materials` を追加。

**完了条件:**
- マテリアルなしメッシュで `mat_missing` が ERROR
- Image Texture ノードに画像なしで `tex_missing` が WARN
- Use Nodes が False のマテリアルで INFO が出る（WARN にならない）

---

## T-011: Fix Safe Issues Operator（Post-MVP）

**目的:** `fix_type == SAFE_AUTO` のチェック結果をまとめて自動修正する。MVP では `uv_missing` への対応のみ。

**前提タスク:** T-008（UV チェック）

**対象ファイル:**
- `sollumz_model_prepper/operators/fix_ops.py`

**実装内容:**

```python
class SMP_OT_FixSafeIssues(Operator):
    bl_idname  = "smp.fix_safe_issues"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        targets = [r for r in scene.smp.check_results
                   if r.fix_type == 'SAFE_AUTO' and r.status != 'OK']

        if not targets:
            self.report({'INFO'}, "Nothing to fix.")
            return {'CANCELLED'}

        obj = context.active_object
        fixed = []

        for result in targets:
            if result.check_id == 'uv_missing':
                obj.data.uv_layers.new(name="UVMap")
                fixed.append(result.check_id)

        # 修正後に Preflight を再実行して結果を更新
        bpy.ops.smp.run_preflight()
        self.report({'INFO'}, f"Fixed: {', '.join(fixed)}")
        return {'FINISHED'}
```

`poll()`: 選択中の MESH があり、SAFE_AUTO の未解決項目があること。

**完了条件:**
- UV なしメッシュに対して実行すると UV レイヤーが追加される
- 実行後に check_results が更新される
- Ctrl+Z で UV レイヤーが消える

---

## T-012: Apply Scale Operator（Post-MVP）

**目的:** Scale 未適用のオブジェクトに Scale を適用する個別 Operator（確認ダイアログ付き）。

**前提タスク:** T-011

**対象ファイル:**
- `sollumz_model_prepper/operators/fix_ops.py`（追記）

**実装内容:**

```python
class SMP_OT_ApplyScale(Operator):
    bl_idname  = "smp.apply_scale"
    bl_label   = "Apply Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self, event,
            message="Apply scale to selected objects?\n"
                    "This may affect child objects and shape keys."
        )

    def execute(self, context):
        bpy.ops.object.transform_apply(scale=True, rotation=False, location=False)
        bpy.ops.smp.run_preflight()
        return {'FINISHED'}
```

**完了条件:**
- 確認ダイアログが表示される
- OK 後に Scale が (1,1,1) になる
- Cancel では何も変わらない

---

## T-013: Recalc Normals Operator（Post-MVP）

**目的:** 法線を外向きに再計算する個別 Operator（確認ダイアログ付き）。

**前提タスク:** T-011

**対象ファイル:**
- `sollumz_model_prepper/operators/fix_ops.py`（追記）
- `sollumz_model_prepper/utils/context_utils.py`（mesh_edit_context 使用）

**実装内容:**

```python
class SMP_OT_RecalcNormals(Operator):
    bl_idname  = "smp.recalc_normals"
    bl_label   = "Recalculate Normals"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self, event,
            message="Recalculate normals to outside?\n"
                    "Interior walls may be affected. Review result manually."
        )

    def execute(self, context):
        obj = context.active_object
        with mesh_edit_context(obj):
            bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.smp.run_preflight()
        return {'FINISHED'}
```

**完了条件:**
- 確認ダイアログが表示される
- 実行後に Preflight の normal_flip が改善される（OK または WARN が減る）
- Ctrl+Z で法線が元に戻る

---

## T-014: Merge Doubles Operator（Post-MVP）

**目的:** 重複頂点をマージする個別 Operator（閾値表示・確認ダイアログ付き）。

**前提タスク:** T-011

**対象ファイル:**
- `sollumz_model_prepper/operators/fix_ops.py`（追記）

**実装内容:**

```python
class SMP_OT_MergeDoubles(Operator):
    bl_idname  = "smp.merge_doubles"
    bl_label   = "Merge Duplicate Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        threshold = context.scene.smp.remove_doubles_threshold
        msg = f"Merge duplicate vertices (threshold: {threshold:.5f})?\n"
        if threshold > 0.01:
            msg += "WARNING: Large threshold may merge unintended vertices!"
        return context.window_manager.invoke_confirm(self, event, message=msg)

    def execute(self, context):
        obj = context.active_object
        threshold = context.scene.smp.remove_doubles_threshold
        with mesh_edit_context(obj):
            bpy.ops.mesh.remove_doubles(threshold=threshold)
        bpy.ops.smp.run_preflight()
        return {'FINISHED'}
```

`0.01` 超の場合のみ確認メッセージに追加警告を含める。

**完了条件:**
- デフォルト閾値 (0.0001) で重複頂点がマージされる
- 閾値 > 0.01 で警告付きダイアログが出る
- Ctrl+Z で元に戻る

---

## T-015: Dissolve Degenerate Operator（Post-MVP）

**目的:** ゼロ面積面を削除する個別 Operator。

**前提タスク:** T-011

**対象ファイル:**
- `sollumz_model_prepper/operators/fix_ops.py`（追記）

**実装内容:** T-013 と同様のパターンで `bpy.ops.mesh.dissolve_degenerate()` を `mesh_edit_context` 内で呼ぶ。

**完了条件:** ゼロ面積面が削除され、`zero_area_face` が OK になる。

---

## T-016: Collision Base Copy 生成 Operator（Post-MVP）

**目的:** 選択メッシュから Collision 用の下地複製を生成し、専用 Collection に配置する。

**前提タスク:** T-003

**対象ファイル:**
- `sollumz_model_prepper/operators/collision_ops.py`
- `sollumz_model_prepper/utils/collection_utils.py`（move_to_collection 追加）

**実装内容:**

`SMP_OT_CreateCollisionBaseCopy`:
- `bl_idname = "smp.create_collision_base_copy"`
- `bl_options = {'REGISTER', 'UNDO'}`
- 前提チェック:
  - 選択オブジェクトが MESH
  - `[MLO_{mlo_name}_collision]` Collection が存在する
  - 対象が既に `is_collision_base_copy == True` でない
- Full Copy のみ（`bpy.ops.object.duplicate(linked=False)`）
- 複製名: `{original.name}_col`
- `smp.is_collision_base_copy = True`・`smp.source_object_name` を設定
- `move_to_collection(col_obj, collision_collection)` で移動

`collection_utils.py` に追加:
```python
def move_to_collection(obj, target_collection):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    target_collection.objects.link(obj)
```

**完了条件:**
- `{name}_col` が `MLO_*_collision` Collection に入っている
- 元オブジェクトは変更されていない
- `smp.is_collision_base_copy` が True
- Ctrl+Z で複製が消える

---

## T-017: フル UI パネル（Post-MVP）

**目的:** T-009 の MVP UI に Fix ボタン群と Collision パネルを追加する。

**前提タスク:** T-009, T-011, T-016

**対象ファイル:**
- `sollumz_model_prepper/ui/panel_preflight.py`（Fix ボタン追記）
- `sollumz_model_prepper/ui/panel_collision.py`（新規）

**実装内容:**

`panel_preflight.py` の追記:
```
# 結果リストに個別 Fix ボタンを追加
for result in scene.smp.check_results:
    row = layout.row()
    ...
    if result.fix_type == 'SAFE_MANUAL' and result.status != 'OK':
        fix_op_map = {
            'transform_scale': 'smp.apply_scale',
            'normal_flip':     'smp.recalc_normals',
            'dupe_vertex':     'smp.merge_doubles',
            'zero_area_face':  'smp.dissolve_degenerate',
        }
        op_id = fix_op_map.get(result.check_id)
        if op_id:
            row.operator(op_id, text="Fix", icon='TOOL_SETTINGS')

# SAFE_AUTO がある場合のみ Fix Safe Issues ボタンを有効化
has_auto = any(r.fix_type == 'SAFE_AUTO' and r.status != 'OK'
               for r in scene.smp.check_results)
col = layout.column()
col.enabled = has_auto
col.operator("smp.fix_safe_issues", icon='CHECKMARK')

# remove_doubles_threshold と警告ラベル
layout.prop(scene.smp, "remove_doubles_threshold")
if scene.smp.remove_doubles_threshold > 0.01:
    layout.label(text="Large threshold may destroy geometry.", icon='ERROR')
```

`panel_collision.py`:
```
layout.operator("smp.create_collision_base_copy", icon='MESH_ICOSPHERE')
# collision_link_mode は廃止（Full Copy のみ）
```

---

## T-018: 結合テスト・最終確認（Post-MVP）

**目的:** MVP + Post-MVP の全機能が連携して正しく動作することを確認する。

**前提タスク:** T-001 〜 T-017 すべて

**テストシナリオ:**

```
シナリオ 1: 正常フロー
1. 新規シーンで Cube を追加（UV なし）
2. MLO Name = "TestHouse"
3. [Create MLO Collection] 実行
4. Cube を選択して [Run Preflight Check] 実行
5. check_results に uv_missing (ERROR, SAFE_AUTO) が含まれること
6. [Fix Safe Issues] 実行 → UV レイヤーが追加される
7. 再チェックで uv_missing が OK になること

シナリオ 2: SAFE_MANUAL フロー
1. Cube の Scale を (2,2,2) に設定
2. [Run Preflight Check] → transform_scale が ERROR
3. [Apply Scale] ボタン → 確認ダイアログ表示 → OK
4. 再チェックで transform_scale が OK になること

シナリオ 3: Collision Base Copy
1. Cube を選択
2. MLO Collection が存在すること
3. [Create Collision Base Copy] → Cube_col が collision Collection に入っていること
4. Ctrl+Z → 複製が消えること

シナリオ 4: Undo 一貫性
各 Fix Operator の後に Ctrl+Z → 修正前の状態に戻ること

シナリオ 5: エッジケース
- 選択なし → [Run Preflight] で WARNING
- Camera 選択 → スキップ（non-MESH）
- MLO Collection なし → [Create Collision Base Copy] で WARNING
- 同名 MLO の [Create MLO Collection] 再実行 → 既存が破壊されない
- mlo_name が空白 → エラーが表示される
```
