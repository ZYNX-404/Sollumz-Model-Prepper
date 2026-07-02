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

        layout.prop(smp, "vertex_count_warn_threshold")
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

        error_count = sum(1 for r in results if r.status == "ERROR")
        warn_count  = sum(1 for r in results if r.status == "WARN")
        ok_count    = result_count - error_count - warn_count

        layout.label(text=f"Results: {result_count}")
        row = layout.row()
        row.label(text=f"Errors: {error_count}", icon="CANCEL")
        row.label(text=f"Warnings: {warn_count}", icon="ERROR")
        row.label(text=f"OK: {ok_count}", icon="CHECKMARK")

        if result_count > 0:
            layout.separator()
            layout.prop(smp, "show_ok_results")

            visible = list(results) if smp.show_ok_results else [r for r in results if r.status != "OK"]
            visible_count = len(visible)

            if visible_count == 0:
                layout.label(text="All results are OK.", icon="CHECKMARK")
            else:
                box = layout.box()
                for r in visible[:_MAX_RESULTS]:
                    check_name = r.check_name or r.check_id
                    detail_count = r.detail_count
                    object_name = r.object_name

                    col = box.column(align=True)
                    row = col.row()
                    row.label(text=f"[{r.status}] {check_name}", icon=_SEVERITY_ICONS.get(r.status, "DOT"))
                    if detail_count >= 1:
                        row.label(text=f"{r.fix_type} x{detail_count}")
                    else:
                        row.label(text=r.fix_type)
                    if object_name:
                        op = row.operator(
                            "smp.select_result_object",
                            text="",
                            icon="RESTRICT_SELECT_OFF",
                        )
                        op.object_name = object_name
                        col.label(text=f"[{object_name}] {r.message}")
                    else:
                        col.label(text=r.message)

                if visible_count > _MAX_RESULTS:
                    box.label(text=f"... and {visible_count - _MAX_RESULTS} more result(s)")

        layout.separator()
        review_box = layout.box()
        review_box.label(text="Review Tools", icon="VIEWZOOM")
        review_box.operator("smp.select_zero_area_faces", text="Select Zero Area Faces")
        review_box.operator("smp.select_open_boundary_edges", text="Select Open Boundary Edges")
        review_box.operator("smp.select_complex_non_manifold_edges", text="Select Complex Non-Manifold Edges")
        review_box.operator("smp.select_loose_geometry", text="Select Loose Geometry")
        review_box.operator("smp.select_duplicate_vertices", text="Select Duplicate Vertices")
        review_box.operator("smp.select_uv_out_of_bounds_faces", text="Select UV Out-of-Bounds Faces")
