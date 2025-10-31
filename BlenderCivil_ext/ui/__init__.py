"""
BlenderCivil UI Module

User interface panels and menus for BlenderCivil.
All UI classes will be organized here.
"""

import bpy
from .. import core

# Always import dependency panel (no IFC dependency)
from . import dependency_panel

# List of UI modules
_ui_modules = [dependency_panel]

# Conditionally import IFC-dependent UI modules
if core.has_ifc_support():
    # Import core classes needed by UI panels
    from ..core.native_ifc_manager import NativeIfcManager

    # Make them available to UI modules
    import sys
    current_module = sys.modules[__name__]
    current_module.NativeIfcManager = NativeIfcManager

    # Import UI panel modules
    from . import alignment_panel
    from . import validation_panel

    _ui_modules.extend([
        alignment_panel,
        validation_panel,
    ])


def register():
    """Register UI classes"""
    print("  [+] UI module loaded")

    # Register UI panel modules
    for module in _ui_modules:
        module.register()

    print(f"  [+] Registered {len(_ui_modules)} UI panel modules")


def unregister():
    """Unregister UI classes"""
    # Unregister UI panel modules
    for module in reversed(_ui_modules):
        module.unregister()
