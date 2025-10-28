"""
BlenderCivil - Core Georeferencing System
IFC4 IfcMapConversion Compliant

Handles real-world coordinates using false origin approach to overcome
Blender's float32 precision limitations. Maintains < 1mm precision for
projects up to 20km from false origin.

Key Concepts:
- False Origin: Reference point in map coordinates (large numbers)
- Local Coordinates: Blender's coordinate system (small numbers, centered near origin)
- Map Coordinates: Real-world coordinates (UTM, State Plane, etc.)

Author: BlenderCivil Development Team
Date: October 28, 2025
"""

import bpy
import math
from bpy.props import *
from bpy.types import PropertyGroup
from mathutils import Vector, Matrix


class BCGeoreferencing(PropertyGroup):
    """
    IFC4 IfcMapConversion compliant georeferencing system.
    
    Stores the transformation between Blender's local coordinate system
    and real-world map coordinates. Uses false origin to handle large
    coordinate values while maintaining sub-millimeter precision.
    """
    
    # ========================================================================
    # CRS Definition
    # ========================================================================
    
    crs_name: StringProperty(
        name="CRS Name",
        default="",
        description="Coordinate Reference System name (e.g., 'NAD83 / UTM zone 10N')"
    )
    
    epsg_code: IntProperty(
        name="EPSG Code",
        default=0,
        min=0,
        description="EPSG code for CRS (e.g., 26910 for NAD83 UTM 10N)"
    )
    
    # ========================================================================
    # False Origin (IFC IfcMapConversion)
    # ========================================================================
    
    false_easting: FloatProperty(
        name="False Easting",
        default=0.0,
        precision=3,
        description="False origin X in map coordinates (meters). Typically set to project center easting."
    )
    
    false_northing: FloatProperty(
        name="False Northing",
        default=0.0,
        precision=3,
        description="False origin Y in map coordinates (meters). Typically set to project center northing."
    )
    
    false_elevation: FloatProperty(
        name="False Elevation",
        default=0.0,
        precision=3,
        description="False origin Z in map coordinates (meters). Typically set to project base elevation."
    )
    
    # ========================================================================
    # Rotation (Project North vs Grid North)
    # ========================================================================
    
    rotation_angle: FloatProperty(
        name="Grid Rotation",
        default=0.0,
        precision=6,
        subtype='ANGLE',
        description="Rotation angle from project north to grid north (radians)"
    )
    
    # IFC IfcMapConversion rotation components
    x_axis_abscissa: FloatProperty(
        name="X Axis Abscissa",
        default=1.0,
        precision=8,
        description="Cosine of rotation angle (computed from rotation_angle)"
    )
    
    x_axis_ordinate: FloatProperty(
        name="X Axis Ordinate",
        default=0.0,
        precision=8,
        description="Sine of rotation angle (computed from rotation_angle)"
    )
    
    # ========================================================================
    # Scale
    # ========================================================================
    
    scale_factor: FloatProperty(
        name="Scale Factor",
        default=1.0,
        min=0.9,
        max=1.1,
        precision=8,
        description="Scale factor from local to map coordinates (typically very close to 1.0)"
    )
    
    # ========================================================================
    # Status Flags
    # ========================================================================
    
    is_georeferenced: BoolProperty(
        name="Is Georeferenced",
        default=False,
        description="Whether the project has georeferencing information"
    )
    
    auto_center_on_import: BoolProperty(
        name="Auto Center on Import",
        default=True,
        description="Automatically calculate false origin when importing survey data"
    )
    
    # ========================================================================
    # Precision Tracking
    # ========================================================================
    
    max_distance_from_origin: FloatProperty(
        name="Max Distance from Origin",
        default=0.0,
        description="Maximum distance of any geometry from Blender origin (for precision tracking)"
    )
    
    precision_warning_threshold: FloatProperty(
        name="Precision Warning Threshold",
        default=20000.0,  # 20km
        description="Distance threshold for precision warnings (meters)"
    )
    
    def update_rotation_components(self):
        """Update x_axis_abscissa and x_axis_ordinate from rotation_angle"""
        self.x_axis_abscissa = math.cos(self.rotation_angle)
        self.x_axis_ordinate = math.sin(self.rotation_angle)
    
    def get_false_origin_vector(self):
        """Get false origin as a Vector"""
        return Vector((self.false_easting, self.false_northing, self.false_elevation))
    
    def get_rotation_matrix(self):
        """Get 2D rotation matrix for horizontal plane"""
        cos_a = math.cos(self.rotation_angle)
        sin_a = math.sin(self.rotation_angle)
        
        # 3x3 rotation matrix around Z-axis
        return Matrix((
            (cos_a, -sin_a, 0.0),
            (sin_a,  cos_a, 0.0),
            (0.0,    0.0,   1.0)
        ))


