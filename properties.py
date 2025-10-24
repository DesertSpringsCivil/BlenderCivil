"""
BlenderCivil Properties

Custom properties for:
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
from bpy.types import PropertyGroup

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
    
    curve_radius: FloatProperty(
        name="Curve Radius",
        description="Radius for horizontal curves",
        default=500.0,
        min=10.0,
        max=10000.0,
        unit='LENGTH'
    )
    
    pi_size: FloatProperty(
        name="PI Marker Size",
        description="Size of PI point markers",
        default=5.0,
        min=0.1,
        max=50.0
    )
    
    alignment_name: StringProperty(
        name="Alignment Name",
        description="Name of the current alignment",
        default="Alignment_01"
    )

class CoordinateSystemProperties(PropertyGroup):
    """Properties for coordinate reference system"""
    
    epsg_code: StringProperty(
        name="EPSG Code",
        description="EPSG code for the coordinate reference system",
        default=""
    )
    
    coordinate_system_name: StringProperty(
        name="CRS Name",
        description="Name of the coordinate reference system",
        default=""
    )
    
    datum: StringProperty(
        name="Datum",
        description="Geodetic datum",
        default=""
    )
    
    projection: StringProperty(
        name="Projection",
        description="Map projection type",
        default=""
    )
    
    units: StringProperty(
        name="Units",
        description="Linear units",
        default="meters"
    )
    
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Scale factor for unit conversion",
        default=1.0
    )
    
    vertical_datum: StringProperty(
        name="Vertical Datum",
        description="Vertical datum",
        default=""
    )
    
    has_crs: BoolProperty(
        name="Has CRS",
        description="Whether coordinate system has been set",
        default=False
    )

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
        ],
        default='NONE'
    )
    
    global_id: StringProperty(
        name="GlobalId",
        description="IFC GlobalId (UUID)",
        default=""
    )
    
    is_alignment_entity: BoolProperty(
        name="Is Alignment Entity",
        description="Mark as IFC alignment entity",
        default=False
    )

def register():
    """Register property groups"""
    bpy.utils.register_class(AlignmentProperties)
    bpy.utils.register_class(CoordinateSystemProperties)
    bpy.utils.register_class(IFCProperties)
    
    # Register to Scene
    bpy.types.Scene.civil_alignment = PointerProperty(type=AlignmentProperties)
    bpy.types.Scene.civil_crs = PointerProperty(type=CoordinateSystemProperties)
    
    # Register to Object for per-object IFC properties
    bpy.types.Object.civil_ifc = PointerProperty(type=IFCProperties)
    
    # Legacy properties for backward compatibility
    # These can be accessed as scene["coordinate_system"] etc.
    # No need to explicitly register these as they're dynamic

def unregister():
    """Unregister property groups"""
    del bpy.types.Object.civil_ifc
    del bpy.types.Scene.civil_crs
    del bpy.types.Scene.civil_alignment
    
    bpy.utils.unregister_class(IFCProperties)
    bpy.utils.unregister_class(CoordinateSystemProperties)
    bpy.utils.unregister_class(AlignmentProperties)
