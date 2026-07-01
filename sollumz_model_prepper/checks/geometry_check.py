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

import bmesh

from .result import CheckResult

DUPLICATE_VERT_DIST = 0.0001
ZERO_AREA_THRESHOLD = 1e-8


def check_geometry(obj) -> list[CheckResult]:
    """
    Return a list of CheckResult entries for geometry issues found in *obj*.

    Args:
        obj: A bpy.types.Object with a mesh data-block (obj.data).
             The mesh is never modified.
    """
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        results = [
            _check_duplicate_verts(bm),
            _check_open_boundary(bm),
            _check_complex_non_manifold(bm),
            _check_zero_area_faces(bm),
            _check_loose_geometry(bm),
        ]
    finally:
        bm.free()

    return results


# ---------------------------------------------------------------------------
# Sub-checks
# ---------------------------------------------------------------------------

def _check_duplicate_verts(bm) -> CheckResult:
    ret = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=DUPLICATE_VERT_DIST)
    dupe_count = len(ret["targetmap"])

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


def _check_open_boundary(bm) -> CheckResult:
    count = sum(1 for e in bm.edges if len(e.link_faces) == 1)

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


def _check_complex_non_manifold(bm) -> CheckResult:
    count = sum(1 for e in bm.edges if len(e.link_faces) >= 3)

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



def _check_zero_area_faces(bm) -> CheckResult:
    zero_faces = [f for f in bm.faces if f.calc_area() < ZERO_AREA_THRESHOLD]
    count = len(zero_faces)

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


def _check_loose_geometry(bm) -> CheckResult:
    loose_verts = [v for v in bm.verts if not v.link_edges]
    loose_edges = [e for e in bm.edges if not e.link_faces]
    loose_vert_count = len(loose_verts)
    loose_edge_count = len(loose_edges)
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
