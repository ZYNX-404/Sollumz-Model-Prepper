"""
UV Check — T-008.

Inspects UV maps using bmesh in read-only mode.
No mesh modification, no bm.to_mesh(), no uv_layers.new(), no bpy.ops.mesh.*.

Two sub-checks are performed:
  A. UV Map existence  — SAFE_AUTO (detection only; Fix is Post-MVP)
  B. UV out-of-bounds  — REVIEW_REQUIRED

Fix processing is Post-MVP.  This module only detects problems.
"""

import bmesh

from .result import CheckResult


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
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()

        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            results.append(CheckResult(
                check_id="uv_out_of_bounds",
                check_name="UV Bounds",
                status="OK",
                message="No active UV layer to check.",
                fix_type="NONE",
            ))
            return results

        out_count = 0
        for face in bm.faces:
            for loop in face.loops:
                u, v = loop[uv_layer].uv
                if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
                    out_count += 1
    finally:
        bm.free()

    if out_count:
        results.append(CheckResult(
            check_id="uv_out_of_bounds",
            check_name="UV Out of Bounds",
            status="WARN",
            message=(
                f"{out_count} UV point(s) are outside [0,1] range. "
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
