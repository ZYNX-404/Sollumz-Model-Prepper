import time

import bpy
from bpy.types import Panel

_STATUS_ICONS = {
    "NONE": "QUESTION",
    "PASS": "CHECKMARK",
    "WARN": "ERROR",
    "FAIL": "CANCEL",
}


class SMP_PT_main_panel(Panel):
    bl_idname = "SMP_PT_main_panel"
    bl_label = "Sollumz Model Prepper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Prepper"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Sollumz Model Prepper", icon="TOOL_SETTINGS")
        layout.separator()

        smp = getattr(scene, "smp", None)
        if smp is None:
            layout.label(text="Properties not registered.", icon="ERROR")
            return

        # check_status
        icon = _STATUS_ICONS.get(smp.check_status, "QUESTION")
        layout.label(text=f"Status: {smp.check_status}", icon=icon)

        # checked_object_count
        layout.label(text=f"Checked Objects: {smp.checked_object_count}")

        # last_check_time
        if smp.last_check_time > 0.0:
            ts = time.strftime("%H:%M:%S", time.localtime(smp.last_check_time))
            layout.label(text=f"Last Check: {ts}")
        else:
            layout.label(text="Last Check: Never")

        # check_results count
        layout.label(text=f"Results: {len(smp.check_results)}")

        layout.separator()
        layout.label(text="MVP-0 / T-003 UI scaffold", icon="INFO")
