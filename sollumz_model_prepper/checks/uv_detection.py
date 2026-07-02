"""
Shared UV detection helpers.

Single source of truth for the UV out-of-bounds condition used by both
checks/uv_check.py (Preflight) and operators/review_ops.py (Review
Tools), so the two can never drift apart.

Read-only: UV data and meshes are never modified.
"""


def find_uv_out_of_bounds_face_indices(mesh) -> list[int]:
    """
    Return indices of faces with at least one UV coordinate outside [0, 1].

    Uses the active UV layer; returns an empty list when none exists.
    Coordinates exactly at 0.0 or 1.0 count as in bounds.
    """
    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        return []

    uv_data = uv_layer.data
    out_faces = []
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            u, v = uv_data[loop_index].uv
            if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
                out_faces.append(poly.index)
                break
    return out_faces
