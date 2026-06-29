"""
Transform Check — T-005.

Inspects Scale, Rotation, and Location of a Blender Object.
Detection only: no mesh modification, no Fix operators, no bpy.ops.mesh.*.
"""

from mathutils import Euler, Vector

from .result import CheckResult

SCALE_TOL = 1e-4
ROT_TOL   = 1e-4
LOC_TOL   = 1e-4

_IDENTITY_SCALE    = Vector((1.0, 1.0, 1.0))
_ZERO_QUAT         = Euler((0.0, 0.0, 0.0)).to_quaternion()


def check_transform(obj) -> list[CheckResult]:
    """
    Return a list of CheckResult entries covering Scale, Rotation, and
    Location for *obj*.  Always returns exactly three items (one per axis
    of concern) so callers can rely on a stable result count.

    Args:
        obj: A bpy.types.Object.  Must not be None; callers are responsible
             for pre-filtering to MESH objects if desired.
    """
    results: list[CheckResult] = []
    results.append(_check_scale(obj))
    results.append(_check_rotation(obj))
    results.append(_check_location(obj))
    return results


# ---------------------------------------------------------------------------
# Scale
# ---------------------------------------------------------------------------

def _check_scale(obj) -> CheckResult:
    scale_vec = Vector(obj.scale)
    diff = (scale_vec - _IDENTITY_SCALE).length

    if diff > SCALE_TOL:
        scale_str = f"({obj.scale.x:.4f}, {obj.scale.y:.4f}, {obj.scale.z:.4f})"
        return CheckResult(
            check_id="transform_scale",
            check_name="Scale Not Applied",
            status="ERROR",
            message=f"Scale {scale_str} is not (1, 1, 1). Apply scale before export.",
            fix_type="SAFE_MANUAL",
        )

    return CheckResult(
        check_id="transform_scale",
        check_name="Scale",
        status="OK",
        message="Scale is applied.",
    )


# ---------------------------------------------------------------------------
# Rotation
# ---------------------------------------------------------------------------

def _check_rotation(obj) -> CheckResult:
    if obj.rotation_mode == "QUATERNION":
        return CheckResult(
            check_id="transform_rotation",
            check_name="Rotation Mode",
            status="WARN",
            message=(
                "Object uses Quaternion rotation mode. "
                "Cannot check rotation as Euler."
            ),
            fix_type="REVIEW_REQUIRED",
        )

    # Covers XYZ, XZY, YXZ, YZX, ZXY, ZYX Euler modes.
    euler = obj.rotation_euler
    angle = euler.to_quaternion().rotation_difference(_ZERO_QUAT).angle

    if angle > ROT_TOL:
        rot_str = (
            f"({euler.x:.4f}, {euler.y:.4f}, {euler.z:.4f})"
        )
        return CheckResult(
            check_id="transform_rotation",
            check_name="Rotation Not Applied",
            status="WARN",
            message=(
                f"Rotation {rot_str} is not (0, 0, 0). "
                "May affect export alignment."
            ),
            fix_type="REVIEW_REQUIRED",
        )

    return CheckResult(
        check_id="transform_rotation",
        check_name="Rotation",
        status="OK",
        message="Rotation is applied.",
    )


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

def _check_location(obj) -> CheckResult:
    loc_len = Vector(obj.location).length

    if loc_len > LOC_TOL:
        loc_str = (
            f"({obj.location.x:.4f}, {obj.location.y:.4f}, {obj.location.z:.4f})"
        )
        return CheckResult(
            check_id="transform_location",
            check_name="Non-zero Origin",
            status="WARN",
            message=(
                f"Object origin is at {loc_str}. "
                "Confirm this is intentional."
            ),
            fix_type="REVIEW_REQUIRED",
        )

    return CheckResult(
        check_id="transform_location",
        check_name="Location",
        status="OK",
        message="Origin is at world zero.",
    )
