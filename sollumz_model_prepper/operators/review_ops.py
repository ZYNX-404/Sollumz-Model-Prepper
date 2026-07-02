"""
Review Operators — selection helpers for manual mesh review.

These operators change selection state and edit mode only.
No mesh geometry, normals, UVs, or materials are modified.
"""

import bmesh
import bpy
from bpy.types import Operator

# Kept in sync with checks/geometry_check.py ZERO_AREA_THRESHOLD
ZERO_AREA_THRESHOLD = 1e-8


class SMP_OT_SelectZeroAreaFaces(Operator):
    bl_idname = "smp.select_zero_area_faces"
    bl_label = "Select Zero Area Faces"
    bl_description = "Select zero-area faces on the active mesh object for manual review"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'MESH' and obj.data is not None

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH' or obj.data is None:
            self.report({'WARNING'}, "No active mesh object.")
            return {'CANCELLED'}

        mesh = obj.data

        # Switch to Object Mode so mesh.polygons reflects current data
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all faces
        for poly in mesh.polygons:
            poly.select = False

        # Select zero-area faces (threshold matches geometry_check.py)
        zero_indices = [poly.index for poly in mesh.polygons if poly.area < ZERO_AREA_THRESHOLD]
        for idx in zero_indices:
            mesh.polygons[idx].select = True

        mesh.update()

        count = len(zero_indices)

        # Set face select mode before entering Edit Mode
        context.tool_settings.mesh_select_mode = (False, False, True)

        # Enter Edit Mode so the user can see the selection
        bpy.ops.object.mode_set(mode='EDIT')

        if count:
            self.report({'INFO'}, f"{count} zero-area face(s) selected.")
        else:
            self.report({'INFO'}, "No zero-area faces found.")

        return {'FINISHED'}


class SMP_OT_SelectOpenBoundaryEdges(Operator):
    bl_idname = "smp.select_open_boundary_edges"
    bl_label = "Select Open Boundary Edges"
    bl_description = "Select open boundary edges on the active mesh object for manual review"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == 'MESH' and obj.data is not None

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH' or obj.data is None:
            self.report({'WARNING'}, "No active mesh object.")
            return {'CANCELLED'}

        mesh = obj.data

        # Switch to Object Mode so mesh edge data is accessible
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all verts/edges/faces
        for v in mesh.vertices:
            v.select = False
        for e in mesh.edges:
            e.select = False
        for p in mesh.polygons:
            p.select = False

        # Detect open boundary edges via bmesh (link_faces == 1)
        # Condition kept in sync with geometry_check.py open_boundary judgement
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            bm.edges.ensure_lookup_table()
            boundary_indices = [e.index for e in bm.edges if len(e.link_faces) == 1]
        finally:
            bm.free()

        # Apply selection to mesh edges (bmesh is freed; no bm.to_mesh() call)
        for idx in boundary_indices:
            mesh.edges[idx].select = True

        mesh.update()

        count = len(boundary_indices)

        # Set Edge select mode and enter Edit Mode
        context.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.object.mode_set(mode='EDIT')

        if count:
            self.report({'INFO'}, f"{count} open boundary edge(s) selected.")
        else:
            self.report({'INFO'}, "No open boundary edges found.")

        return {'FINISHED'}
