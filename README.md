# Sollumz Model Prepper

A Blender add-on that helps prepare and review mesh assets before using [Sollumz](https://github.com/Sollumz/Sollumz) for GTA V / FiveM / MLO workflows.

**Sollumz Model Prepper does not replace Sollumz.**
It is a preflight and review helper: it inspects selected meshes for common export-preparation issues, reports them in the sidebar, and provides selection-only review tools so you can find and inspect problem areas quickly. It does not export assets and it does not automatically fix geometry.

---

## Status

* Early MVP (v0.1.0), under active development
* Preflight checks and review tools only
* Non-destructive: no automatic fix execution of any kind
* Does not replace Sollumz and does not run Sollumz export

---

## Features

### MLO Collection Helper

Creates a standard MLO collection hierarchy from a name you enter:

```text
MLO_<name>
├─ MLO_<name>_entities
├─ MLO_<name>_collision
└─ MLO_<name>_portals
```

Existing collections are never destroyed — if the hierarchy already exists, nothing is changed.

### Preflight Checks

**Run Preflight** checks all selected mesh objects. Results are stored per object and shown in the panel. If no mesh object is selected, the button is disabled.

| Category  | Checks                                                                                              |
| --------- | --------------------------------------------------------------------------------------------------- |
| Transform | Unapplied scale, non-zero Euler rotation, quaternion rotation mode, non-zero location               |
| Normals   | Possibly inward / flipped normals (centroid heuristic)                                              |
| Geometry  | Duplicate vertices, zero-area faces, loose geometry, open boundary edges, complex non-manifold edges, high vertex count |
| UV        | Missing UV map, UVs outside the 0–1 range                                                           |
| Materials | Missing material slots, empty material slots, empty material names, materials without image texture nodes, non-power-of-two texture sizes |

All checks are read-only. They never modify mesh data, normals, UVs, materials, or transforms.

### Result Review UI

* **Summary**: total result count plus Errors / Warnings / OK counts, always computed from all stored results.
* **Show OK Results** toggle: off by default so large assets show only warnings and errors. Turning it on shows OK results too. The summary counts are unaffected by the toggle.
* **Result rows** show the status, a human-readable check name, the fix type, a detail count badge (e.g. `x144`), the source object name, and the check message.
* **Select Object** icon button on each result row selects and activates the object that produced the result, so you can jump straight from a warning to the object and use the Review Tools on it.
  * It does not unhide hidden objects or unlock selection-locked objects — it reports a warning and leaves them untouched.
  * It never modifies mesh data, materials, UVs, normals, or transforms.

### Review Tools

Review Tools operate on the **active mesh object**. They are selection-only: each tool finds the matching elements, selects them, and enters Edit Mode with an appropriate select mode so you can inspect the result. Nothing is fixed, merged, or deleted.

| Tool                              | What it selects                                | Destructive? |
| --------------------------------- | ---------------------------------------------- | ------------ |
| Select Zero Area Faces            | Zero-area faces                                | No           |
| Select Open Boundary Edges        | Open boundary edges (edges with exactly 1 face) | No           |
| Select Complex Non-Manifold Edges | Edges shared by 3 or more faces                | No           |
| Select Loose Geometry             | Loose vertices and loose edges                 | No           |
| Select Duplicate Vertices         | Duplicate vertex candidates (no merging)       | No           |
| Select UV Out-of-Bounds Faces     | Faces with UV coordinates outside the 0–1 range | No           |

---

## Recommended Workflow

1. Install the add-on.
2. Select one or more mesh objects.
3. Click **Run Preflight** in the Sollumz Prepper sidebar tab.
4. Keep **Show OK Results** off for large assets.
5. Inspect the Errors and Warnings in the result list.
6. Click the **Select Object** button on a result row to activate the affected object.
7. Use the **Review Tools** to select and inspect the problem elements on that object.
8. Fix issues manually using normal Blender tools and your Sollumz workflow.
9. Re-run Preflight to confirm.

---

## Preflight Status

| Status | Meaning                                                                   |
| ------ | ------------------------------------------------------------------------- |
| `NONE` | No check has been run yet.                                                |
| `PASS` | No warnings or errors were detected.                                      |
| `WARN` | One or more warnings were detected, but no errors.                        |
| `FAIL` | One or more errors were detected. Manual action is needed before export.  |

## Result Severity

| Severity | Meaning                                               |
| -------- | ----------------------------------------------------- |
| `OK`     | No issue detected.                                    |
| `WARN`   | Something may need review, but it can be intentional. |
| `ERROR`  | A likely export or setup issue was detected.          |

## Fix Types

Each result carries a fix type describing how the issue *could* be addressed. **The current version does not execute any fixes** — fix types are classification only.

| Fix Type          | Meaning                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------- |
| `NONE`            | No fix needed, or informational.                                                             |
| `REVIEW_REQUIRED` | The user should inspect manually. Automatic fixing is not recommended.                       |
| `SAFE_MANUAL`     | The issue can usually be fixed manually, but the add-on does not execute fixes.              |
| `SAFE_AUTO`       | Reserved for narrowly safe future operations. No automatic fix is currently executed.        |

`uv_missing` (adding an empty UV layer) is a future `SAFE_AUTO` candidate, but it is **not** executed in the current version.

---

## Check Details

### Transform Check

| Check                    | Severity | Fix Type          |
| ------------------------ | -------- | ----------------- |
| Scale not applied        | `ERROR`  | `SAFE_MANUAL`     |
| Rotation not applied     | `WARN`   | `REVIEW_REQUIRED` |
| Quaternion rotation mode | `WARN`   | `REVIEW_REQUIRED` |
| Non-zero location        | `WARN`   | `REVIEW_REQUIRED` |

### Normal Check

| Check                    | Severity | Fix Type          |
| ------------------------ | -------- | ----------------- |
| Possibly flipped normals | `WARN`   | `REVIEW_REQUIRED` |

Detection uses a centroid-based heuristic. It does not recalculate normals.

### Geometry Check

| Check                      | Severity | Fix Type          |
| -------------------------- | -------- | ----------------- |
| Duplicate vertices         | `WARN`   | `SAFE_MANUAL`     |
| Open boundary edges        | `WARN`   | `REVIEW_REQUIRED` |
| Complex non-manifold edges | `ERROR`  | `REVIEW_REQUIRED` |
| Zero-area faces            | `WARN`   | `SAFE_MANUAL`     |
| Loose geometry             | `WARN`   | `REVIEW_REQUIRED` |
| High vertex count          | `WARN`   | `REVIEW_REQUIRED` |

The vertex count warning threshold is configurable per scene (**Vertex Count Warning** in the panel, default 65,000). It is a warning threshold, not a hard export guarantee — meshes above it may need to be split or optimized, but the add-on never splits or optimizes meshes automatically.

### UV Check

| Check               | Severity | Fix Type          |
| ------------------- | -------- | ----------------- |
| Missing UV map      | `ERROR`  | `SAFE_AUTO`*      |
| UV outside `[0, 1]` | `WARN`   | `REVIEW_REQUIRED` |

*Classification only — no UV layer is created automatically.

### Material Check

| Check                 | Severity | Fix Type          |
| --------------------- | -------- | ----------------- |
| No material slots           | `ERROR`  | `SAFE_MANUAL`     |
| Empty material slots        | `WARN`   | `SAFE_MANUAL`     |
| Empty material names        | `WARN`   | `SAFE_MANUAL`     |
| Missing image texture       | `WARN`   | `REVIEW_REQUIRED` |
| Non-power-of-two texture    | `WARN`   | `REVIEW_REQUIRED` |

Image texture detection looks for Image Texture nodes with assigned images in node-based materials. Procedural or custom shader setups may be intentional, so missing textures are a warning, not an error. This check does not create or modify materials, textures, or shader nodes.

The power-of-two check inspects the sizes of the unique texture images used by the object's materials (the same image used in multiple materials or nodes is counted once). Images whose size cannot be read (e.g. not loaded) are skipped. The add-on never resizes or replaces textures.

---

## Classification Notes

These judgements are tuned for real GTA V / FiveM / MLO assets, where "textbook-clean" topology is not always the goal:

* **Open boundary edges are `WARN` / `REVIEW_REQUIRED`.** Open boundaries are common in props, interiors, cards, containers, and low-detail meshes. They are not automatically considered fatal.
* **Complex non-manifold edges are `ERROR` / `REVIEW_REQUIRED`.** Edges shared by 3 or more faces are much more likely to indicate genuinely broken topology.
* **Possibly flipped normals are `WARN` / `REVIEW_REQUIRED`.** The centroid-based heuristic can produce false positives on concave, open, or interior meshes — treat the result as a hint, not a verdict.
* **Duplicate vertices are reported as a pair count.** The *Select Duplicate Vertices* tool selects the candidate vertices involved in those pairs, so the selected vertex count can differ from the reported pair count.
* **UVs outside 0–1 are `WARN` / `REVIEW_REQUIRED`.** Tiling UVs are often intentional. The *Select UV Out-of-Bounds Faces* tool selects the affected faces for review only — the add-on never normalizes, wraps, scales, or edits UVs automatically.
* **Missing UV maps are `ERROR` with a `SAFE_AUTO` classification**, but no automatic fix is currently executed.
* **Non-power-of-two texture sizes are `WARN` / `REVIEW_REQUIRED`.** This is a compatibility/performance warning, not a guaranteed export failure — some workflows intentionally use non-power-of-two textures. The add-on does not resize or replace textures automatically.
* **High vertex count is `WARN` / `REVIEW_REQUIRED`.** The threshold (default 65,000, configurable per scene) is a warning aid, not a hard export guarantee. Meshes above it may need to be split or optimized; the add-on does not do this automatically.

---

## Non-Destructive Policy

This add-on is currently a preflight/review helper. It:

* does **not** replace Sollumz,
* does **not** export assets,
* does **not** automatically fix geometry,
* does **not** merge vertices,
* does **not** delete geometry,
* does **not** recalculate normals,
* does **not** edit UVs,
* does **not** edit materials,
* does **not** change transforms.

Review Tools only change selection state, the active object, the object mode, and the mesh select mode. Some reported issues may be intentional depending on the model — always review warnings manually.

---

## Installation

Download or create a zip file with this structure:

```text
Sollumz-Model-Prepper.zip
└─ sollumz_model_prepper/
   ├─ __init__.py
   ├─ preferences.py
   ├─ checks/
   ├─ operators/
   ├─ properties/
   ├─ ui/
   └─ utils/
```

In Blender:

1. Open **Edit > Preferences > Add-ons**
2. Click **Install from Disk...**
3. Select `Sollumz-Model-Prepper.zip`
4. Enable **Sollumz Model Prepper**

After enabling, open the 3D Viewport sidebar with `N` and select the **Sollumz Prepper** tab.

---

## Not Implemented Yet / Roadmap

The following are **not** implemented in the current version:

* Automatic *Fix Safe Issues* execution
* Apply Scale button
* Add missing UV map button
* Collision generation
* Room / Portal authoring tools
* Full Sollumz export automation
* Vertex color presence check
* Face orientation overlay helper
* Frame Selected / viewport navigation from result rows

---

## Development Notes

* An add-on preferences entry is registered as the home for add-on-level configuration (no settings are exposed there yet).
* Scene and Object property groups are registered as `Scene.smp` and `Object.smp`, storing preflight state (results, status, timestamps) and object-level metadata.
* Geometry detection conditions (zero-area faces, open boundary edges, complex non-manifold edges, loose geometry, duplicate vertices) are centralized in `checks/geometry_detection.py`. Both the Preflight checks and the Review Tools call the same shared helpers, so reported counts and selected review elements cannot drift apart.
* Check functions are plain functions returning a bpy-independent `CheckResult` dataclass, so detection logic can be reasoned about (and eventually unit-tested) outside Blender.
* A quick syntax sanity check across the add-on can be run with `python -m py_compile` on the module files.

---

## License

TBD.
