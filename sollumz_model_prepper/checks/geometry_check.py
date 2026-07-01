"""
Geometry Check — T-007.

Inspects mesh geometry using bmesh in read-only mode.
No mesh modification, no bm.to_mesh(), no bpy.ops.mesh.*, no repair ops.

Four sub-checks are performed:
  A. Duplicate Vertices  — SAFE_MANUAL
  B. Non-Manifold Geometry — REVIEW_REQUIRED
  C. Zero Area Faces     — SAFE_MANUAL
  D. Loose Geometry      — REVIEW_REQUIRED

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
            _check_non_manifold(bm),
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


def _check_non_manifold(bm) -> CheckResult:
    non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
    non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
    edge_count = len(non_manifold_edges)
    vert_count = len(non_manifold_verts)
    nm_count = edge_count + vert_count

    if nm_count:
        return CheckResult(
            check_id="non_manifold",
            check_name="Non-Manifold Geometry",
            status="ERROR",
            message=(
                f"{edge_count} non-manifold edge(s), {vert_count} non-manifold vert(s). "
                "Manual review required."
            ),
            fix_type="REVIEW_REQUIRED",
            detail_count=nm_count,
        )

    return CheckResult(
        check_id="non_manifold",
        check_name="Manifold",
        status="OK",
        message="Mesh is manifold.",
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
