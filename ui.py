"""
BlenderCivil - User Interface

UI panels for the Civil engineering workspace
"""

import bpy
from bpy.types import Panel

# ============================================================================
# MAIN CIVIL PANEL
# ============================================================================

class CIVIL_PT_MainPanel(Panel):
    """Main Civil Engineering panel"""
    bl_label = "BlenderCivil"
    bl_idname = "CIVIL_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    
    def draw(self, context):
        layout = self.layout
        
        # Header with info
        box = layout.box()
        row = box.row()
        row.label(text="Civil Engineering Tools", icon='TOOL_SETTINGS')
        
        # Quick actions
        col = box.column(align=True)
        col.operator("civil.open_preferences", icon='PREFERENCES')

# ============================================================================
# COORDINATE SYSTEM PANEL
# ============================================================================

class CIVIL_PT_CoordinateSystem(Panel):
    """Coordinate Reference System panel"""
    bl_label = "Coordinate System"
    bl_idname = "CIVIL_PT_coordinate_system"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    bl_parent_id = "CIVIL_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        crs = context.scene.civil_crs
        
        # Current CRS display
        if crs.has_crs:
            box = layout.box()
            box.label(text="Current CRS", icon='WORLD')
            col = box.column(align=True)
            col.label(text=f"Name: {crs.coordinate_system_name}")
            col.label(text=f"EPSG: {crs.epsg_code}")
            col.label(text=f"Units: {crs.units}")
            if crs.datum:
                col.label(text=f"Datum: {crs.datum}")
            
            row = box.row()
            row.operator("civil.clear_crs", icon='X')
        else:
            box = layout.box()
            box.label(text="No CRS Set", icon='INFO')
        
        # OASYS Section
        box = layout.box()
        box.label(text="OASYS Platform", icon='NETWORK_DRIVE')
        col = box.column(align=True)
        col.operator("civil.list_crs", text="List Available", icon='VIEWZOOM')
        col.operator("civil.fetch_crs", text="Fetch from OASYS", icon='IMPORT')
        
        # Manual Entry
        box = layout.box()
        box.label(text="Manual Entry", icon='HAND')
        box.operator("civil.set_crs_manual", text="Set Manually", icon='GREASEPENCIL')
        
        # Bonsai Integration
        try:
            from bonsai.bim.ifc import IfcStore
            box = layout.box()
            box.label(text="Bonsai Integration", icon='EXPORT')
            if crs.has_crs:
                box.operator("civil.apply_crs_to_bonsai", text="Apply to Bonsai", icon='CHECKMARK')
            else:
                box.label(text="Set CRS first", icon='INFO')
        except ImportError:
            pass

# ============================================================================
# HORIZONTAL ALIGNMENT PANEL
# ============================================================================

class CIVIL_PT_HorizontalAlignment(Panel):
    """Horizontal Alignment design panel"""
    bl_label = "Horizontal Alignment"
    bl_idname = "CIVIL_PT_horizontal_alignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    bl_parent_id = "CIVIL_PT_main_panel"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.civil_alignment
        
        # Alignment Name
        box = layout.box()
        box.prop(props, "alignment_name")
        
        # PI Points
        box = layout.box()
        box.label(text="PI Points", icon='OUTLINER_OB_EMPTY')
        col = box.column(align=True)
        col.operator("civil.add_pi", text="Add PI at Cursor", icon='ADD')
        col.prop(props, "pi_size")
        
        # Tangents
        box = layout.box()
        box.label(text="Tangents", icon='IPO_LINEAR')
        box.operator("civil.create_tangents", text="Create Tangents", icon='CURVE_PATH')
        
        # Curves
        box = layout.box()
        box.label(text="Horizontal Curves", icon='IPO_BEZIER')
        col = box.column(align=True)
        col.prop(props, "curve_radius")
        col.operator("civil.insert_curves", text="Insert Curves", icon='CURVE_BEZCURVE')
        
        # Stations
        box = layout.box()
        box.label(text="Stations", icon='LINENUMBERS_ON')
        col = box.column(align=True)
        col.prop(props, "station_interval")
        col.operator("civil.add_stations", text="Add Station Markers", icon='FONT_DATA')
        
        # Utilities
        box = layout.box()
        box.label(text="Utilities", icon='TOOL_SETTINGS')
        col = box.column(align=True)
        col.operator("civil.export_alignment", text="Export to JSON", icon='EXPORT')
        col.operator("civil.clear_alignment", text="Clear All", icon='TRASH')
        
        # Info
        layout.separator()
        pi_col = bpy.data.collections.get("PI_Points")
        if pi_col:
            pi_count = len([obj for obj in pi_col.objects if "is_pi" in obj])
            layout.label(text=f"Total PIs: {pi_count}")

# ============================================================================
# REGISTRATION
# ============================================================================

classes = (
    CIVIL_PT_MainPanel,
    CIVIL_PT_CoordinateSystem,
    CIVIL_PT_HorizontalAlignment,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
