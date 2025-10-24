"""
BlenderCivil Properties

Custom properties for:
- OASYS cloud platform integration
- Alignment data (PI points, curves, stations)
- Coordinate reference systems
- IFC metadata
"""

import bpy
from bpy.props import (
    StringProperty, 
    FloatProperty, 
    IntProperty, 
    BoolProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import PropertyGroup, AddonPreferences


# =============================================================================
# OASYS Integration Properties
# =============================================================================

class OASYSProperties(PropertyGroup):
    """Properties for OASYS cloud platform integration"""
    
    # API Configuration
    oasys_api_url: StringProperty(
        name="OASYS API URL",
        description="Base URL for OASYS API Gateway",
        default="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod",
        maxlen=1024
    )
    
    oasys_api_key: StringProperty(
        name="API Key",
        description="Optional API key for OASYS authentication (future feature)",
        default="",
        maxlen=256,
        subtype='PASSWORD'
    )
    
    # Available CRS Files (JSON string from S3)
    available_crs_files: StringProperty(
        name="Available CRS Files",
        description="JSON list of available coordinate system files from OASYS",
        default="[]",
        maxlen=8192
    )
    
    # Selected CRS File
    selected_crs_file: StringProperty(
        name="Selected CRS File",
        description="S3 key of the selected coordinate system file",
        default="",
        maxlen=512
    )
    
    # Connection Status
    is_connected: BoolProperty(
        name="Connected",
        description="Whether connection to OASYS API is active",
        default=False
    )
    
    last_connection_time: StringProperty(
        name="Last Connection",
        description="Timestamp of last successful connection",
        default=""
    )
    
    # Processing Status
    processing_status: StringProperty(
        name="Processing Status",
        description="Status of last PDF upload/processing",
        default="idle"
    )


# =============================================================================
# Alignment Properties
# =============================================================================

class AlignmentProperties(PropertyGroup):
    """Properties for horizontal alignment design"""
    
    station_interval: FloatProperty(
        name="Station Interval",
        description="Distance between station markers",
        default=100.0,
        min=1.0,
        max=1000.0,
        unit='LENGTH'
    )
    
    start_station: FloatProperty(
        name="Start Station",
        description="Starting station value (e.g., 0+00)",
        default=0.0,
        min=0.0,
        unit='LENGTH'
    )
    
    curve_radius: FloatProperty(
        name="Default Curve Radius",
        description="Default radius for horizontal curves",
        default=500.0,
        min=10.0,
        max=10000.0,
        unit='LENGTH'
    )
    
    pi_size: FloatProperty(
        name="PI Marker Size",
        description="Display size of PI point markers",
        default=10.0,
        min=0.1,
        max=50.0
    )
    
    alignment_name: StringProperty(
        name="Alignment Name",
        description="Name of the current alignment",
        default="Alignment_01",
        maxlen=128
    )
    
    # Station Label Settings
    text_size: FloatProperty(
        name="Text Size",
        description="Size of station label text",
        default=10.0,
        min=0.1,
        max=100.0
    )
    
    show_station_labels: BoolProperty(
        name="Show Station Labels",
        description="Display station labels along alignment",
        default=True
    )
    
    # Curve Settings
    use_spiral_transitions: BoolProperty(
        name="Use Spiral Transitions",
        description="Add spiral transitions to curves",
        default=False
    )
    
    spiral_length: FloatProperty(
        name="Spiral Length",
        description="Length of spiral transitions",
        default=100.0,
        min=0.0,
        max=500.0,
        unit='LENGTH'
    )


# =============================================================================
# Coordinate System Properties
# =============================================================================

class CoordinateSystemProperties(PropertyGroup):
    """Properties for coordinate reference system (enhanced for OASYS)"""
    
    # Primary CRS Identification
    epsg_code: StringProperty(
        name="EPSG Code",
        description="EPSG code for the coordinate reference system",
        default="",
        maxlen=16
    )
    
    coordinate_system_name: StringProperty(
        name="CRS Name",
        description="Full name of the coordinate reference system",
        default="",
        maxlen=256
    )
    
    # Datum Information
    datum: StringProperty(
        name="Horizontal Datum",
        description="Geodetic datum (e.g., NAD83, WGS84)",
        default="",
        maxlen=64
    )
    
    vertical_datum: StringProperty(
        name="Vertical Datum",
        description="Vertical datum (e.g., NAVD88, NGVD29)",
        default="",
        maxlen=64
    )
    
    # Projection Details
    projection: StringProperty(
        name="Projection",
        description="Map projection type (e.g., Lambert Conformal Conic)",
        default="",
        maxlen=128
    )
    
    zone: StringProperty(
        name="Zone",
        description="Projection zone (e.g., Texas Central)",
        default="",
        maxlen=64
    )
    
    # Units and Conversion
    units: StringProperty(
        name="Linear Units",
        description="Linear units (meters, feet, US survey feet)",
        default="meters",
        maxlen=64
    )
    
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Scale factor for unit conversion (e.g., 0.3048006096 for US Survey Feet)",
        default=1.0,
        min=0.0001,
        max=1000.0,
        precision=10
    )
    
    # Status
    has_crs: BoolProperty(
        name="Has CRS",
        description="Whether coordinate system has been set",
        default=False
    )
    
    confidence: EnumProperty(
        name="Confidence Level",
        description="Confidence level of CRS identification",
        items=[
            ('NONE', "None", "No CRS set"),
            ('LOW', "Low", "Low confidence identification"),
            ('MEDIUM', "Medium", "Medium confidence identification"),
            ('HIGH', "High", "High confidence identification"),
        ],
        default='NONE'
    )
    
    source: StringProperty(
        name="CRS Source",
        description="Source of CRS data (e.g., OASYS, manual entry)",
        default="",
        maxlen=128
    )
    
    # OASYS-specific data
    found_on_page: IntProperty(
        name="Found on Page",
        description="PDF page where CRS was found",
        default=0,
        min=0
    )
    
    context: StringProperty(
        name="Context",
        description="Text context where CRS was identified",
        default="",
        maxlen=512
    )


