"""
Normal Check — T-006.

Inspects face normals using bmesh in read-only mode.
No mesh modification, no bm.to_mesh(), no bpy.ops.mesh.*.

Detection is heuristic: the dot product between each face normal and the
vector from the mesh centroid to the face centre is used to flag faces that
may be pointing inward.  This is an approximation — interior walls, open
meshes, and concave geometry can produce false positives.  Results are
therefore capped at WARN and the message explicitly notes that interior
geometry may be intentional.
"""

import bmesh
from mathutils import Vector

from .result import CheckResult

# Minimum vector length below which the centroid→face direction is considered
# degenerate and the face is skipped (avoids division-by-zero on coincident
# centres).
_MIN_VEC_LEN = 1e-8


def check_normals(obj) -> list[CheckResult]:
    """
    Return a list containing exactly one CheckResult for 'normal_flip'.

    Args:
        obj: A bpy.types.Object with a mesh data-block (obj.data).
             The mesh is never modified.
    """
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.normal_update()

        if not bm.faces:
            return [CheckResult(
                check_id="normal_flip",
                check_name="Normals",
                status="OK",
                message="No faces to check.",
            )]

        flipped = _count_inward_faces(bm)

    finally:
        bm.free()

    if flipped == 0:
        return [CheckResult(
            check_id="normal_flip",
            check_name="Normals",
            status="OK",
            message="No obviously flipped faces.",
        )]

    return [CheckResult(
        check_id="normal_flip",
        check_name="Possibly Flipped Normals",
        status="WARN",
        message=(
            f"{flipped} face(s) may have inward normals. "
            "Interior walls may be intentional — review manually."
        ),
        fix_type="SAFE_MANUAL",
        detail_count=flipped,
    )]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _mesh_centroid(bm) -> Vector:
    """Return the average of all face centres as the mesh centroid."""
    centroid = Vector((0.0, 0.0, 0.0))
    for face in bm.faces:
        centroid += face.calc_center_median()
    centroid /= len(bm.faces)
    return centroid


def _count_inward_faces(bm) -> int:
    """
    Count faces whose normal points away from the mesh centroid (i.e. the
    dot product of the face normal with the centroid→face-centre vector is
    negative).

    Faces where the centroid→face-centre vector is shorter than _MIN_VEC_LEN
    are skipped because the direction is undefined for coincident points.
    """
    centroid = _mesh_centroid(bm)
    count = 0

    for face in bm.faces:
        to_face = face.calc_center_median() - centroid
        if to_face.length < _MIN_VEC_LEN:
            continue
        if face.normal.dot(to_face.normalized()) < 0.0:
            count += 1

    return count
