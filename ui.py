"""
BlenderCivil - User Interface

UI panels for the Civil engineering workspace in the 3D View sidebar
"""

import bpy
from bpy.types import Panel
import json


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
        scene = context.scene
        
        # Header with addon info
        box = layout.box()
        row = box.row()
        row.label(text="Civil Engineering Tools", icon='TOOL_SETTINGS')
        
        # Version and status
        col = box.column(align=True)
        col.label(text="Version 0.1.0 Alpha")
        
        # Quick CRS status
        if hasattr(scene, 'civil_crs') and scene.civil_crs.has_crs:
            status_box = layout.box()
            status_box.label(text=f"CRS: EPSG:{scene.civil_crs.epsg_code}", icon='WORLD')
        

# ============================================================================
# OASYS INTEGRATION PANEL
# ============================================================================

class CIVIL_PT_OASYS(Panel):
    """OASYS Cloud Platform Integration"""
    bl_label = "OASYS Platform"
    bl_idname = "CIVIL_PT_oasys"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    bl_parent_id = "CIVIL_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Check if properties exist
        if not hasattr(scene, 'civil_properties'):
            layout.label(text="Properties not loaded", icon='ERROR')
            return
        
        props = scene.civil_properties
        oasys = props.oasys
        
        # API Configuration
        box = layout.box()
        box.label(text="Configuration", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(oasys, "oasys_api_url", text="API URL")
        
        # Connection test
        row = box.row(align=True)
        row.operator("civil.connect_oasys", text="Test Connection", icon='PLUGIN')
        if oasys.is_connected:
            row.label(text="✓", icon='CHECKMARK')
        
        # PDF Upload
        box = layout.box()
        box.label(text="Upload Plan", icon='IMPORT')
        box.operator("civil.upload_plan_pdf", text="Upload PDF for Processing", icon='FILE_FOLDER')
        
        # List and retrieve CRS files
        box = layout.box()
        box.label(text="Coordinate Systems", icon='WORLD')
        col = box.column(align=True)
        col.operator("civil.list_crs_files", text="Refresh List", icon='FILE_REFRESH')
        
        # Display available CRS files
        try:
            files_json = oasys.available_crs_files
            if files_json and files_json != "[]":
                files = json.loads(files_json)
                
                if files:
                    box2 = layout.box()
                    box2.label(text=f"Available: {len(files)} files", icon='DOCUMENTS')
                    
                    # Show first few files
                    for i, file_info in enumerate(files[:5]):
                        key = file_info.get('key', 'unknown')
                        filename = key.split('/')[-1].replace('_crs.json', '')
                        row = box2.row()
                        
                        # Button to select and apply this CRS
                        op = row.operator("civil.set_coordinate_system", text=filename, icon='FILE')
                        op.crs_file_key = key
                    
                    if len(files) > 5:
                        box2.label(text=f"...and {len(files)-5} more")
                else:
                    col.label(text="No CRS files found", icon='INFO')
            else:
                col.label(text="Click 'Refresh List'", icon='INFO')
        except:
            col.label(text="Error loading files", icon='ERROR')


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
        scene = context.scene
        
        # Check if properties exist
        if not hasattr(scene, 'civil_crs'):
            layout.label(text="Properties not loaded", icon='ERROR')
            return
        
        crs = scene.civil_crs
        
        # Current CRS display
        if crs.has_crs:
            box = layout.box()
            box.label(text="Current CRS", icon='WORLD')
            col = box.column(align=True)
            col.label(text=f"Name: {crs.coordinate_system_name}")
            col.label(text=f"EPSG: {crs.epsg_code}")
            col.label(text=f"Units: {crs.units}")
            
            if crs.datum:
                col.label(text=f"H. Datum: {crs.datum}")
            if crs.vertical_datum:
                col.label(text=f"V. Datum: {crs.vertical_datum}")
            if crs.zone:
                col.label(text=f"Zone: {crs.zone}")
            
            # Scale factor
            if crs.scale_factor != 1.0:
                col.label(text=f"Scale: {crs.scale_factor:.10f}")
            
            # Confidence and source
            if crs.confidence != 'NONE':
                row = col.row()
                row.label(text=f"Confidence: {crs.confidence}")
            if crs.source:
                col.label(text=f"Source: {crs.source}")
            
            layout.separator()
            
        else:
            box = layout.box()
            box.label(text="No CRS Set", icon='INFO')
            box.label(text="Use OASYS to fetch CRS data")
        
        # Scene properties (if set via OASYS)
        if 'EPSG_Code' in scene:
            box = layout.box()
            box.label(text="Scene Properties", icon='PROPERTIES')
            col = box.column(align=True)
            col.label(text=f"EPSG: {scene.get('EPSG_Code', 'None')}")
            col.label(text=f"Units: {scene.get('Units', 'None')}")
            col.label(text=f"Scale: {scene.get('ScaleFactor', 1.0):.10f}")
        
        # Bonsai Integration (if available)
        try:
            import bonsai
            box = layout.box()
            box.label(text="Bonsai Integration", icon='EXPORT')
            if crs.has_crs:
                box.label(text="Ready for IFC export", icon='CHECKMARK')
                box.label(text="Use Bonsai to create IFC project")
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
        scene = context.scene
        
        # Check if properties exist
        if not hasattr(scene, 'civil_alignment'):
            layout.label(text="Properties not loaded", icon='ERROR')
            return
        
        props = scene.civil_alignment
        
        # Alignment Name
        box = layout.box()
        box.prop(props, "alignment_name", text="Name")
        
        # PI Points Section
        box = layout.box()
        box.label(text="PI Points", icon='EMPTY_AXIS')
        col = box.column(align=True)
        col.operator("civil.add_pi_point", text="Add PI at Cursor", icon='ADD')
        col.prop(props, "pi_size", text="Display Size")
        
        # Count PI points
        pi_count = len([o for o in scene.objects if o.name.startswith('PI_')])
        if pi_count > 0:
            box.label(text=f"Total PIs: {pi_count}", icon='INFO')
        
        # Create Alignment Section
        box = layout.box()
        box.label(text="Create Alignment", icon='CURVE_BEZCURVE')
        col = box.column(align=True)
        col.operator("civil.create_alignment_tangents", text="Tangents Only", icon='IPO_LINEAR')
        col.operator("civil.create_alignment_curves", text="With Curves", icon='IPO_BEZIER')
        col.prop(props, "curve_radius", text="Default Radius")
        
        # Station Labels Section
        box = layout.box()
        box.label(text="Station Labels", icon='FONT_DATA')
        col = box.column(align=True)
        col.prop(props, "station_interval", text="Interval")
        col.prop(props, "start_station", text="Start Station")
        col.prop(props, "text_size", text="Label Size")
        col.operator("civil.apply_station_labels", text="Apply Labels", icon='LINENUMBERS_ON')
        
        # Import/Export Section
        box = layout.box()
        box.label(text="Import/Export", icon='IMPORT')
        col = box.column(align=True)
        col.operator("civil.import_landxml", text="Import LandXML", icon='IMPORT')
        col.operator("civil.export_ifc_alignment", text="Export IFC", icon='EXPORT')
        
        # Utilities Section
        box = layout.box()
        box.label(text="Utilities", icon='TOOL_SETTINGS')
        col = box.column(align=True)
        col.operator("civil.calculate_curve_data", text="Calculate Curve Data", icon='COMMUNITY')
        col.operator("civil.clear_pi_points", text="Clear All PIs", icon='TRASH')


# ============================================================================
# VERTICAL ALIGNMENT PANEL (Placeholder)
# ============================================================================

class CIVIL_PT_VerticalAlignment(Panel):
    """Vertical Alignment design panel (future feature)"""
    bl_label = "Vertical Alignment"
    bl_idname = "CIVIL_PT_vertical_alignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    bl_parent_id = "CIVIL_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Coming Soon", icon='TIME')
        box.label(text="Vertical alignment tools")
        box.label(text="will be added in a future version")


# ============================================================================
# TERRAIN PANEL (Placeholder)
# ============================================================================

class CIVIL_PT_Terrain(Panel):
    """Terrain modeling panel (future feature)"""
    bl_label = "Terrain"
    bl_idname = "CIVIL_PT_terrain"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    bl_parent_id = "CIVIL_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Coming Soon", icon='MESH_GRID')
        box.label(text="Terrain modeling and")
        box.label(text="DEM import coming soon")


# ============================================================================
# REGISTRATION
# ============================================================================

classes = (
    CIVIL_PT_MainPanel,
    CIVIL_PT_OASYS,
    CIVIL_PT_CoordinateSystem,
    CIVIL_PT_HorizontalAlignment,
    CIVIL_PT_VerticalAlignment,
    CIVIL_PT_Terrain,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("BlenderCivil UI registered")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