# =============================================================================
# IFC/OpenBIM Properties
# =============================================================================

class IFCProperties(PropertyGroup):
    """Properties for IFC/OpenBIM metadata"""
    
    ifc_class: EnumProperty(
        name="IFC Class",
        description="IFC entity class for this object",
        items=[
            ('NONE', "None", "Not an IFC entity"),
            ('IFCALIGNMENT', "IfcAlignment", "Horizontal/vertical alignment"),
            ('IFCALIGNMENTHORIZONTAL', "IfcAlignmentHorizontal", "Horizontal alignment"),
            ('IFCALIGNMENTVERTICAL', "IfcAlignmentVertical", "Vertical alignment"),
            ('IFCALIGNMENTSEGMENT', "IfcAlignmentSegment", "Alignment segment"),
            ('IFCREFERENT', "IfcReferent", "Reference point (station, PI)"),
            ('IFCSITE', "IfcSite", "Project site"),
            ('IFCBUILDING', "IfcBuilding", "Building structure"),
            ('IFCROAD', "IfcRoad", "Road infrastructure (IFC 4.3)"),
        ],
        default='NONE'
    )
    
    global_id: StringProperty(
        name="GlobalId",
        description="IFC GlobalId (UUID)",
        default="",
        maxlen=64
    )
    
    is_alignment_entity: BoolProperty(
        name="Is Alignment Entity",
        description="Mark as IFC alignment entity",
        default=False
    )
    
    # Additional IFC Metadata
    description: StringProperty(
        name="Description",
        description="IFC entity description",
        default="",
        maxlen=512
    )
    
    object_type: StringProperty(
        name="Object Type",
        description="IFC ObjectType attribute",
        default="",
        maxlen=128
    )


# =============================================================================
# Addon Preferences
# =============================================================================

class BlenderCivilPreferences(AddonPreferences):
    """Addon-wide preferences for BlenderCivil"""
    bl_idname = "BlenderCivil"
    
    # OASYS API Settings (global defaults)
    default_oasys_api_url: StringProperty(
        name="Default OASYS API URL",
        description="Default API URL for new scenes",
        default="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod",
        maxlen=1024
    )
    
    # Display Settings
    show_debug_info: BoolProperty(
        name="Show Debug Info",
        description="Print debug information to console",
        default=False
    )
    
    auto_apply_crs: BoolProperty(
        name="Auto-Apply CRS",
        description="Automatically apply coordinate system when retrieved from OASYS",
        default=True
    )
    
    # Default Alignment Settings
    default_station_interval: FloatProperty(
        name="Default Station Interval",
        description="Default distance between station markers",
        default=100.0,
        min=1.0,
        max=1000.0
    )
    
    default_curve_radius: FloatProperty(
        name="Default Curve Radius",
        description="Default radius for horizontal curves",
        default=500.0,
        min=10.0,
        max=10000.0
    )
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="OASYS Integration", icon='WORLD')
        box.prop(self, "default_oasys_api_url")
        box.prop(self, "auto_apply_crs")
        
        box = layout.box()
        box.label(text="Alignment Defaults", icon='CURVE_BEZCURVE')
        box.prop(self, "default_station_interval")
        box.prop(self, "default_curve_radius")
        
        box = layout.box()
        box.label(text="Development", icon='PREFERENCES')
        box.prop(self, "show_debug_info")


# =============================================================================
# Unified Scene Properties Container
# =============================================================================

class CivilProperties(PropertyGroup):
    """Main property group that contains all civil engineering properties"""
    
    # Sub-property groups
    oasys: PointerProperty(type=OASYSProperties)
    alignment: PointerProperty(type=AlignmentProperties)
    crs: PointerProperty(type=CoordinateSystemProperties)
    
    # Quick access properties for operators
    @property
    def oasys_api_url(self):
        """Quick access to OASYS API URL"""
        return self.oasys.oasys_api_url
    
    @property
    def selected_crs_file(self):
        """Quick access to selected CRS file"""
        return self.oasys.selected_crs_file
    
    @property
    def available_crs_files(self):
        """Quick access to available CRS files"""
        return self.oasys.available_crs_files


# =============================================================================
# Registration
# =============================================================================

classes = (
    OASYSProperties,
    AlignmentProperties,
    CoordinateSystemProperties,
    IFCProperties,
    BlenderCivilPreferences,
    CivilProperties,
)

def register():
    """Register property groups"""
    # Register all property classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register main property group to Scene
    bpy.types.Scene.civil_properties = PointerProperty(type=CivilProperties)
    
    # Register individual groups for backward compatibility and direct access
    bpy.types.Scene.civil_alignment = PointerProperty(type=AlignmentProperties)
    bpy.types.Scene.civil_crs = PointerProperty(type=CoordinateSystemProperties)
    bpy.types.Scene.civil_oasys = PointerProperty(type=OASYSProperties)
    
    # Register IFC properties to Object for per-object metadata
    bpy.types.Object.civil_ifc = PointerProperty(type=IFCProperties)
    
    print("BlenderCivil properties registered")

def unregister():
    """Unregister property groups"""
    # Unregister from types
    del bpy.types.Object.civil_ifc
    del bpy.types.Scene.civil_oasys
    del bpy.types.Scene.civil_crs
    del bpy.types.Scene.civil_alignment
    del bpy.types.Scene.civil_properties
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
