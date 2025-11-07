"""
BlenderCivil UI Module

User interface panels and menus for BlenderCivil.
All UI classes will be organized here.
"""

import bpy
from .. import core

# Always import dependency panel (no IFC dependency)
from . import dependency_panel

# Import alignment properties (no IFC dependency for properties)
from . import alignment_properties

# Import georeferencing properties (no IFC dependency for properties)
from . import georef_properties

# Import vertical alignment properties (no IFC dependency for properties)
from . import vertical_properties

# Import cross section properties (no IFC dependency for properties)
from . import cross_section_properties

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
    from . import file_management_panel
    from . import alignment_panel
    from . import validation_panel
    from . import corridor_panel
    from . import panels

    _ui_modules.extend([
        file_management_panel,
        alignment_panel,
        validation_panel,
        corridor_panel,
        panels,
    ])


def register():
    """Register UI classes"""
    print("  [+] UI module loaded")

    # Register alignment properties FIRST (required by other modules)
    alignment_properties.register()

    # Register other property modules
    georef_properties.register()
    vertical_properties.register()
    cross_section_properties.register()

    # Register UI panel modules
    for module in _ui_modules:
        module.register()

    print(f"  [+] Registered {len(_ui_modules)} UI panel modules")


def unregister():
    """Unregister UI classes"""
    # Unregister UI panel modules
    for module in reversed(_ui_modules):
        module.unregister()

    # Unregister properties in reverse order
    cross_section_properties.unregister()
    vertical_properties.unregister()
    georef_properties.unregister()

    # Unregister alignment properties LAST (unregister first registered last)
    alignment_properties.unregister()
