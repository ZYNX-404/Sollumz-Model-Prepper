bl_info = {
    "name": "Sollumz Model Prepper",
    "author": "ZYNX-404",
    "version": (0, 1, 1),
    "blender": (5, 1, 2),
    "category": "Object",
    "description": "Prepare models for Sollumz (GTA V / FiveM) export",
}

from . import preferences
from . import properties
from . import operators
from . import ui


def register():
    preferences.register()
    properties.register()
    operators.register()
    ui.register()
    print("[SMP] Sollumz Model Prepper registered.")


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
    preferences.unregister()
    print("[SMP] Sollumz Model Prepper unregistered.")
