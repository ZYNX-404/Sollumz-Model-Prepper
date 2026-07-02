"""
Result Operators — navigation helpers for preflight result rows.

These operators change object selection and active object only.
No mesh geometry, transforms, materials, hide state, or selectability
flags are modified.
"""

import bpy
from bpy.props import StringProperty
from bpy.types import Operator


class SMP_OT_SelectResultObject(Operator):
    bl_idname = "smp.select_result_object"
    bl_label = "Select Result Object"
    bl_description = "Select and activate the object associated with this preflight result"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: StringProperty(
        name="Object Name",
        default="",
    )

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        if not self.object_name:
            self.report({'WARNING'}, "No object name stored for this result.")
            return {'CANCELLED'}

        obj = bpy.data.objects.get(self.object_name)
        if obj is None:
            self.report({'WARNING'}, f"Object not found: {self.object_name}")
            return {'CANCELLED'}

        # Membership check via name set — direct `in view_layer.objects`
        # lookup behaviour varies across versions.
        if obj.name not in {o.name for o in context.view_layer.objects}:
            self.report({'WARNING'}, f"Object is not in the current view layer: {obj.name}")
            return {'CANCELLED'}

        # Hidden objects are not force-shown; report and bail instead.
        if obj.hide_get() or obj.hide_viewport:
            self.report({'WARNING'}, f"Object is hidden: {obj.name}. Unhide it to select.")
            return {'CANCELLED'}

        # Selection-locked objects are not force-unlocked either.
        if obj.hide_select:
            self.report({'WARNING'}, f"Object is not selectable: {obj.name}.")
            return {'CANCELLED'}

        # Leave Edit Mode (e.g. after a Review Tool) before changing selection.
        if context.object is not None and context.object.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                self.report({'WARNING'}, "Could not switch to Object Mode.")
                return {'CANCELLED'}

        for o in context.view_layer.objects:
            o.select_set(False)

        obj.select_set(True)
        context.view_layer.objects.active = obj

        self.report({'INFO'}, f"Selected object: {obj.name}")
        return {'FINISHED'}
