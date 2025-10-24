"""
BlenderCivil Preferences

Addon preferences for configuring:
- OASYS API connection
- Default civil engineering parameters
- IFC export settings
- Bonsai integration options
"""

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import AddonPreferences

class BlenderCivilPreferences(AddonPreferences):
    """Preferences for BlenderCivil addon"""
    bl_idname = __package__
    
    # OASYS API Settings
    oasys_api_url: StringProperty(
        name="OASYS API URL",
        description="URL for OASYS coordinate system extraction API",
        default="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod",
    )
    
    oasys_api_key: StringProperty(
        name="API Key",
        description="API key for OASYS platform (optional)",
        default="",
        subtype='PASSWORD',
    )
    
    # Default Engineering Parameters
    default_station_interval: FloatProperty(
        name="Default Station Interval",
        description="Default distance between station markers",
        default=100.0,
        min=1.0,
        max=1000.0,
        unit='LENGTH',
    )
    
    default_curve_radius: FloatProperty(
        name="Default Curve Radius",
        description="Default radius for horizontal curves",
        default=500.0,
        min=10.0,
        max=10000.0,
        unit='LENGTH',
    )
    
    default_pi_size: FloatProperty(
        name="Default PI Size",
        description="Default size for PI markers",
        default=5.0,
        min=0.1,
        max=50.0,
    )
    
    # Unit System
    unit_system: EnumProperty(
        name="Unit System",
        description="Preferred unit system for civil engineering",
        items=[
            ('METRIC', "Metric", "International System (meters)"),
            ('IMPERIAL', "Imperial", "US customary units (feet)"),
        ],
        default='METRIC',
    )
    
    # IFC Export Settings
    export_ifc_alignment: BoolProperty(
        name="Export IFC Alignment",
        description="Include IfcAlignment entities when exporting to IFC",
        default=True,
    )
    
    export_georeferencing: BoolProperty(
        name="Export Georeferencing",
        description="Include coordinate reference system in IFC exports",
        default=True,
    )
    
    # Bonsai Integration
    auto_detect_bonsai: BoolProperty(
        name="Auto-detect Bonsai",
        description="Automatically detect and integrate with Bonsai addon",
        default=True,
    )
    
    # Development Options
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable debug output and additional logging",
        default=False,
    )
    
    def draw(self, context):
        layout = self.layout
        
        # OASYS API Section
        box = layout.box()
        box.label(text="OASYS Platform Integration", icon='WORLD')
        box.prop(self, "oasys_api_url")
        box.prop(self, "oasys_api_key")
        
        # Default Parameters Section
        box = layout.box()
        box.label(text="Default Engineering Parameters", icon='PREFERENCES')
        col = box.column(align=True)
        col.prop(self, "unit_system")
        col.prop(self, "default_station_interval")
        col.prop(self, "default_curve_radius")
        col.prop(self, "default_pi_size")
        
        # IFC/OpenBIM Section
        box = layout.box()
        box.label(text="IFC/OpenBIM Settings", icon='EXPORT')
        col = box.column(align=True)
        col.prop(self, "export_ifc_alignment")
        col.prop(self, "export_georeferencing")
        col.prop(self, "auto_detect_bonsai")
        
        # Check for Bonsai
        try:
            from bonsai.bim.ifc import IfcStore
            box.label(text="✓ Bonsai addon detected", icon='CHECKMARK')
        except ImportError:
            box.label(text="⚠ Bonsai addon not found", icon='ERROR')
            box.label(text="Install Bonsai for full IFC integration")
        
        # Development Section
        box = layout.box()
        box.label(text="Development", icon='CONSOLE')
        box.prop(self, "debug_mode")

def get_preferences(context=None):
    """Helper function to get addon preferences"""
    if context is None:
        context = bpy.context
    return context.preferences.addons[__package__].preferences

def register():
    bpy.utils.register_class(BlenderCivilPreferences)

def unregister():
    bpy.utils.unregister_class(BlenderCivilPreferences)
