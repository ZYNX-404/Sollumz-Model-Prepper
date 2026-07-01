"""
checks package — Preflight check functions.

Each check function takes a bpy.types.Object and returns list[CheckResult].
CHECK_FUNCTIONS is the canonical ordered list used by run_all_checks().

Registered checks (in order):
  1. check_transform   — scale / rotation / location
  2. check_normals     — custom normals presence
  3. check_geometry    — duplicate verts, open boundary, complex non-manifold,
                         zero area faces, loose geometry
  4. check_uv          — UV map presence and validity
  5. check_materials   — material slots, empty slots, names, image textures
"""

from .result import CheckResult
from .transform_check import check_transform
from .normal_check import check_normals
from .geometry_check import check_geometry
from .uv_check import check_uv
from .material_check import check_materials

CHECK_FUNCTIONS = [
    check_transform,
    check_normals,
    check_geometry,
    check_uv,
    check_materials,
]


def run_all_checks(obj) -> list[CheckResult]:
    """
    Run all registered check functions against *obj* and return a flat list
    of CheckResult entries.

    Callers are responsible for ensuring *obj* is a valid MESH object.
    """
    results: list[CheckResult] = []
    for fn in CHECK_FUNCTIONS:
        results.extend(fn(obj))
    return results
