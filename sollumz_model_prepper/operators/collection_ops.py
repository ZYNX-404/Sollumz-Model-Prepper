"""
Collection creation operators.

T-003: MLO Collection hierarchy creation.
"""

import bpy
from bpy.types import Operator

from ..utils.collection_utils import get_or_create_collection, collection_exists

# Sub-collection suffixes created under the MLO parent.
_CHILD_SUFFIXES = ("_entities", "_collision", "_portals")


class SMP_OT_CreateMLOCollection(Operator):
    bl_idname = "smp.create_mlo_collection"
    bl_label = "Create MLO Collections"
    bl_description = (
        "Create the standard MLO Collection hierarchy "
        "(entities / collision / portals) under the given MLO name"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.scene is not None
            and getattr(context.scene, "smp", None) is not None
        )

    def execute(self, context):
        mlo_name = context.scene.smp.mlo_name.strip()

        if not mlo_name:
            self.report({'ERROR'}, "MLO Name is empty. Please enter a name.")
            return {'CANCELLED'}

        parent_name = f"MLO_{mlo_name}"
        already_existed = collection_exists(parent_name)

        # Create or retrieve the parent Collection.
        parent_col = get_or_create_collection(parent_name, parent=None)

        # Create or retrieve each child Collection under the parent.
        for suffix in _CHILD_SUFFIXES:
            get_or_create_collection(parent_name + suffix, parent=parent_col)

        if already_existed:
            self.report(
                {'INFO'},
                f"MLO Collections already exist for '{mlo_name}' — nothing changed.",
            )
        else:
            self.report(
                {'INFO'},
                f"Created MLO Collections: {parent_name} "
                f"(+ {', '.join(suffix.lstrip('_') for suffix in _CHILD_SUFFIXES)})",
            )

        return {'FINISHED'}
