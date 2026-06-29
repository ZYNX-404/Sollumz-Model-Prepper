from bpy.props import CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
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
