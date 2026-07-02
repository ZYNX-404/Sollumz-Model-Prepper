from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup

from .check_result import SMPCheckResult


class SMPSceneProperties(PropertyGroup):
    mlo_name: StringProperty(name="MLO Name", default="MyMLO")
    last_check_time: FloatProperty(default=0.0)
    checked_object_count: IntProperty(default=0)
    check_results: CollectionProperty(type=SMPCheckResult)
    check_status: EnumProperty(
        items=[
            ("NONE", "Not Run", ""),
            ("PASS", "Pass", ""),
            ("WARN", "Warning", ""),
            ("FAIL", "Fail", ""),
        ],
        default="NONE",
    )
    remove_doubles_threshold: FloatProperty(
        name="Merge Distance",
        default=0.0001,
        min=0.00001,
        max=0.1,
        precision=5,
        step=1,
    )
    vertex_count_warn_threshold: IntProperty(
        name="Vertex Count Warning",
        description="Warn when a mesh object has more vertices than this value",
        default=65000,
        min=1,
    )
    show_ok_results: BoolProperty(
        name="Show OK Results",
        description="Show OK preflight results in the result list",
        default=False,
    )
