"""
Review Operators — selection helpers for manual mesh review.

These operators change selection state and edit mode only.
No mesh geometry, normals, UVs, or materials are modified.
"""

import bpy
from bpy.types import Operator

from ..checks.geometry_detection import (
    find_zero_area_face_indices,
    find_open_boundary_edge_indices,
    find_complex_non_manifold_edge_indices,
    find_loose_vertex_indices,
    find_loose_edge_indices,
    find_duplicate_vertex_indices,
)


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

        # Shared detection — same condition as Preflight's zero_area_face check
        zero_indices = find_zero_area_face_indices(mesh)
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

        # Shared detection — same condition as Preflight's open_boundary check
        boundary_indices = find_open_boundary_edge_indices(mesh)

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


class SMP_OT_SelectComplexNonManifoldEdges(Operator):
    bl_idname = "smp.select_complex_non_manifold_edges"
    bl_label = "Select Complex Non-Manifold Edges"
    bl_description = "Select edges connected to three or more faces on the active mesh object for manual review"
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

        # Shared detection — same condition as Preflight's complex_non_manifold check
        complex_indices = find_complex_non_manifold_edge_indices(mesh)

        for idx in complex_indices:
            mesh.edges[idx].select = True

        mesh.update()

        count = len(complex_indices)

        # Set Edge select mode and enter Edit Mode
        context.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.object.mode_set(mode='EDIT')

        if count:
            self.report({'INFO'}, f"{count} complex non-manifold edge(s) selected.")
        else:
            self.report({'INFO'}, "No complex non-manifold edges found.")

        return {'FINISHED'}


class SMP_OT_SelectLooseGeometry(Operator):
    bl_idname = "smp.select_loose_geometry"
    bl_label = "Select Loose Geometry"
    bl_description = "Select loose vertices and edges on the active mesh object"
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

        # Switch to Object Mode so mesh data is accessible
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all verts/edges/faces
        for v in mesh.vertices:
            v.select = False
        for e in mesh.edges:
            e.select = False
        for p in mesh.polygons:
            p.select = False

        # Shared detection — same conditions as Preflight's loose_geo check
        loose_vert_indices = find_loose_vertex_indices(mesh)
        loose_edge_indices = find_loose_edge_indices(mesh)

        for idx in loose_vert_indices:
            mesh.vertices[idx].select = True
        for idx in loose_edge_indices:
            mesh.edges[idx].select = True

        mesh.update()

        v_count = len(loose_vert_indices)
        e_count = len(loose_edge_indices)

        # Set Vertex+Edge select mode and enter Edit Mode
        context.tool_settings.mesh_select_mode = (True, True, False)
        bpy.ops.object.mode_set(mode='EDIT')

        if v_count or e_count:
            self.report({'INFO'}, f"Selected {v_count} loose vert(s) and {e_count} loose edge(s).")
        else:
            self.report({'INFO'}, "No loose geometry found.")

        return {'FINISHED'}


class SMP_OT_SelectDuplicateVertices(Operator):
    bl_idname = "smp.select_duplicate_vertices"
    bl_label = "Select Duplicate Vertices"
    bl_description = "Select duplicate vertex candidates on the active mesh object"
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

        # Switch to Object Mode so mesh data is accessible
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Deselect all verts/edges/faces
        for v in mesh.vertices:
            v.select = False
        for e in mesh.edges:
            e.select = False
        for p in mesh.polygons:
            p.select = False

        # Shared detection — same threshold as Preflight's dupe_vertex check.
        # Detection only: no merge / weld / remove doubles is performed.
        duplicate_indices = find_duplicate_vertex_indices(mesh)

        for idx in duplicate_indices:
            mesh.vertices[idx].select = True

        mesh.update()

        count = len(duplicate_indices)

        # Set Vertex select mode and enter Edit Mode
        context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.object.mode_set(mode='EDIT')

        if count:
            self.report({'INFO'}, f"Selected {count} duplicate vertex candidate(s).")
        else:
            self.report({'INFO'}, "No duplicate vertices found.")

        return {'FINISHED'}
