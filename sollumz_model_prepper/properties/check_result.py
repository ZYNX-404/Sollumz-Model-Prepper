from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


class SMPCheckResult(PropertyGroup):
    check_id: StringProperty()
    check_name: StringProperty(
        name="Check Name",
        description="Human-readable check name",
        default="",
    )
    object_name: StringProperty(
        name="Object Name",
        description="Name of the object this result belongs to",
        default="",
    )
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
    detail_count: IntProperty(
        name="Detail Count",
        description="Number of detected details for this result",
        default=0,
        min=0,
    )
