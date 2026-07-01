"""
checks package — Preflight check functions.

Each check function takes a bpy.types.Object and returns list[CheckResult].
CHECK_FUNCTIONS is the canonical ordered list used by run_all_checks().

T-009 (material_check) is not imported here yet; it will be added when that
task is implemented.
"""

from .result import CheckResult
from .transform_check import check_transform
from .normal_check import check_normals
from .geometry_check import check_geometry
from .uv_check import check_uv

CHECK_FUNCTIONS = [
    check_transform,
    check_normals,
    check_geometry,
    check_uv,
    # check_material,   # T-009
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
