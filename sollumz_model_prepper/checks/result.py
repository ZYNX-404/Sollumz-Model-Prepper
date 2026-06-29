"""
CheckResult dataclass — the return type of every check function.

This is a plain Python dataclass; it has no dependency on bpy and can be
unit-tested without a running Blender instance.
"""

from dataclasses import dataclass, field
from typing import Literal

Status  = Literal["OK", "WARN", "ERROR"]
FixType = Literal["NONE", "SAFE_AUTO", "SAFE_MANUAL", "REVIEW_REQUIRED"]


@dataclass
class CheckResult:
    check_id:     str
    check_name:   str
    status:       Status
    message:      str
    fix_type:     FixType = field(default="NONE")
    detail_count: int     = field(default=0)
