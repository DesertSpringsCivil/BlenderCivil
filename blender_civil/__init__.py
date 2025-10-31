"""
BlenderCivil Native IFC Extension
Version 0.4.0

A native IFC-based civil engineering design tool for Blender.
Supports PI-driven horizontal alignments with professional workflows.
"""

# bl_info for legacy addon compatibility (Extensions ignore this)
bl_info = {
    "name": "BlenderCivil Native IFC",
    "author": "Desert Springs CE, Michael Yoder",
    "version": (0, 4, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BlenderCivil",
    "description": "Native IFC civil engineering design with PI-driven alignments",
    "category": "Object", }

import bpy
import sys
from pathlib import Path

# Track loaded modules for cleanup
_loaded_modules = []

def check_dependencies():
    """
    Check if all required dependencies are available.
    Returns: (bool, list) - (all_satisfied, missing_list)
    """
    missing = []
    
    # Check for IfcOpenShell
    try:
        import ifcopenshell
        # Check version if possible
        if hasattr(ifcopenshell, '__version__'):
            version = ifcopenshell.__version__
            print(f"   ✅ IfcOpenShell {version}")
        else:
            print(f"   ✅ IfcOpenShell (version unknown)")
    except ImportError:
        print(f"   ❌ IfcOpenShell - Not found")
        missing.append("ifcopenshell")
    
    return len(missing) == 0, missing


def load_modules_with_dependencies():
    """
    Load all addon modules. Returns True if successful.
    Handles dependency issues gracefully.
    """
    global _loaded_modules
    
    try:
        # Import core modules
        from . import core
        _loaded_modules.append(core)
        print("  ✅ Core modules")
        
        # Import operators
        from . import operators  
        _loaded_modules.append(operators)
        print("  ✅ Operators")
        
        # Import UI modules
        from . import ui
        _loaded_modules.append(ui)
        print("  ✅ UI modules")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading modules: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_dependency_ui_only():
    """
    Load only the dependency management UI when dependencies are missing.
    This allows users to install missing dependencies from within Blender.
    """
    global _loaded_modules
    
    try:
        # Only import the dependency panel
        from .ui import dependency_panel
        _loaded_modules.append(dependency_panel)
        print("  ✅ Dependency UI (limited mode)")
        return True
    except Exception as e:
        print(f"  ❌ Error loading dependency UI: {e}")
        import traceback
        traceback.print_exc()
        return False


def register():
    """
    Register the addon. Checks dependencies and loads modules accordingly.
    """
    # Get version from bl_info
    version_str = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
    
    print("\n" + "=" * 60)
    print(f"BlenderCivil v{version_str} - Initializing...")
    print("=" * 60)
    
    # Check dependencies
    print("\n🔍 Checking dependencies...")
    deps_ok, missing = check_dependencies()
    
    if deps_ok:
        # All dependencies available - load full addon
        print("\n📦 Loading addon modules...")
        if load_modules_with_dependencies():
            # Register all modules
            for module in _loaded_modules:
                if hasattr(module, 'register'):
                    module.register()
            
            print("\n✅ BlenderCivil loaded successfully!")
            print("📍 Location: 3D Viewport > Sidebar (N) > BlenderCivil tab")
            print("\n" + "=" * 60)
            print("🎯 Ready to design! Create your first native IFC alignment.")
            print("=" * 60 + "\n")
        else:
            print("\n⚠️  Module loading failed - check console for errors")
            print("=" * 60 + "\n")
    
    else:
        # Missing dependencies - load only dependency UI
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("\n📦 Loading dependency management UI...")
        
        if load_dependency_ui_only():
            # Register dependency UI
            for module in _loaded_modules:
                if hasattr(module, 'register'):
                    module.register()
            
            print("\n⚠️  BlenderCivil loaded in LIMITED mode")
            print("📍 Location: 3D Viewport > Sidebar (N) > BlenderCivil tab")
            print("💡 Use the 'Install Dependencies' button to install required packages")
            print("=" * 60 + "\n")
        else:
            print("\n❌ Failed to load dependency UI")
            print("=" * 60 + "\n")


def unregister():
    """
    Unregister the addon and clean up all modules.
    """
    global _loaded_modules
    
    print("\n" + "=" * 60)
    print("BlenderCivil - Unregistering...")
    print("=" * 60)
    
    # Unregister in reverse order
    for module in reversed(_loaded_modules):
        if hasattr(module, 'unregister'):
            try:
                module.unregister()
                print(f"  ✅ Unregistered: {module.__name__}")
            except Exception as e:
                print(f"  ⚠️  Error unregistering {module.__name__}: {e}")
    
    # Clear the module list
    _loaded_modules.clear()
    
    print("\n✅ BlenderCivil unregistered successfully")
    print("=" * 60 + "\n")


# This allows running the script directly for testing
if __name__ == "__main__":
    register()
