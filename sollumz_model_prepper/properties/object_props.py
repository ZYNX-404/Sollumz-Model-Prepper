from bpy.props import BoolProperty, StringProperty
from bpy.types import PropertyGroup


class SMPObjectProperties(PropertyGroup):
    is_collision_base_copy: BoolProperty(default=False)
    source_object_name: StringProperty()
    preflight_passed: BoolProperty(default=False)
