import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import PropertyGroup


class SMPMaterialAnalysisResult(PropertyGroup):
    material_name: StringProperty(name="Material Name", default="")
    object_name: StringProperty(name="Object Name", default="")
    category: EnumProperty(
        name="Category",
        items=[
            ("NORMAL_SPEC", "NORMAL_SPEC Candidate", "Likely opaque material suitable for NORMAL_SPEC-style setup"),
            ("ALPHA", "Alpha Candidate", "Likely transparent or blended material"),
            ("CUTOUT", "Cutout Candidate", "Likely alpha clip/cutout material"),
            ("MISSING_TEXTURE", "Missing Texture", "Material has no usable image texture"),
            ("MANUAL_REVIEW", "Manual Review", "Material needs manual inspection"),
        ],
        default="MANUAL_REVIEW",
    )
    confidence: EnumProperty(
        name="Confidence",
        items=[
            ("HIGH", "High", "Strong heuristic match"),
            ("MEDIUM", "Medium", "Likely match"),
            ("LOW", "Low", "Weak or ambiguous match"),
        ],
        default="LOW",
    )
    suggested_shader: StringProperty(name="Suggested Sollumz Shader", default="")
    reason: StringProperty(name="Reason", default="")
    image_count: IntProperty(name="Image Count", default=0, min=0)
    texture_names: StringProperty(name="Texture Names", default="")
    has_alpha: BoolProperty(name="Has Alpha", default=False)
    blend_method: StringProperty(name="Blend Method", default="")
    needs_review: BoolProperty(name="Needs Review", default=True)