class GeoreferencingUtils:
    """
    Utility functions for coordinate transformations between local and map coordinates.
    
    All functions are static methods for easy use throughout the addon.
    """
    
    @staticmethod
    def local_to_map(local_coord, georef):
        """
        Transform local Blender coordinates to real-world map coordinates.
        
        Process:
        1. Scale local coordinates
        2. Rotate (if needed)
        3. Translate by false origin
        
        Args:
            local_coord: Vector or tuple (x, y, z) in Blender local space
            georef: BCGeoreferencing property group
            
        Returns:
            Vector in map coordinates (easting, northing, elevation)
        """
        if not isinstance(local_coord, Vector):
            local_coord = Vector(local_coord)
        
        # Step 1: Scale
        scaled = local_coord * georef.scale_factor
        
        # Step 2: Rotate (2D rotation in XY plane)
        if abs(georef.rotation_angle) > 1e-6:
            rot_matrix = georef.get_rotation_matrix()
            rotated = rot_matrix @ scaled
        else:
            rotated = scaled
        
        # Step 3: Translate by false origin
        false_origin = georef.get_false_origin_vector()
        map_coord = rotated + false_origin
        
        return map_coord
    
    @staticmethod
    def map_to_local(map_coord, georef):
        """
        Transform real-world map coordinates to local Blender coordinates.
        
        Process (reverse of local_to_map):
        1. Subtract false origin
        2. Rotate back (if needed)
        3. Scale back
        
        Args:
            map_coord: Vector or tuple (easting, northing, elevation) in map space
            georef: BCGeoreferencing property group
            
        Returns:
            Vector in Blender local coordinates
        """
        if not isinstance(map_coord, Vector):
            map_coord = Vector(map_coord)
        
        # Step 1: Translate by negative false origin
        false_origin = georef.get_false_origin_vector()
        translated = map_coord - false_origin
        
        # Step 2: Rotate back (inverse rotation)
        if abs(georef.rotation_angle) > 1e-6:
            rot_matrix = georef.get_rotation_matrix()
            rot_matrix_inv = rot_matrix.inverted()
            rotated = rot_matrix_inv @ translated
        else:
            rotated = translated
        
        # Step 3: Scale back
        local_coord = rotated / georef.scale_factor
        
        return local_coord
    
    @staticmethod
    def calculate_optimal_false_origin(map_coords_list):
        """
        Calculate optimal false origin for a list of map coordinates.
        Uses centroid and rounds to nearest 100m for clean numbers.
        
        Args:
            map_coords_list: List of Vectors in map coordinates
            
        Returns:
            Vector representing optimal false origin
        """
        if not map_coords_list:
            return Vector((0, 0, 0))
        
        # Calculate centroid
        centroid = Vector((0, 0, 0))
        for coord in map_coords_list:
            if not isinstance(coord, Vector):
                coord = Vector(coord)
            centroid += coord
        centroid /= len(map_coords_list)
        
        # Round to nearest 100m for clean numbers
        false_easting = round(centroid.x / 100.0) * 100.0
        false_northing = round(centroid.y / 100.0) * 100.0
        false_elevation = round(centroid.z / 100.0) * 100.0
        
        return Vector((false_easting, false_northing, false_elevation))
    
    @staticmethod
    def verify_precision(max_distance_from_origin):
        """
        Verify that precision is adequate for given maximum distance.
        
        Blender uses float32 which has ~7 decimal digits of precision.
        For coordinate values, this means:
        - At 1m: precision ~0.1μm (0.0001mm)
        - At 100m: precision ~10μm (0.01mm)
        - At 10km: precision ~1mm
        - At 100km: precision ~10mm
        
        Args:
            max_distance_from_origin: Maximum distance in meters from Blender origin
            
        Returns:
            tuple: (is_acceptable, precision_mm, warning_message)
        """
        # Float32 has ~7 decimal digits
        # Precision = value / 10^7
        precision_meters = max_distance_from_origin / 1e7
        precision_mm = precision_meters * 1000.0
        
        if precision_mm < 1.0:
            return (True, precision_mm, None)
        elif precision_mm < 10.0:
            warning = f"Precision degraded to {precision_mm:.1f}mm at {max_distance_from_origin/1000:.1f}km from origin"
            return (False, precision_mm, warning)
        else:
            warning = f"CRITICAL: Precision degraded to {precision_mm:.0f}mm at {max_distance_from_origin/1000:.1f}km from origin. Consider splitting project or adjusting false origin."
            return (False, precision_mm, warning)
    
    @staticmethod
    def attach_real_coordinates_to_object(obj, map_coord, georef):
        """
        Attach real-world coordinates to an object as custom properties.
        
        Args:
            obj: Blender object
            map_coord: Vector in map coordinates
            georef: BCGeoreferencing property group
        """
        if not isinstance(map_coord, Vector):
            map_coord = Vector(map_coord)
        
        obj["real_easting"] = map_coord.x
        obj["real_northing"] = map_coord.y
        obj["real_elevation"] = map_coord.z
        obj["crs_name"] = georef.crs_name
        obj["epsg_code"] = georef.epsg_code
    
    @staticmethod
    def get_real_coordinates_from_object(obj):
        """
        Retrieve real-world coordinates from object custom properties.
        
        Args:
            obj: Blender object
            
        Returns:
            Vector in map coordinates, or None if not georeferenced
        """
        if "real_easting" in obj and "real_northing" in obj and "real_elevation" in obj:
            return Vector((
                obj["real_easting"],
                obj["real_northing"],
                obj["real_elevation"]
            ))
        return None


# ============================================================================
# Registration
# ============================================================================

classes = (
    BCGeoreferencing,
)

def register():
    """Register georeferencing classes"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add georeferencing property to Scene
    bpy.types.Scene.bc_georeferencing = PointerProperty(type=BCGeoreferencing)
    
    print("✓ Georeferencing system registered")

def unregister():
    """Unregister georeferencing classes"""
    # Remove Scene property
    if hasattr(bpy.types.Scene, 'bc_georeferencing'):
        del bpy.types.Scene.bc_georeferencing
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("✓ Georeferencing system unregistered")

