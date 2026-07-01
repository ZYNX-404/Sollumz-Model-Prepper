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
* Run Preflight operator
* Sidebar UI result display

Not implemented yet:

* Automatic fix execution
* Material Check
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
* Non-manifold geometry
* Zero-area faces
* Loose geometry

Typical results:

| Check                 | Severity | Fix Type          |
| --------------------- | -------- | ----------------- |
| Duplicate vertices    | `WARN`   | `SAFE_MANUAL`     |
| Non-manifold geometry | `ERROR`  | `REVIEW_REQUIRED` |
| Zero-area faces       | `WARN`   | `SAFE_MANUAL`     |
| Loose geometry        | `WARN`   | `REVIEW_REQUIRED` |

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

## MLO Collection Helper

The add-on includes a helper for creating a basic MLO collection structure.

It creates or reuses:

```text
MLO_<name>
├─ MLO_<name>_entities
├─ MLO_<name>_collision
└─ MLO_<name>_portals
```

Existing collections are not destroyed.

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
