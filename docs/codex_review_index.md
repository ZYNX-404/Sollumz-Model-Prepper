# Codex Review Index — Sollumz Model Prepper

> Use Search Tokens to jump to the relevant section in each file.
> Updated: 2026-06-29

---

## [CRI-01] SAFE_AUTO_SCOPE

**Files:** `design.md §7`, `design.md §6 (table)`, `review.md §1.1`, `tasks.md T-011`

**Search Tokens:** `SAFE_AUTO`, `uv_missing`, `fix_safe_issues`, `uv_layers.new`

**Expected:**
- `SAFE_AUTO` contains only `uv_missing`
- `normal_flip`, `dupe_vertex`, `zero_area_face` are `SAFE_MANUAL`, not `SAFE_AUTO`
- `SMP_OT_FixSafeIssues.execute()` calls only `uv_layers.new()` — no topology change

---

## [CRI-02] FIX_TYPE_CLASSIFICATION

**Files:** `design.md §6 (table)`, `design.md §6 (3-tier definition)`, `review.md §1.2 (table)`

**Search Tokens:** `fix_type`, `SAFE_MANUAL`, `REVIEW_REQUIRED`, `transform_scale`, `transform_rotation`

**Expected:**
- `SAFE_AUTO` — data addition only, zero change to existing data
- `SAFE_MANUAL` — individual operator with confirm dialog, Fix button shown in UI
- `REVIEW_REQUIRED` — no Fix button, warning label only
- `transform_scale` → `SAFE_MANUAL`
- `transform_rotation`, `uv_out_of_bounds`, `non_manifold`, all material checks → `REVIEW_REQUIRED`

---

## [CRI-03] BMESH_READONLY_PREFLIGHT

**Files:** `design.md §8`, `tasks.md T-006`, `tasks.md T-007`, `tasks.md T-008`, `review.md §2.1 (table)`

**Search Tokens:** `bmesh.new`, `bm.from_mesh`, `bm.free`, `find_doubles`, `bpy.ops.mesh`

**Expected:**
- All check functions (read-only) use `bmesh` only — zero `bpy.ops.mesh.*` calls
- Pattern: `bm = bmesh.new()` → `bm.from_mesh(obj.data)` → read → `bm.free()`
- `bmesh.ops.find_doubles` is read-only use — `remove_doubles` is Fix path only
- `bm.free()` always called in `finally` block

---

## [CRI-04] BPY_OPS_CONTEXT_RESTORE

**Files:** `design.md §8 (mesh_edit_context code)`, `tasks.md T-004 (context_utils.py)`, `tasks.md T-013`, `review.md §2.1`

**Search Tokens:** `mesh_edit_context`, `prev_active`, `prev_mode`, `prev_selected`, `ReferenceError`, `mode_set`

**Expected:**
- All Fix operators that call `bpy.ops.mesh.*` use `mesh_edit_context(obj)` — no direct `mode_set` outside it
- `mesh_edit_context` saves `prev_active`, `prev_mode`, `prev_selected` and restores all in `finally`
- `ReferenceError` is caught when restoring selection state
- `context_utils.py` is created in `utils/` at T-004

---

## [CRI-05] PROPERTYGROUP_REGISTRATION_ORDER

**Files:** `design.md §4.1 (code snippet)`, `tasks.md T-002 (properties/__init__.py)`, `review.md §2.2`

**Search Tokens:** `register_class`, `SMPCheckResult`, `SMPSceneProperties`, `SMPObjectProperties`, `PointerProperty`, `unregister_class`

**Expected:**
- `register()` order: `SMPCheckResult` → `SMPSceneProperties` → `SMPObjectProperties` → `PointerProperty`
- `unregister()` order: `del PointerProperty` → `SMPObjectProperties` → `SMPSceneProperties` → `SMPCheckResult`
- Registering `SMPSceneProperties` before `SMPCheckResult` is a bug

---

## [CRI-06] PREFLIGHT_RESULT_CLEAR_RESET

**Files:** `design.md §9`, `tasks.md T-004 (execute() step 2 and step 6)`

**Search Tokens:** `check_results.clear`, `check_status`, `last_check_time`, `NONE`, `run_preflight`

**Expected:**
- `check_results.clear()` is called at the top of `execute()`, before any check runs
- UI does not render result list when `check_status == 'NONE'` or `last_check_time == 0.0`
- No auto-reset of `check_status` on `.blend` load
- Each Fix operator calls `bpy.ops.smp.run_preflight()` at the end to refresh results

---

## [CRI-07] MVP_SCOPE_T001_T009

**Files:** `tasks.md (dependency graph)`, `tasks.md T-001` to `tasks.md T-009`, `tasks.md Post-MVP header`, `review.md §4`

**Search Tokens:** `Post-MVP`, `T-010`, `T-011`, `T-016`, `CHECK_FUNCTIONS`, `check_materials`

**Expected:**
- MVP = T-001 through T-009 only
- T-009 UI panel has no Fix buttons (placeholder comment is acceptable)
- `check_materials` is not in `CHECK_FUNCTIONS` at MVP (commented out)
- T-010 Material check, T-011–T-015 Fix operators, T-016 Collision, T-017 full UI are all Post-MVP

---

## [CRI-08] COLLISION_BASE_COPY_WORDING

**Files:** `design.md §10 (terminology table)`, `tasks.md T-016`, `properties/object_props.py`

**Search Tokens:** `create_collision_base_copy`, `SMP_OT_CreateCollisionBaseCopy`, `is_collision_base_copy`, `generate_collision`, `is_collision_base`

**Expected:**
- Operator ID: `smp.create_collision_base_copy` — `generate_collision_base` must not exist
- Class name: `SMP_OT_CreateCollisionBaseCopy`
- Property name: `is_collision_base_copy` — `is_collision_base` must not exist
- No Linked Duplicate mode — Full Copy (`linked=False`) only
- Strings "Collision生成", "Generate Collision" must not appear in code, comments, or UI labels

---

## [CRI-09] REMOVE_DOUBLES_THRESHOLD_SAFETY

**Files:** `design.md §4.3 (SMPSceneProperties)`, `tasks.md T-014 (invoke())`, `tasks.md T-017 (UI warning label)`, `review.md §2.6 (table)`

**Search Tokens:** `remove_doubles_threshold`, `0.0001`, `0.01`, `invoke_confirm`, `icon='ERROR'`

**Expected:**
- Default: `0.0001`, `min=0.00001`, `max=0.1`
- UI shows warning label (`icon='ERROR'`) when threshold `> 0.01`
- `invoke()` appends extra warning text to confirm message when threshold `> 0.01`
- Value above `max=0.1` is rejected by the PropertyGroup definition

---

## [CRI-10] MULTI_OBJECT_CHECK_STATE

**Files:** `design.md §4.3 (SMPSceneProperties)`, `tasks.md T-004 (execute() step 5)`, `review.md §1.7`

**Search Tokens:** `last_check_time`, `checked_object_count`, `last_check_object`, `time.time`

**Expected:**
- `last_check_object: StringProperty` does not exist — removed
- `last_check_time: FloatProperty` stores `time.time()` value
- `checked_object_count: IntProperty` stores number of checked mesh objects
- Results from multiple objects are flattened into `check_results`
- When the same `check_id` appears from multiple objects, `message` includes the object name
