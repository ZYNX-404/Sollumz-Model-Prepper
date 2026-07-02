"""
Geometry Check — T-007 / T-007.1.

Inspects mesh geometry using bmesh in read-only mode.
No mesh modification, no bm.to_mesh(), no bpy.ops.mesh.*, no repair ops.

Five sub-checks are performed:
  A. Duplicate Vertices       — SAFE_MANUAL
  B. Open Boundary Edges      — REVIEW_REQUIRED  (link_faces == 1 → WARN)
  C. Complex Non-Manifold     — REVIEW_REQUIRED  (link_faces >= 3 → ERROR)
  D. Zero Area Faces          — SAFE_MANUAL
  E. Loose Geometry           — REVIEW_REQUIRED  (link_faces == 0)

T-007.1: non_manifold was split into open_boundary (WARN) and
complex_non_manifold (ERROR) to avoid false positives on open props,
thin surfaces, and interior meshes common in GTA/FiveM/MLO assets.

Fix processing is Post-MVP.  This module only detects problems.
"""

from .geometry_detection import (
    DUPLICATE_VERT_DIST,
    find_duplicate_vertex_pairs,
    find_zero_area_face_indices,
    find_open_boundary_edge_indices,
    find_complex_non_manifold_edge_indices,
    find_loose_vertex_indices,
    find_loose_edge_indices,
)
from .result import CheckResult


def check_geometry(obj) -> list[CheckResult]:
    """
    Return a list of CheckResult entries for geometry issues found in *obj*.

    All detection is delegated to geometry_detection.py, which is shared
    with the Review Tools.

    Args:
        obj: A bpy.types.Object with a mesh data-block (obj.data).
             The mesh is never modified.
    """
    mesh = obj.data

    return [
        _check_duplicate_verts(mesh),
        _check_open_boundary(mesh),
        _check_complex_non_manifold(mesh),
        _check_zero_area_faces(mesh),
        _check_loose_geometry(mesh),
    ]


# ---------------------------------------------------------------------------
# Sub-checks
# ---------------------------------------------------------------------------

def _check_duplicate_verts(mesh) -> CheckResult:
    # Pair count == len(find_doubles targetmap); same as before extraction
    dupe_count = len(find_duplicate_vertex_pairs(mesh))

    if dupe_count:
        return CheckResult(
            check_id="dupe_vertex",
            check_name="Duplicate Vertices",
            status="WARN",
            message=f"{dupe_count} duplicate vertex pair(s) found (dist < {DUPLICATE_VERT_DIST}).",
            fix_type="SAFE_MANUAL",
            detail_count=dupe_count,
        )

    return CheckResult(
        check_id="dupe_vertex",
        check_name="Duplicate Vertices",
        status="OK",
        message="No duplicate vertices found.",
    )


def _check_open_boundary(mesh) -> CheckResult:
    count = len(find_open_boundary_edge_indices(mesh))

    if count:
        return CheckResult(
            check_id="open_boundary",
            check_name="Open Boundary Edges",
            status="WARN",
            message=(
                f"{count} open boundary edge(s) found. "
                "This may be intentional for open props, thin surfaces, or interior meshes "
                "— review manually."
            ),
            fix_type="REVIEW_REQUIRED",
            detail_count=count,
        )

    return CheckResult(
        check_id="open_boundary",
        check_name="Open Boundary Edges",
        status="OK",
        message="No open boundary edges.",
        fix_type="NONE",
        detail_count=0,
    )


def _check_complex_non_manifold(mesh) -> CheckResult:
    count = len(find_complex_non_manifold_edge_indices(mesh))

    if count:
        return CheckResult(
            check_id="complex_non_manifold",
            check_name="Complex Non-Manifold",
            status="ERROR",
            message=(
                f"{count} complex non-manifold edge(s) found. "
                "Edges connected to 3 or more faces require manual review."
            ),
            fix_type="REVIEW_REQUIRED",
            detail_count=count,
        )

    return CheckResult(
        check_id="complex_non_manifold",
        check_name="Complex Non-Manifold",
        status="OK",
        message="No complex non-manifold edges.",
        fix_type="NONE",
        detail_count=0,
    )



def _check_zero_area_faces(mesh) -> CheckResult:
    count = len(find_zero_area_face_indices(mesh))

    if count:
        return CheckResult(
            check_id="zero_area_face",
            check_name="Zero Area Faces",
            status="WARN",
            message=f"{count} zero-area face(s) found.",
            fix_type="SAFE_MANUAL",
            detail_count=count,
        )

    return CheckResult(
        check_id="zero_area_face",
        check_name="Face Areas",
        status="OK",
        message="No zero-area faces.",
    )


def _check_loose_geometry(mesh) -> CheckResult:
    loose_vert_count = len(find_loose_vertex_indices(mesh))
    loose_edge_count = len(find_loose_edge_indices(mesh))
    loose_count = loose_vert_count + loose_edge_count

    if loose_count:
        return CheckResult(
            check_id="loose_geo",
            check_name="Loose Geometry",
            status="WARN",
            message=(
                f"{loose_vert_count} loose vert(s), {loose_edge_count} loose edge(s). "
                "Review manually."
            ),
            fix_type="REVIEW_REQUIRED",
            detail_count=loose_count,
        )

    return CheckResult(
        check_id="loose_geo",
        check_name="Loose Geometry",
        status="OK",
        message="No loose geometry.",
    )
