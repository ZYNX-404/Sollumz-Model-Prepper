from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


class SMPCheckResult(PropertyGroup):
    check_id: StringProperty()
    check_name: StringProperty()
    status: EnumProperty(
        items=[
            ("OK", "OK", ""),
            ("WARN", "Warning", ""),
            ("ERROR", "Error", ""),
        ],
        default="OK",
    )
    message: StringProperty()
    fix_type: EnumProperty(
        items=[
            ("NONE", "No Fix", ""),
            ("SAFE_AUTO", "Safe Auto", ""),
            ("SAFE_MANUAL", "Safe Manual", ""),
            ("REVIEW_REQUIRED", "Review Required", ""),
        ],
        default="NONE",
    )
    detail_count: IntProperty(default=0)
