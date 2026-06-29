"""
Collection helper utilities.

Pure helpers that create or look up bpy.data.collections.
No Operators, Panels, or PropertyGroups live here.
"""

import bpy


def collection_exists(name: str) -> bool:
    """Return True if a Collection with *name* exists in bpy.data.collections."""
    return name in bpy.data.collections


def get_or_create_collection(name: str, parent=None):
    """
    Return the Collection named *name*, creating it if necessary.

    Args:
        name:   Name of the Collection to find or create.
        parent: Parent Collection to link the new Collection into.
                If None, links into the scene's master collection.

    The function is idempotent: calling it twice with the same arguments
    will not create duplicates or raise exceptions.

    Returns:
        The existing or newly created bpy.data.Collection.
    """
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        _link_to_parent(col, parent)
        return col

    # Collection already exists — ensure it is linked under the requested parent
    # without creating a duplicate link.
    _link_to_parent(col, parent, check_existing=True)
    return col


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _link_to_parent(col, parent, check_existing: bool = False):
    """
    Link *col* into *parent* (or the scene master collection when parent is
    None).  When *check_existing* is True, skip if the link already exists.

    RuntimeError handling:
      Blender raises RuntimeError when the collection is already a direct child
      of *parent*.  We verify this by checking the actual children list after
      the error.  If the collection is confirmed linked, the error is a benign
      duplicate-link attempt and is silently ignored.  If it is NOT linked,
      something else went wrong and the RuntimeError is re-raised so callers
      are not given a false sense of success.
    """
    parent_col = parent if parent is not None else bpy.context.scene.collection

    if check_existing and any(
        child.name == col.name for child in parent_col.children
    ):
        return  # already linked; nothing to do

    try:
        parent_col.children.link(col)
    except RuntimeError:
        # Re-check: is the collection actually present in parent_col.children?
        already_linked = any(
            child.name == col.name for child in parent_col.children
        )
        if not already_linked:
            raise  # unexpected error — do not hide it
