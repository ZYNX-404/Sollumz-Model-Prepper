import bpy
from bpy.props import PointerProperty

from .check_result import SMPCheckResult
from .scene_props import SMPSceneProperties
from .object_props import SMPObjectProperties


classes = (
    SMPCheckResult,
    SMPSceneProperties,
    SMPObjectProperties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.smp = PointerProperty(type=SMPSceneProperties)
    bpy.types.Object.smp = PointerProperty(type=SMPObjectProperties)


def unregister():
    if hasattr(bpy.types.Scene, "smp"):
        del bpy.types.Scene.smp
    if hasattr(bpy.types.Object, "smp"):
        del bpy.types.Object.smp

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
