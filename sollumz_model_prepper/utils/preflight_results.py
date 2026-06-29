"""
Preflight result management helpers.

These functions operate on scene.smp (SMPSceneProperties) and are the
single point of truth for initialising, populating, and finalising
check state.  No Blender operators or mesh operations live here.
"""

import time

# ---------------------------------------------------------------------------
# Allowed Enum values — must match SMPCheckResult / SMPSceneProperties exactly.
# Centralised here so callers never write raw strings that diverge from the
# PropertyGroup definitions.
# ---------------------------------------------------------------------------

_VALID_SEVERITY = frozenset(("OK", "WARN", "ERROR"))
_VALID_FIX_TYPE = frozenset(("NONE", "SAFE_AUTO", "SAFE_MANUAL", "REVIEW_REQUIRED"))
_VALID_STATUS   = frozenset(("NONE", "PASS", "WARN", "FAIL"))


# ---------------------------------------------------------------------------
# Internal guard
# ---------------------------------------------------------------------------

def _get_smp(scene):
    """Return scene.smp or None if the PropertyGroup is not yet registered."""
    return getattr(scene, "smp", None)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def clear_results(scene) -> bool:
    """
    Reset all preflight state on scene.smp to initial values.

    Returns True on success, False if scene.smp is not available.
    """
    smp = _get_smp(scene)
    if smp is None:
        return False

    smp.check_results.clear()
    smp.checked_object_count = 0
    smp.check_status = "NONE"
    smp.last_check_time = 0.0
    return True


def add_result(
    scene,
    severity: str,
    code: str,
    message: str,
    object_name: str = "",
    fix_type: str = "NONE",
) -> bool:
    """
    Append one check result to scene.smp.check_results.

    Args:
        severity:    "OK" | "WARN" | "ERROR"  — maps to SMPCheckResult.status
        code:        check identifier string   — maps to SMPCheckResult.check_id
        message:     human-readable detail     — maps to SMPCheckResult.message
                     If object_name is given it is prepended: "[ObjName] message"
        object_name: optional source object name; embedded into message because
                     SMPCheckResult has no dedicated object_name field.
        fix_type:    "NONE" | "SAFE_AUTO" | "SAFE_MANUAL" | "REVIEW_REQUIRED"

    Returns True on success, False if scene.smp is not available or an
    invalid enum value is supplied (prevents Blender EnumProperty exceptions).
    """
    if severity not in _VALID_SEVERITY:
        return False
    if fix_type not in _VALID_FIX_TYPE:
        return False

    smp = _get_smp(scene)
    if smp is None:
        return False

    item = smp.check_results.add()
    item.check_id = code
    item.check_name = code          # display name; callers may override via direct access
    item.status = severity
    item.message = f"[{object_name}] {message}" if object_name else message
    item.fix_type = fix_type
    # item.detail_count is left at its default (0); callers that need a count
    # should set it directly on the returned item.
    return True


def set_check_started(scene, object_count: int) -> bool:
    """
    Mark the beginning of a preflight run.

    Resets all result state via clear_results() and records the number of
    objects that will be checked.

    T-004 design note — no RUNNING state:
      SMPSceneProperties.check_status has no "RUNNING" enum value and one is
      not added here.  After this call, check_status == "NONE" and
      last_check_time == 0.0.  The UI treats last_check_time == 0.0 as
      "not yet finished" and shows no result list until set_check_finished()
      is called.  A future task may introduce explicit in-progress signalling
      if needed.

    Returns True on success, False if scene.smp is not available.
    """
    if not clear_results(scene):
        return False

    smp = _get_smp(scene)
    if smp is None:
        return False

    smp.checked_object_count = object_count
    # last_check_time intentionally left at 0.0 — set by set_check_finished().
    return True


def set_check_finished(scene, status: str) -> bool:
    """
    Mark the end of a preflight run.

    Args:
        status: "NONE" | "PASS" | "WARN" | "FAIL"
                Must be a value present in SMPSceneProperties.check_status.
                Invalid values are rejected to prevent Blender EnumProperty
                exceptions; the function returns False without modifying state.

    Returns True on success, False if scene.smp is not available or status
    is not a recognised enum value.
    """
    if status not in _VALID_STATUS:
        return False

    smp = _get_smp(scene)
    if smp is None:
        return False

    smp.check_status = status
    smp.last_check_time = time.time()
    return True
