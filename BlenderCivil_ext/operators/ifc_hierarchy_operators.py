"""
BlenderCivil - IFC File Operators with Hierarchy Visualization
Operators for creating, opening, and saving IFC files with visual hierarchy
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

# Import the NativeIfcManager from the core module
from ..core.native_ifc_manager import NativeIfcManager


class BC_OT_new_ifc(Operator):
    """Create new IFC file with complete spatial hierarchy"""
    bl_idname = "bc.new_ifc"
    bl_label = "Create New IFC"
    bl_description = "Create new IFC4X3 file with Project → Site → Road hierarchy"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """
        Create new IFC file and visualize hierarchy in Blender outliner.
        
        Creates:
        - IFC spatial structure: IfcProject → IfcSite → IfcRoad
        - Blender visualization with Empty objects
        - Collections for Alignments and Geomodels
        """
        
        try:
            # Create new IFC file with full hierarchy
            result = NativeIfcManager.new_file()
            
            # Report success
            self.report({'INFO'}, 
                f"Created IFC file: {result['project'].Name} "
                f"({result['ifc_file'].schema})")
            
            # Show info in console
            print("\n" + "="*60)
            print("✅ IFC SPATIAL HIERARCHY CREATED")
            print("="*60)
            print(f"Schema: {result['ifc_file'].schema}")
            print(f"Entities: {len(result['ifc_file'])}")
            print(f"\nProject: {result['project'].Name}")
            print(f"Site: {result['site'].Name}")
            print(f"Road: {result['road'].Name}")
            print("\n📂 Check Blender outliner for visual hierarchy")
            print("="*60 + "\n")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create IFC file: {str(e)}")
            print(f"❌ Error creating IFC: {str(e)}")
            return {'CANCELLED'}


class BC_OT_open_ifc(Operator, ImportHelper):
    """Open existing IFC file and visualize hierarchy"""
    bl_idname = "bc.open_ifc"
    bl_label = "Open IFC File"
    bl_description = "Open existing IFC file and create Blender visualization"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".ifc"
    filter_glob: StringProperty(
        default="*.ifc",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        """
        Load IFC file and create Blender visualization.
        """
        
        try:
            # Load IFC file
            ifc_file = NativeIfcManager.open_file(self.filepath)
            
            # Get info
            info = NativeIfcManager.get_info()
            
            # Report success
            self.report({'INFO'}, 
                f"Loaded: {info['project']} ({info['entities']} entities)")
            
            # Show info in console
            print("\n" + "="*60)
            print("✅ IFC FILE LOADED")
            print("="*60)
            print(f"File: {self.filepath}")
            print(f"Schema: {info['schema']}")
            print(f"Entities: {info['entities']}")
            print(f"Alignments: {info['alignments']}")
            print(f"Geomodels: {info['geomodels']}")
            print("\n📂 Check Blender outliner for visual hierarchy")
            print("="*60 + "\n")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open IFC file: {str(e)}")
            print(f"❌ Error opening IFC: {str(e)}")
            return {'CANCELLED'}


class BC_OT_save_ifc(Operator, ExportHelper):
    """Save IFC file to disk"""
    bl_idname = "bc.save_ifc"
    bl_label = "Save IFC File"
    bl_description = "Save current IFC file to disk"
    bl_options = {'REGISTER'}
    
    filename_ext = ".ifc"
    filter_glob: StringProperty(
        default="*.ifc",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        """
        Save IFC file to selected location.
        """
        
        try:
            # Check if file exists
            if NativeIfcManager.file is None:
                self.report({'ERROR'}, "No IFC file to save")
                return {'CANCELLED'}
            
            # Save file
            NativeIfcManager.save_file(self.filepath)
            
            # Get info
            info = NativeIfcManager.get_info()
            
            # Report success
            self.report({'INFO'}, 
                f"Saved: {self.filepath} ({info['entities']} entities)")
            
            # Show info in console
            print("\n" + "="*60)
            print("✅ IFC FILE SAVED")
            print("="*60)
            print(f"File: {self.filepath}")
            print(f"Entities: {info['entities']}")
            print(f"Alignments: {info['alignments']}")
            print(f"Geomodels: {info['geomodels']}")
            print("="*60 + "\n")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save IFC file: {str(e)}")
            print(f"❌ Error saving IFC: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        """Open file browser with default filename"""
        # Set default filename
        if NativeIfcManager.filepath:
            self.filepath = NativeIfcManager.filepath
        else:
            self.filepath = "BlenderCivil_Project.ifc"
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BC_OT_clear_ifc(Operator):
    """Clear current IFC file and Blender hierarchy"""
    bl_idname = "bc.clear_ifc"
    bl_label = "Clear IFC"
    bl_description = "Clear current IFC file and remove Blender visualization"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """Clear IFC data and Blender hierarchy"""
        
        try:
            NativeIfcManager.clear()
            
            self.report({'INFO'}, "Cleared IFC file and hierarchy")
            print("\n✅ IFC data cleared\n")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clear IFC: {str(e)}")
            print(f"❌ Error clearing IFC: {str(e)}")
            return {'CANCELLED'}


class BC_OT_show_ifc_info(Operator):
    """Show current IFC file information"""
    bl_idname = "bc.show_ifc_info"
    bl_label = "Show IFC Info"
    bl_description = "Display current IFC file information in console"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        """Display IFC file information"""
        
        info = NativeIfcManager.get_info()
        
        if not info['loaded']:
            self.report({'INFO'}, "No IFC file loaded")
            return {'FINISHED'}
        
        # Display in console
        print("\n" + "="*60)
        print("📊 IFC FILE INFORMATION")
        print("="*60)
        print(f"File: {info['filepath'] or 'Not saved'}")
        print(f"Schema: {info['schema']}")
        print(f"Total Entities: {info['entities']}")
        print(f"\nSpatial Structure:")
        print(f"  Project: {info['project']}")
        print(f"  Site: {info['site']}")
        print(f"  Road: {info['road']}")
        print(f"\nCivil Elements:")
        print(f"  Alignments: {info['alignments']}")
        print(f"  Geomodels: {info['geomodels']}")
        print("="*60 + "\n")
        
        self.report({'INFO'}, 
            f"IFC Info: {info['entities']} entities, "
            f"{info['alignments']} alignments")
        
        return {'FINISHED'}


# ============================================================================
# Registration
# ============================================================================

classes = (
    BC_OT_new_ifc,
    BC_OT_open_ifc,
    BC_OT_save_ifc,
    BC_OT_clear_ifc,
    BC_OT_show_ifc_info,
)


def register():
    """Register operators"""
    for cls in classes:
        bpy.utils.register_class(cls)
    print("✅ Registered IFC operators")


def unregister():
    """Unregister operators"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("✅ Unregistered IFC operators")


if __name__ == "__main__":
    register()
