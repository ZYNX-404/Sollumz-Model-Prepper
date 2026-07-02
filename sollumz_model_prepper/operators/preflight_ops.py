from bpy.types import Operator

from .. import checks
from ..utils.preflight_results import add_result, set_check_started, set_check_finished


class SMP_OT_RunPreflight(Operator):
    bl_idname = "smp.run_preflight"
    bl_label = "Run Preflight"
    bl_description = "Run preflight checks on selected mesh objects"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene is None:
            return False
        if getattr(scene, "smp", None) is None:
            return False
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        scene = context.scene
        if scene is None:
            self.report({'WARNING'}, "No active scene.")
            return {'CANCELLED'}

        scene_props = getattr(scene, "smp", None)
        if scene_props is None:
            self.report({'WARNING'}, "Sollumz Model Prepper properties are not registered.")
            return {'CANCELLED'}

        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}

        if not set_check_started(scene, len(mesh_objects)):
            self.report({'WARNING'}, "Failed to initialise preflight state.")
            return {'CANCELLED'}

        has_error = False
        has_warn = False

        for obj in mesh_objects:
            for result in checks.run_all_checks(obj):
                add_result(
                    scene,
                    severity=result.status,
                    code=result.check_id,
                    message=result.message,
                    object_name=obj.name,
                    fix_type=result.fix_type,
                    check_name=result.check_name,
                    detail_count=result.detail_count,
                )
                if result.status == "ERROR":
                    has_error = True
                elif result.status == "WARN":
                    has_warn = True

        if has_error:
            final_status = "FAIL"
        elif has_warn:
            final_status = "WARN"
        else:
            final_status = "PASS"

        set_check_finished(scene, final_status)

        result_count = len(scene_props.check_results)
        self.report(
            {'INFO'},
            f"Preflight complete: {len(mesh_objects)} object(s), {result_count} result(s). Status: {final_status}",
        )
        return {'FINISHED'}
