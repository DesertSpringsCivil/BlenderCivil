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
    bl_idname = "BlenderCivil"
    
    # =========================================================================
    # OASYS API Settings
    # =========================================================================
    
    oasys_api_url: StringProperty(
        name="OASYS API URL",
        description="URL for OASYS coordinate system extraction API",
        default="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod",
        maxlen=1024
    )
    
    oasys_api_key: StringProperty(
        name="API Key",
        description="API key for OASYS platform (future authentication)",
        default="",
        subtype='PASSWORD',
        maxlen=256
    )
    
    auto_apply_crs: BoolProperty(
        name="Auto-Apply CRS",
        description="Automatically apply coordinate system when retrieved from OASYS",
        default=True,
    )
    
    cache_crs_files: BoolProperty(
        name="Cache CRS Files",
        description="Cache CRS file list locally to reduce API calls",
        default=True,
    )
    
    # =========================================================================
    # Default Engineering Parameters
    # =========================================================================
    
    default_station_interval: FloatProperty(
        name="Station Interval",
        description="Default distance between station markers",
        default=100.0,
        min=1.0,
        max=1000.0,
        unit='LENGTH',
    )
    
    default_start_station: FloatProperty(
        name="Start Station",
        description="Default starting station value",
        default=0.0,
        min=0.0,
        unit='LENGTH',
    )
    
    default_curve_radius: FloatProperty(
        name="Curve Radius",
        description="Default radius for horizontal curves",
        default=500.0,
        min=10.0,
        max=10000.0,
        unit='LENGTH',
    )
    
    default_pi_size: FloatProperty(
        name="PI Marker Size",
        description="Default display size for PI point markers",
        default=10.0,
        min=0.1,
        max=50.0,
    )
    
    default_text_size: FloatProperty(
        name="Station Label Size",
        description="Default size for station label text",
        default=10.0,
        min=0.1,
        max=100.0,
    )
    
    # =========================================================================
    # Unit System
    # =========================================================================
    
    unit_system: EnumProperty(
        name="Unit System",
        description="Preferred unit system for civil engineering projects",
        items=[
            ('METRIC', "Metric", "International System (meters)"),
            ('IMPERIAL', "Imperial", "US customary units (feet)"),
            ('US_SURVEY', "US Survey Feet", "US Survey Feet (slightly different from international feet)"),
        ],
        default='METRIC',
    )
    
    auto_set_scene_units: BoolProperty(
        name="Auto-Set Scene Units",
        description="Automatically set Blender scene units based on CRS",
        default=True,
    )
    
    # =========================================================================
    # IFC/OpenBIM Export Settings
    # =========================================================================
    
    export_ifc_alignment: BoolProperty(
        name="Export IFC Alignment",
        description="Include IfcAlignment entities when exporting to IFC",
        default=True,
    )
    
    export_georeferencing: BoolProperty(
        name="Export Georeferencing",
        description="Include coordinate reference system metadata in IFC exports",
        default=True,
    )
    
    ifc_schema_version: EnumProperty(
        name="IFC Schema Version",
        description="Preferred IFC schema version for exports",
        items=[
            ('IFC4', "IFC 4", "IFC 4 (2013) - Most widely supported"),
            ('IFC4X1', "IFC 4.1", "IFC 4.1 - Adds IfcAlignment"),
            ('IFC4X3', "IFC 4.3", "IFC 4.3 - Latest with infrastructure"),
        ],
        default='IFC4X1',
    )
    
    # =========================================================================
    # Bonsai Integration
    # =========================================================================
    
    auto_detect_bonsai: BoolProperty(
        name="Auto-detect Bonsai",
        description="Automatically detect and integrate with Bonsai addon",
        default=True,
    )
    
    sync_crs_with_bonsai: BoolProperty(
        name="Sync CRS with Bonsai",
        description="Synchronize coordinate system with Bonsai IFC project",
        default=True,
    )
    
    # =========================================================================
    # Alignment Design Settings
    # =========================================================================
    
    use_spiral_transitions: BoolProperty(
        name="Use Spiral Transitions",
        description="Include spiral transitions in curve design by default",
        default=False,
    )
    
    default_spiral_length: FloatProperty(
        name="Spiral Length",
        description="Default length for spiral transitions",
        default=100.0,
        min=0.0,
        max=500.0,
        unit='LENGTH',
    )
    
    show_curve_annotations: BoolProperty(
        name="Show Curve Annotations",
        description="Display curve radius, length, and deflection angle annotations",
        default=True,
    )
    
    # =========================================================================
    # Development & Debug Options
    # =========================================================================
    
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable verbose console output and additional logging",
        default=False,
    )
    
    show_api_responses: BoolProperty(
        name="Show API Responses",
        description="Print full API responses to console (for debugging)",
        default=False,
    )
    
    developer_mode: BoolProperty(
        name="Developer Mode",
        description="Enable experimental features and developer tools",
        default=False,
    )
    
    # =========================================================================
    # UI Drawing
    # =========================================================================
    
    def draw(self, context):
        layout = self.layout
        
        # Header
        row = layout.row()
        row.label(text="BlenderCivil v0.1.0 - Civil Engineering Tools", icon='TOOL_SETTINGS')
        
        layout.separator()
        
        # =====================================================================
        # OASYS API Section
        # =====================================================================
        box = layout.box()
        box.label(text="OASYS Platform Integration", icon='WORLD')
        
        col = box.column(align=True)
        col.prop(self, "oasys_api_url")
        col.prop(self, "oasys_api_key")
        
        col = box.column(align=True)
        col.prop(self, "auto_apply_crs")
        col.prop(self, "cache_crs_files")
        
        # Test connection button
        row = box.row()
        row.operator("civil.connect_oasys", text="Test Connection", icon='PLUGIN')
        
        layout.separator()
        
        # =====================================================================
        # Default Parameters Section
        # =====================================================================
        box = layout.box()
        box.label(text="Default Engineering Parameters", icon='PREFERENCES')
        
        # Unit system
        row = box.row()
        row.prop(self, "unit_system", expand=True)
        box.prop(self, "auto_set_scene_units")
        
        box.separator()
        
        # Alignment defaults
        split = box.split()
        
        col = split.column()
        col.label(text="Stations:")
        col.prop(self, "default_station_interval", text="Interval")
        col.prop(self, "default_start_station", text="Start")
        col.prop(self, "default_text_size", text="Label Size")
        
        col = split.column()
        col.label(text="Horizontal Curves:")
        col.prop(self, "default_curve_radius", text="Radius")
        col.prop(self, "use_spiral_transitions", text="Use Spirals")
        if self.use_spiral_transitions:
            col.prop(self, "default_spiral_length", text="Spiral Length")
        
        col = split.column()
        col.label(text="Display:")
        col.prop(self, "default_pi_size", text="PI Size")
        col.prop(self, "show_curve_annotations", text="Annotations")
        
        layout.separator()
        
        # =====================================================================
        # IFC/OpenBIM Section
        # =====================================================================
        box = layout.box()
        box.label(text="IFC/OpenBIM Settings", icon='EXPORT')
        
        col = box.column(align=True)
        col.prop(self, "ifc_schema_version")
        col.prop(self, "export_ifc_alignment")
        col.prop(self, "export_georeferencing")
        
        box.separator()
        
        # Bonsai integration
        col = box.column(align=True)
        col.prop(self, "auto_detect_bonsai")
        col.prop(self, "sync_crs_with_bonsai")
        
        # Check for Bonsai installation
        try:
            import bonsai
            status_box = box.box()
            row = status_box.row()
            row.label(text="✓ Bonsai addon detected", icon='CHECKMARK')
        except ImportError:
            status_box = box.box()
            status_box.alert = True
            row = status_box.row()
            row.label(text="⚠ Bonsai addon not found", icon='ERROR')
            row = status_box.row()
            row.label(text="Install Bonsai for full IFC/OpenBIM integration")
            row = status_box.row()
            row.operator("wm.url_open", text="Get Bonsai", icon='URL').url = "https://blenderbim.org/"
        
        layout.separator()
        
        # =====================================================================
        # Development Section
        # =====================================================================
        box = layout.box()
        box.label(text="Development & Debug", icon='CONSOLE')
        
        col = box.column(align=True)
        col.prop(self, "debug_mode")
        if self.debug_mode:
            col.prop(self, "show_api_responses")
        col.prop(self, "developer_mode")
        
        if self.developer_mode:
            info_box = box.box()
            info_box.label(text="Developer Mode Enabled", icon='INFO')
            info_box.label(text="Experimental features may be unstable")
        
        layout.separator()
        
        # =====================================================================
        # Links and Info
        # =====================================================================
        box = layout.box()
        box.label(text="Resources", icon='URL')
        
        row = box.row()
        row.operator("wm.url_open", text="Documentation", icon='HELP').url = "https://github.com/DesertSpringsCivil/BlenderCivil"
        row.operator("wm.url_open", text="Report Issue", icon='ERROR').url = "https://github.com/DesertSpringsCivil/BlenderCivil/issues"
        
        row = box.row()
        row.label(text="OASYS Platform: Cloud-based roadway plan processing")


