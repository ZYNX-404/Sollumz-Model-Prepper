"""
Material Check — T-009.

Inspects material slots and node-based image textures in read-only mode.
No material creation, no texture creation, no mesh modification.

Five sub-checks are performed:
  A. material_missing      — slot count == 0                   → ERROR / SAFE_MANUAL
  B. material_empty_slot   — slot.material is None             → WARN  / SAFE_MANUAL
  C. material_name         — assigned material has empty name  → WARN  / SAFE_MANUAL
  D. material_texture_missing — no TEX_IMAGE node with image   → WARN  / REVIEW_REQUIRED
  E. texture_non_power_of_two — image size not power-of-two    → WARN  / REVIEW_REQUIRED

If no material slots exist, only A is returned (B/C/D/E are skipped).
"""

from .result import CheckResult


def check_materials(obj) -> list[CheckResult]:
    """Return Material Check results for *obj*. Caller must pass a MESH object."""
    slots = obj.material_slots

    if len(slots) == 0:
        return [
            CheckResult(
                check_id="material_missing",
                check_name="Materials",
                status="ERROR",
                message="No material slots found.",
                fix_type="SAFE_MANUAL",
                detail_count=0,
            )
        ]

    results: list[CheckResult] = []

    # A. Material slot exists
    results.append(CheckResult(
        check_id="material_missing",
        check_name="Materials",
        status="OK",
        message=f"{len(slots)} material slot(s) found.",
        fix_type="NONE",
        detail_count=len(slots),
    ))

    # B. Empty material slots
    empty_count = sum(1 for s in slots if s.material is None)
    if empty_count:
        results.append(CheckResult(
            check_id="material_empty_slot",
            check_name="Empty Material Slots",
            status="WARN",
            message=f"{empty_count} empty material slot(s) found.",
            fix_type="SAFE_MANUAL",
            detail_count=empty_count,
        ))
    else:
        results.append(CheckResult(
            check_id="material_empty_slot",
            check_name="Empty Material Slots",
            status="OK",
            message="No empty material slots.",
            fix_type="NONE",
            detail_count=0,
        ))

    # Collect assigned materials (slot.material is not None) for C and D
    assigned = [s.material for s in slots if s.material is not None]

    # C. Material name check
    unnamed_count = sum(1 for m in assigned if not m.name.strip())
    if unnamed_count:
        results.append(CheckResult(
            check_id="material_name",
            check_name="Material Names",
            status="WARN",
            message=f"{unnamed_count} material(s) have empty names.",
            fix_type="SAFE_MANUAL",
            detail_count=unnamed_count,
        ))
    else:
        results.append(CheckResult(
            check_id="material_name",
            check_name="Material Names",
            status="OK",
            message="All assigned materials have names.",
            fix_type="NONE",
            detail_count=0,
        ))

    # D. Image texture detection
    no_texture_count = sum(1 for m in assigned if not _has_image_texture(m))
    if no_texture_count:
        results.append(CheckResult(
            check_id="material_texture_missing",
            check_name="Material Image Textures",
            status="WARN",
            message=(
                f"{no_texture_count} material(s) have no image texture detected. "
                "This may be intentional for procedural or custom materials "
                "— review manually."
            ),
            fix_type="REVIEW_REQUIRED",
            detail_count=no_texture_count,
        ))
    else:
        results.append(CheckResult(
            check_id="material_texture_missing",
            check_name="Material Image Textures",
            status="OK",
            message="Image textures detected on all assigned materials.",
            fix_type="NONE",
            detail_count=0,
        ))

    # E. Texture power-of-two check
    results.append(_check_texture_power_of_two(assigned))

    return results


def _is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def _collect_unique_images(materials) -> list:
    """
    Return unique Image datablocks used by TEX_IMAGE nodes in *materials*.

    Deduplicated by image.as_pointer() so the same Image used across
    multiple materials or nodes is counted once. Read-only.
    """
    images = {}
    for mat in materials:
        if mat is None or not mat.use_nodes:
            continue
        node_tree = getattr(mat, "node_tree", None)
        nodes = getattr(node_tree, "nodes", None) if node_tree is not None else None
        if nodes is None:
            continue
        for node in nodes:
            if getattr(node, "type", None) == "TEX_IMAGE":
                image = getattr(node, "image", None)
                if image is not None:
                    images[image.as_pointer()] = image
    return list(images.values())


def _check_texture_power_of_two(materials) -> CheckResult:
    # Images with no readable size (e.g. not loaded) are skipped here;
    # missing textures are material_texture_missing's responsibility.
    non_pot = []
    for image in _collect_unique_images(materials):
        width, height = image.size[0], image.size[1]
        if width > 0 and height > 0 and not (_is_power_of_two(width) and _is_power_of_two(height)):
            non_pot.append((image.name, width, height))

    count = len(non_pot)

    if count:
        name, width, height = non_pot[0]
        if count == 1:
            message = (
                f"Texture '{name}' is {width}x{height}. "
                "Power-of-two texture sizes are usually safer for game assets."
            )
        else:
            message = (
                f"{count} texture image(s) use non-power-of-two sizes, "
                f"e.g. '{name}' {width}x{height}. "
                "Power-of-two texture sizes are usually safer for game assets."
            )
        return CheckResult(
            check_id="texture_non_power_of_two",
            check_name="Non-Power-of-Two Texture",
            status="WARN",
            message=message,
            fix_type="REVIEW_REQUIRED",
            detail_count=count,
        )

    return CheckResult(
        check_id="texture_non_power_of_two",
        check_name="Texture Power-of-Two",
        status="OK",
        message="All checked texture images use power-of-two sizes.",
        fix_type="NONE",
        detail_count=0,
    )


def _has_image_texture(mat) -> bool:
    """Return True if *mat* has at least one TEX_IMAGE node with a loaded image."""
    if mat is None:
        return False
    if not mat.use_nodes:
        return False
    node_tree = getattr(mat, "node_tree", None)
    if node_tree is None:
        return False
    nodes = getattr(node_tree, "nodes", None)
    if nodes is None:
        return False
    for node in nodes:
        if getattr(node, "type", None) == "TEX_IMAGE" and getattr(node, "image", None) is not None:
            return True
    return False
