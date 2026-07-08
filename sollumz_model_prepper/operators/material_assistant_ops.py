import bpy
from bpy.props import EnumProperty, StringProperty
from datetime import datetime


_CATEGORY_ITEMS = [
    ("NORMAL_SPEC", "NORMAL_SPEC Candidate", ""),
    ("ALPHA", "Alpha Candidate", ""),
    ("CUTOUT", "Cutout Candidate", ""),
    ("MISSING_TEXTURE", "Missing Texture", ""),
    ("MANUAL_REVIEW", "Manual Review", ""),
]


def _ensure_object_mode(context):
    """Switch to Object Mode if not already. Returns False on failure."""
    if context.active_object is not None and context.active_object.mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            return False
    return True


def _select_objects(context, objects):
    """Deselect all, select given objects, set first as active."""
    for obj in context.view_layer.objects:
        obj.select_set(False)
    for obj in objects:
        obj.select_set(True)
    if objects:
        context.view_layer.objects.active = objects[0]


_CUTOUT_KEYWORDS = {"cutout", "alpha_clip", "fence", "grate", "leaf", "decal"}
_ALPHA_KEYWORDS = {"alpha", "glass", "window", "transparent"}


def _collect_image_textures(material):
    """Return (image_count, texture_names_csv, has_alpha) for a material."""
    if not material.use_nodes or material.node_tree is None:
        return 0, "", False

    images = []
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            images.append(node.image)

    image_count = len(images)
    texture_names = ", ".join(img.name for img in images)
    # truncate to avoid extremely long strings
    if len(texture_names) > 200:
        texture_names = texture_names[:197] + "..."

    has_alpha = any(img.depth in {32, 128} for img in images)

    return image_count, texture_names, has_alpha


def _keywords_match(text, keywords):
    lower = (text or "").lower()
    return any(kw in lower for kw in keywords)


def _classify_material(material, image_count, texture_names, has_alpha):
    """Return (category, confidence, suggested_shader, reason, needs_review)."""
    mat_name = material.name or ""
    blend_method = getattr(material, "blend_method", "") or ""

    # --- A: MISSING_TEXTURE ---
    if image_count == 0:
        return (
            "MISSING_TEXTURE",
            "HIGH",
            "",
            "No image texture found. Assign or review textures before Sollumz conversion.",
            True,
        )

    # --- B: CUTOUT ---
    is_clip_method = blend_method == "CLIP"
    is_cutout_name = _keywords_match(mat_name, _CUTOUT_KEYWORDS) or _keywords_match(texture_names, _CUTOUT_KEYWORDS)
    if is_clip_method or is_cutout_name:
        confidence = "HIGH" if is_clip_method else "MEDIUM"
        return (
            "CUTOUT",
            confidence,
            "NORMAL_SPEC_CUTOUT",
            "Blend method or texture name suggests alpha cutout.",
            True,
        )

    # --- C: ALPHA ---
    is_blend_method = blend_method in {"BLEND", "HASHED"}
    diffuse_alpha = getattr(material, "diffuse_color", None)
    is_diffuse_alpha = (diffuse_alpha is not None and len(diffuse_alpha) >= 4 and diffuse_alpha[3] < 1.0)
    is_alpha_name = _keywords_match(mat_name, _ALPHA_KEYWORDS) or _keywords_match(texture_names, _ALPHA_KEYWORDS)
    if is_blend_method or is_diffuse_alpha or has_alpha or is_alpha_name:
        return (
            "ALPHA",
            "MEDIUM",
            "NORMAL_SPEC_ALPHA",
            "Material appears to use transparency.",
            True,
        )

    # --- D: NORMAL_SPEC ---
    if blend_method in {"OPAQUE", ""} or blend_method not in {"BLEND", "HASHED", "CLIP"}:
        return (
            "NORMAL_SPEC",
            "MEDIUM",
            "NORMAL_SPEC",
            "Opaque material with image texture.",
            False,
        )

    # --- E: MANUAL_REVIEW ---
    return (
        "MANUAL_REVIEW",
        "LOW",
        "",
        "Material setup is ambiguous. Review manually.",
        True,
    )


