import time

import bpy
from bpy.types import Panel

_STATUS_ICONS = {
    "NONE": "QUESTION",
    "PASS": "CHECKMARK",
    "WARN": "ERROR",
    "FAIL": "CANCEL",
}

_SEVERITY_ICONS = {
    "OK": "CHECKMARK",
    "WARN": "ERROR",
    "ERROR": "CANCEL",
}

_MAX_RESULTS = 20


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

        layout.operator("smp.run_preflight", icon="CHECKMARK")

        layout.separator()

        icon = _STATUS_ICONS.get(smp.check_status, "QUESTION")
        layout.label(text=f"Status: {smp.check_status}", icon=icon)
        layout.label(text=f"Checked Objects: {smp.checked_object_count}")

        if smp.last_check_time > 0.0:
            ts = time.strftime("%H:%M:%S", time.localtime(smp.last_check_time))
            layout.label(text=f"Last Check: {ts}")
        else:
            layout.label(text="Last Check: Never")

        results = smp.check_results
        result_count = len(results)
        layout.label(text=f"Results: {result_count}")

        if result_count == 0:
            return

        layout.separator()
        box = layout.box()
        display_count = min(result_count, _MAX_RESULTS)
        for i in range(display_count):
            r = results[i]
            col = box.column(align=True)
            row = col.row()
            row.label(text=f"[{r.status}] {r.check_id}", icon=_SEVERITY_ICONS.get(r.status, "DOT"))
            row.label(text=r.fix_type)
            col.label(text=r.message)

        if result_count > _MAX_RESULTS:
            box.label(text=f"... and {result_count - _MAX_RESULTS} more result(s)")
