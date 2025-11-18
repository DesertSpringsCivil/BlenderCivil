# ==============================================================================
# BlenderCivil - Civil Engineering Tools for Blender
# Copyright (c) 2024-2025 Michael Yoder / Desert Springs Civil Engineering PLLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Primary Author: Michael Yoder
# Company: Desert Springs Civil Engineering PLLC
# ==============================================================================

"""
BlenderCivil Core Module

Core functionality and data structures for BlenderCivil.
This will contain IFC utilities, geometry helpers, and core algorithms.
"""

import bpy

# Always import dependency_manager (no ifcopenshell dependency)
from . import dependency_manager

# Conditionally import IFC-dependent modules
_ifc_modules_loaded = False
_ifc_modules = []

try:
    import ifcopenshell

    # Import IFC-dependent modules
    from . import native_ifc_manager
    from . import ifc_relationship_manager
    from . import native_ifc_alignment
    from . import native_ifc_vertical_alignment
    from . import native_ifc_cross_section
    from . import alignment_3d
    from . import alignment_visualizer
    from . import alignment_registry
    from . import complete_update_system
    from . import ifc_geometry_builders
    from . import corridor_mesh_generator
    from . import profile_view_data
    from . import profile_view_renderer
    from . import profile_view_overlay

    _ifc_modules = [
        native_ifc_manager,
        ifc_relationship_manager,
        native_ifc_alignment,
        native_ifc_vertical_alignment,
        native_ifc_cross_section,
        alignment_3d,
        alignment_visualizer,
        alignment_registry,
        complete_update_system,
        ifc_geometry_builders,
        corridor_mesh_generator,
        profile_view_data,
        profile_view_renderer,
        profile_view_overlay,
    ]
    _ifc_modules_loaded = True

except ImportError as e:
    print(f"  [!] IFC modules not available: {e}")
    print(f"  [i] Install ifcopenshell to enable IFC features")


def register():
    """Register core module"""
    print("  [+] Core module loaded")

    if _ifc_modules_loaded:
        print("  [+] IFC features enabled")
    else:
        print("  [!] IFC features disabled (ifcopenshell not found)")


def unregister():
    """Unregister core module"""
    pass


def has_ifc_support():
    """Check if IFC support is available"""
    return _ifc_modules_loaded
