"""
checks package — Preflight check functions.

Each check function takes a bpy.types.Object and returns list[CheckResult].
CHECK_FUNCTIONS is the canonical ordered list used by run_all_checks().

T-006 (normal_check), T-007 (geometry_check), T-008 (uv_check) are not
imported here yet; they will be added when those tasks are implemented.
"""

from .result import CheckResult
from .transform_check import check_transform

CHECK_FUNCTIONS = [
    check_transform,
    # check_normals,    # T-006
    # check_geometry,   # T-007
    # check_uv,         # T-008
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
