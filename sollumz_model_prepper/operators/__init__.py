import bpy

from .collection_ops import SMP_OT_CreateMLOCollection
from .preflight_ops import SMP_OT_RunPreflight

_classes = (
    SMP_OT_CreateMLOCollection,
    SMP_OT_RunPreflight,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
