# Sollumz Model Prepper

A Blender add-on for preparing existing building / interior models before exporting with Sollumz.

**Sollumz Model Prepper** does not replace Sollumz.
It is a small helper add-on focused on preflight checks, collection setup, and export-preparation workflows for GTA V / FiveM style MLO work.

The goal is to catch common setup issues early before export.

---

## Current Status

This project is currently in MVP stage.

Implemented:

* MLO collection setup helper
* Preflight check result system
* Transform Check
* Normal Check
* Geometry Check
* UV Check
* Material Check
* Run Preflight operator
* Sidebar UI result display
* Result severity summary
* Show / hide OK results filter

Not implemented yet:

* Automatic fix execution
* Collision generation
* Room / Portal authoring tools
* Full Sollumz export automation

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

## Basic Usage

### Run Preflight

1. Select one or more mesh objects.
2. Open **3D Viewport > Sidebar > Sollumz Prepper**.
3. Click **Run Preflight**.
4. Review the results in the panel.

The operator only checks selected mesh objects.

If no mesh object is selected, the button will be disabled or the operator will cancel safely.

---

## Preflight Status

The panel shows an overall status:

| Status | Meaning                                                                  |
| ------ | ------------------------------------------------------------------------ |
| `NONE` | No check has been run yet.                                               |
| `PASS` | No warnings or errors were detected.                                     |
| `WARN` | One or more warnings were detected, but no errors.                       |
| `FAIL` | One or more errors were detected. Manual action is needed before export. |

---

## Result Severity

Each check result has a severity:

| Severity | Meaning                                               |
| -------- | ----------------------------------------------------- |
| `OK`     | No issue detected.                                    |
| `WARN`   | Something may need review, but it can be intentional. |
| `ERROR`  | A likely export or setup issue was detected.          |

---

## Fix Type

Each result also has a fix type:

| Fix Type          | Meaning                                                                                     |
| ----------------- | ------------------------------------------------------------------------------------------- |
| `NONE`            | No fix needed.                                                                              |
| `SAFE_AUTO`       | Intended to be safely fixable automatically in the future. Not executed in the current MVP. |
| `SAFE_MANUAL`     | Usually fixable, but should be reviewed and applied manually.                               |
| `REVIEW_REQUIRED` | Requires manual review. Automatic fixing is not recommended.                                |

Current MVP does not execute any fixes.

---

## Result Filtering

The Preflight panel includes a result summary and display filter.

The summary shows:

* `Errors`
* `Warnings`
* `OK`

These counts are based on all stored check results.

The **Show OK Results** option controls only the visible result list:

| Option   | Behavior                                                      |
| -------- | ------------------------------------------------------------- |
| Enabled  | Shows `OK`, `WARN`, and `ERROR` results.                      |
| Disabled | Hides `OK` results and shows only `WARN` and `ERROR` results. |

This is useful for large production assets where most checks pass but a small number of warnings need review.

---

## Checks

### Transform Check

Checks whether object transforms are export-ready.

Detected issues:

* Scale is not applied
* Rotation is not applied
* Object origin is not at world zero

Typical results:

| Check                | Severity | Fix Type          |
| -------------------- | -------- | ----------------- |
| Scale not applied    | `ERROR`  | `SAFE_MANUAL`     |
| Rotation not applied | `WARN`   | `REVIEW_REQUIRED` |
| Non-zero location    | `WARN`   | `REVIEW_REQUIRED` |

---

### Normal Check

Checks for faces that may have inward-facing normals.

Because interior walls, backfaces, and open building meshes can be intentional, this check is conservative.

Typical results:

| Check                    | Severity | Fix Type      |
| ------------------------ | -------- | ------------- |
| Possibly flipped normals | `WARN`   | `SAFE_MANUAL` |

This check does not automatically recalculate normals.

---

### Geometry Check

Checks for common mesh geometry issues.

Detected issues:

* Duplicate vertices
* Open boundary edges
* Complex non-manifold edges
* Zero-area faces
* Loose geometry

Typical results:

| Check                      | Severity | Fix Type          |
| -------------------------- | -------- | ----------------- |
| Duplicate vertices         | `WARN`   | `SAFE_MANUAL`     |
| Open boundary edges        | `WARN`   | `REVIEW_REQUIRED` |
| Complex non-manifold edges | `ERROR`  | `REVIEW_REQUIRED` |
| Zero-area faces            | `WARN`   | `SAFE_MANUAL`     |
| Loose geometry             | `WARN`   | `REVIEW_REQUIRED` |

#### Open Boundary vs Complex Non-Manifold

Open boundary edges are reported separately from complex non-manifold edges.

Open boundary edges are edges connected to only one face.
They are common in open props, thin surfaces, containers, shelves, interior meshes, and other game-ready assets. These are reported as `WARN` because they may be intentional.

Complex non-manifold edges are edges connected to three or more faces.
These are more likely to indicate broken topology and are reported as `ERROR`.

This check is read-only and does not modify mesh data.

---

### UV Check

Checks whether the mesh has UV maps and whether active UV coordinates are within the `[0, 1]` range.

Detected issues:

* Missing UV map
* UV coordinates outside `[0, 1]`

Typical results:

| Check               | Severity | Fix Type          |
| ------------------- | -------- | ----------------- |
| Missing UV map      | `ERROR`  | `SAFE_AUTO`       |
| UV outside `[0, 1]` | `WARN`   | `REVIEW_REQUIRED` |

UV tiling may be intentional, so out-of-bounds UVs are reported as warnings rather than errors.

The current MVP does not create UV layers automatically.

---

### Material Check

Checks whether mesh objects have usable material assignments and image textures.

Detected issues:

* No material slots
* Empty material slots
* Empty material names
* Materials without detected image textures

Typical results:

| Check                 | Severity | Fix Type          |
| --------------------- | -------- | ----------------- |
| No material slots     | `ERROR`  | `SAFE_MANUAL`     |
| Empty material slots  | `WARN`   | `SAFE_MANUAL`     |
| Empty material names  | `WARN`   | `SAFE_MANUAL`     |
| Missing image texture | `WARN`   | `REVIEW_REQUIRED` |

Image texture detection looks for Image Texture nodes with assigned images in node-based materials.

Materials without detected image textures are reported as `WARN`, not `ERROR`, because procedural materials, custom shaders, or special material setups may be intentional.

This check does not create materials, assign materials, create textures, or modify shader nodes.

---

## Design Goals

* Keep Sollumz as the actual export tool.
* Provide preparation and validation before export.
* Avoid destructive automatic edits.
* Prefer warnings for ambiguous building / interior modeling cases.
* Make common export mistakes visible in Blender UI.
* Keep MVP behavior predictable and safe.

---

## Safety Notes

This add-on is currently read-only for preflight checks.

The Preflight runner does not:

* Modify mesh data
* Recalculate normals
* Add UV layers
* Remove vertices
* Merge geometry
* Execute automatic fixes
* Run Sollumz export

Some results may be intentional depending on the model. Always review warnings manually.

---

## Development Roadmap

Possible future tasks:

* Fix Safe Issues operator
* Empty UV map creation for `uv_missing`
* Material Check
* Collision base copy workflow improvements
* Room / Portal helper tools
* Export checklist presets
* Better result filtering in UI
* Per-check enable / disable options

---

## License

TBD.