# =============================================================================
# Helper Functions
# =============================================================================

def get_preferences(context=None):
    """
    Helper function to get addon preferences from any context.
    
    Usage:
        prefs = get_preferences()
        api_url = prefs.oasys_api_url
    """
    if context is None:
        context = bpy.context
    
    try:
        return context.preferences.addons["BlenderCivil"].preferences
    except KeyError:
        print("Warning: BlenderCivil addon preferences not found")
        return None


def initialize_scene_defaults(scene):
    """
    Initialize scene properties with values from preferences.
    Call this when creating a new scene or when user wants to reset to defaults.
    
    Usage:
        initialize_scene_defaults(bpy.context.scene)
    """
    prefs = get_preferences()
    if prefs is None:
        return
    
    # Initialize alignment properties
    if hasattr(scene, 'civil_alignment'):
        scene.civil_alignment.station_interval = prefs.default_station_interval
        scene.civil_alignment.start_station = prefs.default_start_station
        scene.civil_alignment.curve_radius = prefs.default_curve_radius
        scene.civil_alignment.pi_size = prefs.default_pi_size
        scene.civil_alignment.text_size = prefs.default_text_size
        scene.civil_alignment.use_spiral_transitions = prefs.use_spiral_transitions
        scene.civil_alignment.spiral_length = prefs.default_spiral_length
    
    # Initialize OASYS properties
    if hasattr(scene, 'civil_properties'):
        scene.civil_properties.oasys.oasys_api_url = prefs.oasys_api_url
    
    # Set scene units based on preference
    if prefs.auto_set_scene_units:
        if prefs.unit_system == 'METRIC':
            scene.unit_settings.length_unit = 'METERS'
        elif prefs.unit_system in ('IMPERIAL', 'US_SURVEY'):
            scene.unit_settings.length_unit = 'FEET'


def apply_preferences_to_scene(context=None):
    """
    Operator-callable function to apply current preferences to active scene.
    """
    if context is None:
        context = bpy.context
    
    initialize_scene_defaults(context.scene)
    return {'FINISHED'}


# =============================================================================
# Registration
# =============================================================================

def register():
    bpy.utils.register_class(BlenderCivilPreferences)
    print("BlenderCivil preferences registered")

def unregister():
    bpy.utils.unregister_class(BlenderCivilPreferences)
