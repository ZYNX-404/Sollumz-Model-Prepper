import bpy
from bpy.types import AddonPreferences


class SMPAddonPreferences(AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        pass


def register():
    bpy.utils.register_class(SMPAddonPreferences)


def unregister():
    bpy.utils.unregister_class(SMPAddonPreferences)