class SMP_OT_AnalyzeMaterials(bpy.types.Operator):
    bl_idname = "smp.analyze_materials"
    bl_label = "Analyze Materials"
    bl_description = "Analyze selected mesh materials and suggest safe Sollumz material conversion groups"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.scene is None:
            return False
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        scene = context.scene
        scene_props = getattr(scene, "smp", None)
        if scene_props is None:
            self.report({'WARNING'}, "Sollumz Model Prepper properties are not registered.")
            return {'CANCELLED'}

        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}

        # Collect unique materials (deduplicate by datablock pointer)
        seen = {}  # pointer -> (material, object_name)
        for obj in mesh_objects:
            for slot in obj.material_slots:
                mat = slot.material
                if mat is None:
                    continue
                ptr = mat.as_pointer()
                if ptr not in seen:
                    seen[ptr] = (mat, obj.name)

        scene_props.material_analysis_results.clear()

        for mat, obj_name in seen.values():
            image_count, texture_names, has_alpha = _collect_image_textures(mat)
            blend_method = getattr(mat, "blend_method", "") or ""
            category, confidence, suggested_shader, reason, needs_review = _classify_material(
                mat, image_count, texture_names, has_alpha
            )

            entry = scene_props.material_analysis_results.add()
            entry.material_name = mat.name
            entry.object_name = obj_name
            entry.category = category
            entry.confidence = confidence
            entry.suggested_shader = suggested_shader
            entry.reason = reason
            entry.image_count = image_count
            entry.texture_names = texture_names
            entry.has_alpha = has_alpha
            entry.blend_method = blend_method
            entry.needs_review = needs_review

        count = len(scene_props.material_analysis_results)
        scene_props.material_analysis_material_count = count
        scene_props.material_analysis_last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if count == 0:
            self.report({'WARNING'}, "No materials found on selected mesh objects.")
            return {'FINISHED'}

        self.report({'INFO'}, f"Analyzed {count} material(s).")
        return {'FINISHED'}


class SMP_OT_SelectMaterialCategoryObjects(bpy.types.Operator):
    bl_idname = "smp.select_material_category_objects"
    bl_label = "Select Material Category Objects"
    bl_description = "Select objects using materials from the selected Material Assistant category"
    bl_options = {'REGISTER', 'UNDO'}

    category: EnumProperty(name="Category", items=_CATEGORY_ITEMS, default="MANUAL_REVIEW")

    @classmethod
    def poll(cls, context):
        if context.scene is None:
            return False
        smp = getattr(context.scene, "smp", None)
        return smp is not None and len(smp.material_analysis_results) > 0

    def execute(self, context):
        if not _ensure_object_mode(context):
            self.report({'WARNING'}, "Could not switch to Object Mode.")
            return {'CANCELLED'}

        smp = getattr(context.scene, "smp", None)
        if smp is None:
            self.report({'WARNING'}, "Sollumz Model Prepper properties are not registered.")
            return {'CANCELLED'}

        target_names = {
            r.material_name
            for r in smp.material_analysis_results
            if r.category == self.category
        }
        if not target_names:
            self.report({'INFO'}, f"No materials in category: {self.category}")
            return {'FINISHED'}

        found = []
        skipped = 0
        for obj in context.view_layer.objects:
            if obj.type != 'MESH':
                continue
            if obj.hide_get() or obj.hide_select:
                skipped += 1
                continue
            slot_names = {slot.material.name for slot in obj.material_slots if slot.material is not None}
            if slot_names & target_names:
                found.append(obj)

        _select_objects(context, found)
        skip_msg = f" ({skipped} hidden/locked skipped)" if skipped else ""
        if found:
            self.report({'INFO'}, f"Selected {len(found)} object(s) for {self.category}.{skip_msg}")
        else:
            self.report({'INFO'}, f"No visible selectable objects found for category: {self.category}.{skip_msg}")
        return {'FINISHED'}


class SMP_OT_SelectMaterialUsers(bpy.types.Operator):
    bl_idname = "smp.select_material_users"
    bl_label = "Select Material Users"
    bl_description = "Select objects using this material"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty(name="Material Name", default="")

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        if not self.material_name:
            self.report({'WARNING'}, "No material name specified.")
            return {'CANCELLED'}

        if not _ensure_object_mode(context):
            self.report({'WARNING'}, "Could not switch to Object Mode.")
            return {'CANCELLED'}

        mat = bpy.data.materials.get(self.material_name)
        if mat is None:
            self.report({'WARNING'}, f"Material not found: {self.material_name}")
            return {'CANCELLED'}

        found = []
        skipped = 0
        for obj in context.view_layer.objects:
            if obj.type != 'MESH':
                continue
            if obj.hide_get() or obj.hide_select:
                skipped += 1
                continue
            if any(slot.material == mat for slot in obj.material_slots):
                found.append(obj)

        _select_objects(context, found)
        skip_msg = f" ({skipped} hidden/locked skipped)" if skipped else ""
        if found:
            self.report({'INFO'}, f"Selected {len(found)} object(s) using material: {self.material_name}.{skip_msg}")
        else:
            self.report({'INFO'}, f"No visible selectable objects found for material: {self.material_name}.{skip_msg}")
        return {'FINISHED'}
