"""
BlenderCivil Extension
Version 0.5.0

A fresh start for native IFC civil engineering design in Blender.
"""

import bpy

# Reload support for development
def _reload_modules():
    """Reload all submodules in the correct order"""
    import sys
    import importlib
    
    # List of submodules in dependency order
    module_names = [
        "core",
        "operators",
        "ui",
    ]
    
    # Reload each module if it's already loaded
    for name in module_names:
        full_name = f"{__package__}.{name}"
        if full_name in sys.modules:
            importlib.reload(sys.modules[full_name])

# Attempt reload if extension is being reloaded
if "bpy" in locals():
    _reload_modules()

# Import submodules after reload
from . import core
from . import operators
from . import ui


def register():
    """Register extension modules and classes"""
    print("\n" + "="*60)
    print("BlenderCivil Extension v0.5.0 - Loading...")
    print("="*60)

    # Register modules in order
    print("\n[*] Loading modules:")
    core.register()
    ui.register()         # Register UI properties FIRST (operators depend on them)
    operators.register()  # Then operators can use the properties

    # Register update system for real-time PI movement
    from .core import complete_update_system
    complete_update_system.register()

    print("\n[+] BlenderCivil Extension loaded successfully!")
    print("[i] Location: 3D Viewport > Sidebar (N) > BlenderCivil tab")
    print("="*60 + "\n")


def unregister():
    """Unregister extension modules and classes"""
    print("BlenderCivil Extension - Unregistering...")

    # Unregister update system first
    from .core import complete_update_system
    complete_update_system.unregister()

    # Unregister modules in reverse order
    operators.unregister()  # Unregister operators first (they use properties)
    ui.unregister()         # Then UI properties
    core.unregister()

    print("[+] BlenderCivil Extension unregistered")


if __name__ == "__main__":
    register()
