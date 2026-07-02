"""
Shared geometry detection helpers.

Single source of truth for the detection conditions used by both
checks/geometry_check.py (Preflight) and operators/review_ops.py
(Review Tools), so the two can never drift apart.

All functions are read-only: the mesh is never modified, bmesh
instances are detection-only and always freed, and bm.to_mesh()
is never called.
"""

import bmesh

ZERO_AREA_THRESHOLD = 1e-8
DUPLICATE_VERT_DIST = 0.0001


def find_zero_area_face_indices(mesh, threshold=ZERO_AREA_THRESHOLD) -> list[int]:
    """Return indices of faces whose area is below *threshold*."""
    return [poly.index for poly in mesh.polygons if poly.area < threshold]


def find_open_boundary_edge_indices(mesh) -> list[int]:
    """Return indices of edges linked to exactly one face."""
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()
        return [e.index for e in bm.edges if len(e.link_faces) == 1]
    finally:
        bm.free()


def find_complex_non_manifold_edge_indices(mesh) -> list[int]:
    """Return indices of edges linked to three or more faces."""
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()
        return [e.index for e in bm.edges if len(e.link_faces) >= 3]
    finally:
        bm.free()


def find_duplicate_vertex_pairs(mesh, threshold=DUPLICATE_VERT_DIST) -> list[tuple[int, int]]:
    """
    Return (duplicate, target) vertex index pairs closer than *threshold*.

    Uses bmesh.ops.find_doubles, which only detects — no welding is
    performed. The pair count equals len(targetmap), the value the
    Preflight dupe_vertex check reports as detail_count.
    """
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        ret = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=threshold)
        return [(v.index, t.index) for v, t in ret["targetmap"].items()]
    finally:
        bm.free()


def find_duplicate_vertex_indices(mesh, threshold=DUPLICATE_VERT_DIST) -> set[int]:
    """Return indices of all vertices involved in a duplicate pair."""
    indices: set[int] = set()
    for dupe_idx, target_idx in find_duplicate_vertex_pairs(mesh, threshold):
        indices.add(dupe_idx)
        indices.add(target_idx)
    return indices


def find_loose_vertex_indices(mesh) -> list[int]:
    """Return indices of vertices not linked to any edge."""
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        return [v.index for v in bm.verts if not v.link_edges]
    finally:
        bm.free()


def find_loose_edge_indices(mesh) -> list[int]:
    """Return indices of edges not linked to any face."""
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()
        return [e.index for e in bm.edges if not e.link_faces]
    finally:
        bm.free()
