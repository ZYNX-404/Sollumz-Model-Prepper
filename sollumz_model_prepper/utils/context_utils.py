"""
Blender context helpers — stubs for future Fix operator use.

All managers here are safe to import even before any Fix operator exists.
bpy.ops.mesh.* is intentionally NOT called anywhere in this file (T-004 scope).
Actual mesh-edit usage is added in Post-MVP Fix operator tasks (T-013 onward).
"""

from contextlib import contextmanager

import bpy


# ---------------------------------------------------------------------------
# preserve_active_object
# ---------------------------------------------------------------------------

@contextmanager
def preserve_active_object(context):
    """
    Context manager: restores context.view_layer.objects.active after the
    block exits, even if an exception is raised.

    Usage::

        with preserve_active_object(context):
            context.view_layer.objects.active = some_obj
            ...
        # original active is restored here
    """
    prev_active = context.view_layer.objects.active
    try:
        yield
    finally:
        try:
            context.view_layer.objects.active = prev_active
        except Exception:
            pass  # prev_active may have been deleted; silently skip


# ---------------------------------------------------------------------------
# preserve_selection
# ---------------------------------------------------------------------------

@contextmanager
def preserve_selection(context):
    """
    Context manager: saves and restores the selection state of all objects in
    the current view layer.

    Only the select state is captured; active object is NOT touched here.
    Use together with preserve_active_object when both are needed.

    Usage::

        with preserve_selection(context):
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            ...
        # original selection is restored here
    """
    saved = {obj: obj.select_get() for obj in context.view_layer.objects}
    try:
        yield
    finally:
        for obj, was_selected in saved.items():
            try:
                obj.select_set(was_selected)
            except ReferenceError:
                pass  # object was deleted during the block; skip gracefully


# ---------------------------------------------------------------------------
# mesh_edit_context
# ---------------------------------------------------------------------------

@contextmanager
def mesh_edit_context(context, obj):
    """
    Context manager: validates *obj*, switches it to Edit Mode, yields,
    then restores the previous mode, active object, and selection.

    Designed for Post-MVP Fix operators (T-013 onward) that must call
    bpy.ops.mesh.* .  The body of this manager intentionally contains no
    mesh operations — callers are responsible for the actual edits.
    bpy.ops.mesh.* is NOT called inside this file (T-004 scope).

    Invariants guaranteed by this manager:
      - context.view_layer.objects.active is restored on exit.
      - All object select states are restored on exit.
      - Original mode is always restored: OBJECT→OBJECT, EDIT→EDIT,
        SCULPT→SCULPT, etc.  (Blender is never left stranded in Edit Mode.)
      - mode_set(prev_mode) is always called while *obj* is still active,
        so the mode is restored on the correct object even when prev_active
        differs from *obj*.

    TODO (Post-MVP / T-013):
      - Expose a ``select_only`` parameter to deselect all other objects first,
        which is required by some bpy.ops.mesh.* operators.

    Raises:
        ValueError: if *obj* fails any pre-flight validation check.

    Usage (future Fix operator)::

        with mesh_edit_context(context, obj):
            bpy.ops.mesh.normals_make_consistent(inside=False)
    """
    # ------------------------------------------------------------------
    # Pre-entry validation — raise before touching any Blender state.
    # ------------------------------------------------------------------
    if obj is None:
        raise ValueError("mesh_edit_context: obj is None")
    if obj.type != 'MESH':
        raise ValueError(
            f"mesh_edit_context: '{obj.name}' is not a MESH (type={obj.type})"
        )
    if obj.name not in context.view_layer.objects:
        raise ValueError(
            f"mesh_edit_context: '{obj.name}' is not in the current view layer"
        )
    if not obj.visible_get():
        raise ValueError(
            f"mesh_edit_context: '{obj.name}' is not visible in the viewport"
        )
    if obj.hide_get():
        raise ValueError(
            f"mesh_edit_context: '{obj.name}' is hidden (hide_get() is True)"
        )
    if obj.hide_select:
        raise ValueError(
            f"mesh_edit_context: '{obj.name}' is not selectable (hide_select is True)"
        )

    # ------------------------------------------------------------------
    # Save state before making any changes.
    # ------------------------------------------------------------------
    prev_active = context.view_layer.objects.active
    prev_mode = obj.mode  # mode of the object we are about to edit
    saved_selection = {o: o.select_get() for o in context.view_layer.objects}

    try:
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        yield
    finally:
        # Step 1: return to OBJECT mode.
        # obj is still active at this point (set in the try block above).
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        # Step 2: re-assert obj as active and ensure it is selected.
        # mode_set() targets the active object, so obj must be active when
        # prev_mode is restored.  If prev_active != obj and we restored
        # prev_active first, mode_set(prev_mode) would land on the wrong object.
        try:
            context.view_layer.objects.active = obj
            obj.select_set(True)
        except Exception:
            pass

        # Step 3: restore original mode on obj while obj is still active.
        # prev_mode != 'OBJECT' covers EDIT, SCULPT, POSE, etc.
        if prev_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass

        # Step 4: restore the previously active object.
        try:
            context.view_layer.objects.active = prev_active
        except Exception:
            pass

        # Step 5: restore per-object selection state.
        # Runs after Step 2's select_set(True), so obj's original selection
        # state is correctly overwritten if it was not selected before.
        for o, was_selected in saved_selection.items():
            try:
                o.select_set(was_selected)
            except ReferenceError:
                pass  # object was deleted during the block; skip gracefully
