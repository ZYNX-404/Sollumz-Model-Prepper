"""
UV Check — T-008.

Inspects UV maps in read-only mode.
No mesh modification, no uv_layers.new(), no bpy.ops.mesh.*.

Two sub-checks are performed:
  A. UV Map existence  — SAFE_AUTO (detection only; Fix is Post-MVP)
  B. UV out-of-bounds  — REVIEW_REQUIRED (shared with the Review Tools
                         via uv_detection.py; counted per face)

Fix processing is Post-MVP.  This module only detects problems.
"""

from .result import CheckResult
from .uv_detection import find_uv_out_of_bounds_face_indices


def check_uv(obj) -> list[CheckResult]:
    """
    Return a list of CheckResult entries for UV issues found in *obj*.

    Args:
        obj: A bpy.types.Object with a mesh data-block (obj.data).
             The mesh is never modified.
    """
    results: list[CheckResult] = []
    mesh = obj.data

    # --- A. UV Map existence ---
    if not mesh.uv_layers:
        results.append(CheckResult(
            check_id="uv_missing",
            check_name="No UV Map",
            status="ERROR",
            message="No UV map found. An empty UV map can be added by Fix Safe Issues.",
            fix_type="SAFE_AUTO",
            detail_count=0,
        ))
        return results

    results.append(CheckResult(
        check_id="uv_missing",
        check_name="UV Map",
        status="OK",
        message=f"{len(mesh.uv_layers)} UV layer(s) found.",
        fix_type="NONE",
        detail_count=len(mesh.uv_layers),
    ))

    # --- B. UV out-of-bounds ---
    if mesh.uv_layers.active is None:
        results.append(CheckResult(
            check_id="uv_out_of_bounds",
            check_name="UV Bounds",
            status="OK",
            message="No active UV layer to check.",
            fix_type="NONE",
        ))
        return results

    # Shared detection — same condition as the Select UV Out-of-Bounds
    # Faces review tool; detail_count is the out-of-bounds face count.
    out_count = len(find_uv_out_of_bounds_face_indices(mesh))

    if out_count:
        results.append(CheckResult(
            check_id="uv_out_of_bounds",
            check_name="UV Out of Bounds",
            status="WARN",
            message=(
                f"{out_count} face(s) have UV coordinates outside the [0,1] range. "
                "May be intentional tiling — review manually."
            ),
            fix_type="REVIEW_REQUIRED",
            detail_count=out_count,
        ))
    else:
        results.append(CheckResult(
            check_id="uv_out_of_bounds",
            check_name="UV Bounds",
            status="OK",
            message="All UVs are within [0,1] range.",
            fix_type="NONE",
            detail_count=0,
        ))

    return results
