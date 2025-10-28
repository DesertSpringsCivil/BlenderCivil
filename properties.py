"""
BlenderCivil v0.3.0 - Professional Property System
IFC-Compatible Properties with Explicit Object References

This module defines property groups for the separate entity architecture,
using Blender's PointerProperty for explicit object relationships instead
of string-based references.

Author: BlenderCivil Development Team
Date: October 24, 2025
"""

import bpy
from bpy.props import (
    StringProperty, FloatProperty, IntProperty, 
    BoolProperty, PointerProperty, EnumProperty
)
from bpy.types import PropertyGroup


class AlignmentPIProperties(PropertyGroup):
    """
    Properties for PI (Point of Intersection) objects.
    
    Enhanced Empty objects that serve as control points for horizontal alignment.
    These correspond to intersection points where tangents would meet if extended.
    
    IFC Mapping: Part of IfcAlignment semantic structure (implicit PI)
    """
    
    # Identification
    object_type: StringProperty(
        name="Object Type",
        default='ALIGNMENT_PI',
        description="Identifies this as an alignment PI point"
    )
    
    index: IntProperty(
        name="PI Index",
        default=1,
        min=1,
        description="Sequential number of this PI in the alignment"
    )
    
    # Geometric Properties
    station: FloatProperty(
        name="Station",
        default=0.0,
        unit='LENGTH',
        description="Station location along alignment where this PI occurs"
    )
    
    radius: FloatProperty(
        name="Curve Radius",
        default=500.0,
        min=10.0,
        unit='LENGTH',
        description="Radius of the curve at this PI"
    )
    
    design_speed: FloatProperty(
        name="Design Speed",
        default=35.0,
        min=5.0,
        max=120.0,
        description="Design speed (mph) for this segment"
    )
    
    # Object Pointer Properties (Explicit References)
    alignment_root: PointerProperty(
        type=bpy.types.Object,
        name="Alignment Root",
        description="Reference to parent alignment container"
    )
    
    tangent_in: PointerProperty(
        type=bpy.types.Object,
        name="Incoming Tangent",
        description="Tangent line entering this PI"
    )
    
    tangent_out: PointerProperty(
        type=bpy.types.Object,
        name="Outgoing Tangent",
        description="Tangent line leaving this PI"
    )
    
    curve: PointerProperty(
        type=bpy.types.Object,
        name="Curve at PI",
        description="Curve element at this PI (if exists)"
    )


class AlignmentTangentProperties(PropertyGroup):
    """
    Properties for Tangent Line objects.
    
    Straight line segments connecting PIs, representing the tangent
    sections of the horizontal alignment.
    
    IFC Mapping: IfcAlignmentSegment with LINE type
    """
    
    # Identification
    object_type: StringProperty(
        name="Object Type",
        default='ALIGNMENT_TANGENT',
        description="Identifies this as an alignment tangent"
    )
    
    element_type: StringProperty(
        name="Element Type",
        default='LINE',
        description="Geometric element type"
    )
    
    # Constraint Type
    constraint: EnumProperty(
        name="Constraint",
        items=[
            ('FIXED', 'Fixed', 'Both ends locked to PIs - tangent line connects specific points'),
            ('FLOATING', 'Floating', 'Tangent to one element, maintains relationship'),
            ('FREE', 'Free', 'Tangent to both adjacent elements, fully dependent'),
        ],
        default='FIXED',
        description="Constraint type determining how this element behaves during updates"
    )
    
    # Geometric Properties
    length: FloatProperty(
        name="Length",
        default=0.0,
        unit='LENGTH',
        description="Length of this tangent segment"
    )
    
    bearing: FloatProperty(
        name="Bearing",
        default=0.0,
        unit='ROTATION',
        description="Bearing angle of this tangent (radians from north/+Y axis)"
    )
    
    # Station Properties
    start_station: FloatProperty(
        name="Start Station",
        default=0.0,
        unit='LENGTH',
        description="Station at beginning of this tangent"
    )
    
    end_station: FloatProperty(
        name="End Station",
        default=0.0,
        unit='LENGTH',
        description="Station at end of this tangent"
    )
    
    # Object Pointer Properties (Explicit References)
    alignment_root: PointerProperty(
        type=bpy.types.Object,
        name="Alignment Root",
        description="Reference to parent alignment container"
    )
    
    pi_start: PointerProperty(
        type=bpy.types.Object,
        name="Start PI",
        description="PI at the start of this tangent"
    )
    
    pi_end: PointerProperty(
        type=bpy.types.Object,
        name="End PI",
        description="PI at the end of this tangent"
    )
    
    previous_element: PointerProperty(
        type=bpy.types.Object,
        name="Previous Element",
        description="Previous element in alignment (curve or tangent)"
    )
    
    next_element: PointerProperty(
        type=bpy.types.Object,
        name="Next Element",
        description="Next element in alignment (curve or tangent)"
    )


class AlignmentCurveProperties(PropertyGroup):
    """
    Properties for Curve objects.
    
    Circular arc segments connecting tangent lines, providing smooth
    transitions at PIs.
    
    IFC Mapping: IfcAlignmentSegment with CIRCULARARC type
    """
    
    # Identification
    object_type: StringProperty(
        name="Object Type",
        default='ALIGNMENT_CURVE',
        description="Identifies this as an alignment curve"
    )
    
    element_type: StringProperty(
        name="Element Type",
        default='CURVE',
        description="Geometric element type"
    )
    
    # Constraint Type
    constraint: EnumProperty(
        name="Constraint",
        items=[
            ('FIXED', 'Fixed', 'Fixed radius and location'),
            ('FLOATING', 'Floating', 'Tangent to one element'),
            ('FREE', 'Free', 'Tangent to both adjacent tangents - most common'),
        ],
        default='FREE',
        description="Constraint type determining how this curve behaves during updates"
    )
    
    # Geometric Properties
    radius: FloatProperty(
        name="Radius",
        default=500.0,
        min=10.0,
        unit='LENGTH',
        description="Radius of this circular curve"
    )
    
    delta_angle: FloatProperty(
        name="Delta Angle",
        default=0.0,
        unit='ROTATION',
        description="Central angle (delta) of the curve in radians"
    )
    
    length: FloatProperty(
        name="Length",
        default=0.0,
        unit='LENGTH',
        description="Arc length of this curve"
    )
    
    tangent_length: FloatProperty(
        name="Tangent Length",
        default=0.0,
        unit='LENGTH',
        description="Length from PC/PT to PI along tangent"
    )
    
    # Station Properties
    start_station: FloatProperty(
        name="Start Station",
        default=0.0,
        unit='LENGTH',
        description="Station at PC (Point of Curvature)"
    )
    
    end_station: FloatProperty(
        name="End Station",
        default=0.0,
        unit='LENGTH',
        description="Station at PT (Point of Tangency)"
    )
    
    # Object Pointer Properties (Explicit References)
    alignment_root: PointerProperty(
        type=bpy.types.Object,
        name="Alignment Root",
        description="Reference to parent alignment container"
    )
    
    pi: PointerProperty(
        type=bpy.types.Object,
        name="Associated PI",
        description="PI point where this curve is located"
    )
    
    previous_element: PointerProperty(
        type=bpy.types.Object,
        name="Previous Element",
        description="Previous element in alignment (tangent)"
    )
    
    next_element: PointerProperty(
        type=bpy.types.Object,
        name="Next Element",
        description="Next element in alignment (tangent)"
    )


class AlignmentRootProperties(PropertyGroup):
    """
    Properties for Alignment Root container.
    
    Empty object serving as the root container for an alignment,
    organizing all related elements in an IFC-compatible hierarchy.
    
    IFC Mapping: IfcAlignment
    """
    
    # Identification
    object_type: StringProperty(
        name="Object Type",
        default='ALIGNMENT_ROOT',
        description="Identifies this as an alignment root container"
    )
    
    alignment_name: StringProperty(
        name="Alignment Name",
        default="Alignment_01",
        description="Human-readable name for this alignment"
    )
    
    # Alignment Type
    alignment_type: EnumProperty(
        name="Alignment Type",
        items=[
            ('CENTERLINE', 'Centerline', 'Main road/rail centerline alignment'),
            ('ROW', 'Right-of-Way', 'Right-of-way boundary line'),
            ('EASEMENT', 'Easement', 'Easement boundary line'),
            ('CURB', 'Curb', 'Curb line alignment'),
            ('EDGE_PAVEMENT', 'Edge of Pavement', 'Pavement edge line'),
            ('BASELINE', 'Baseline', 'Design baseline alignment'),
        ],
        default='CENTERLINE',
        description="Functional type of this alignment"
    )
    
    # Design Properties
    design_speed: FloatProperty(
        name="Design Speed",
        default=35.0,
        min=5.0,
        max=120.0,
        description="Design speed (mph) for this alignment"
    )
    
    total_length: FloatProperty(
        name="Total Length",
        default=0.0,
        unit='LENGTH',
        description="Total length of the alignment"
    )
    
    # Metadata
    description: StringProperty(
        name="Description",
        default="",
        description="Additional description of this alignment"
    )
    
    # Auto-update control
    auto_update_enabled: BoolProperty(
        name="Auto-Update Enabled",
        default=True,
        description="Automatically update alignment when PIs are moved"
    )




# ============================================================================
# CROSS-SECTION PROPERTIES (Sprint 1)
# ============================================================================

class LaneProperties(PropertyGroup):
    """
    Properties for a single lane or group of lanes.
    
    Represents travel lanes with consistent width and cross slope.
    IFC Mapping: Part of IfcCourse structure
    """
    
    count: IntProperty(
        name="Lane Count",
        default=1,
        min=0,
        max=8,
        description="Number of lanes"
    )
    
    width: FloatProperty(
        name="Lane Width",
        default=12.0,  # feet (default US standard)
        min=8.0,
        max=16.0,
        unit='LENGTH',
        description="Width of each lane"
    )
    
    cross_slope: FloatProperty(
        name="Cross Slope",
        default=-0.02,  # -2% (negative = down from centerline)
        min=-0.08,
        max=0.08,
        precision=4,
        description="Cross slope as decimal (e.g., -0.02 = -2%)"
    )


class ShoulderProperties(PropertyGroup):
    """
    Properties for shoulder components.
    
    Shoulders are the areas adjacent to travel lanes, providing
    emergency stopping and lateral support.
    """
    
    width: FloatProperty(
        name="Shoulder Width",
        default=8.0,  # feet
        min=0.0,
        max=20.0,
        unit='LENGTH',
        description="Width of shoulder"
    )
    
    slope: FloatProperty(
        name="Shoulder Slope",
        default=-0.04,  # -4%
        min=-0.08,
        max=0.08,
        precision=4,
        description="Shoulder slope as decimal (e.g., -0.04 = -4%)"
    )
    
    type: EnumProperty(
        name="Shoulder Type",
        items=[
            ('PAVED', 'Paved', 'Paved shoulder (asphalt/concrete)'),
            ('GRAVEL', 'Gravel', 'Gravel shoulder'),
            ('TURF', 'Turf', 'Grass/turf shoulder'),
        ],
        default='PAVED',
        description="Surface type of shoulder"
    )


class MedianProperties(PropertyGroup):
    """
    Properties for median components.
    
    Medians separate opposing traffic directions, typically in
    divided highways and arterials.
    """
    
    width: FloatProperty(
        name="Median Width",
        default=20.0,  # feet
        min=4.0,
        max=100.0,
        unit='LENGTH',
        description="Width of median"
    )
    
    type: EnumProperty(
        name="Median Type",
        items=[
            ('FLUSH', 'Flush', 'Flush median (painted or textured)'),
            ('RAISED', 'Raised', 'Raised median with curbs'),
            ('DEPRESSED', 'Depressed', 'Depressed median (drainage)'),
            ('BARRIER', 'Barrier', 'Barrier median (concrete barrier)'),
        ],
        default='FLUSH',
        description="Type of median treatment"
    )
    
    left_slope: FloatProperty(
        name="Left Slope",
        default=-0.04,
        min=-0.10,
        max=0.10,
        precision=4,
        description="Slope of left side of median"
    )
    
    right_slope: FloatProperty(
        name="Right Slope",
        default=0.04,
        min=-0.10,
        max=0.10,
        precision=4,
        description="Slope of right side of median"
    )


class CrossSectionTemplate(PropertyGroup):
    """
    Main cross-section template defining the typical section.
    
    This is the parametric definition of a road cross-section that
    can be applied to an alignment at specific station ranges.
    
    IFC Mapping: Relates to IfcSectionedSolidHorizontal concept
    """
    
    # Identification
    name: StringProperty(
        name="Template Name",
        default="Typical Section",
        description="Name of this cross-section template"
    )
    
    template_type: EnumProperty(
        name="Template Type",
        items=[
            ('RURAL', 'Rural', 'Rural road section'),
            ('URBAN', 'Urban', 'Urban street section'),
            ('HIGHWAY', 'Highway', 'Highway/freeway section'),
            ('CUSTOM', 'Custom', 'Custom user-defined section'),
        ],
        default='RURAL',
        description="Classification of this template"
    )
    
    # Geometric Properties
    symmetrical: BoolProperty(
        name="Symmetrical",
        default=True,
        description="Mirror left side to right side"
    )
    
    crown_type: EnumProperty(
        name="Crown Type",
        items=[
            ('NORMAL', 'Normal Crown', 'Standard crown (high in center)'),
            ('REVERSE', 'Reverse Crown', 'Reverse crown (low in center)'),
            ('SUPERELEVATION', 'Superelevation', 'Banked in curves'),
        ],
        default='NORMAL',
        description="Type of cross slope configuration"
    )
    
    # Station Range
    start_station: FloatProperty(
        name="Start Station",
        default=0.0,
        unit='LENGTH',
        description="Beginning station where this template applies"
    )
    
    end_station: FloatProperty(
        name="End Station",
        default=1000.0,
        unit='LENGTH',
        description="Ending station where this template applies"
    )
    
    # Component Pointers (using nested property groups)
    lanes_left: PointerProperty(
        type=LaneProperties,
        name="Left Lanes",
        description="Lane configuration for left side"
    )
    
    lanes_right: PointerProperty(
        type=LaneProperties,
        name="Right Lanes",
        description="Lane configuration for right side"
    )
    
    shoulder_left: PointerProperty(
        type=ShoulderProperties,
        name="Left Shoulder",
        description="Left shoulder configuration"
    )
    
    shoulder_right: PointerProperty(
        type=ShoulderProperties,
        name="Right Shoulder",
        description="Right shoulder configuration"
    )
    
    median: PointerProperty(
        type=MedianProperties,
        name="Median",
        description="Median configuration (if applicable)"
    )
    
    has_median: BoolProperty(
        name="Has Median",
        default=False,
        description="Whether this section includes a median"
    )
    
    # Metadata
    description: StringProperty(
        name="Description",
        default="",
        description="Additional notes about this template"
    )



# Registration

class SectionAssignment(bpy.types.PropertyGroup):
    """
    Assignment of a cross-section template to a station range.
    Sprint 1 Day 4: Station-based template assignment.
    """
    
    template_index: bpy.props.IntProperty(
        name="Template",
        description="Index of the template to use",
        default=0,
        min=0
    )
    
    start_station: bpy.props.FloatProperty(
        name="Start Station",
        description="Starting station for this section",
        default=0.0,
        unit='LENGTH',
        precision=2
    )
    
    end_station: bpy.props.FloatProperty(
        name="End Station",
        description="Ending station for this section",
        default=1000.0,
        unit='LENGTH',
        precision=2
    )
    
    transition_length: bpy.props.FloatProperty(
        name="Transition Length",
        description="Length of transition zone (for future use)",
        default=100.0,
        min=0.0,
        unit='LENGTH'
    )
    
    description: bpy.props.StringProperty(
        name="Description",
        description="Optional description of this section",
        default=""
    )



# Registration
classes = (
    # Alignment Properties
    AlignmentPIProperties,
    AlignmentTangentProperties,
    AlignmentCurveProperties,
    AlignmentRootProperties,
    # Cross-Section Properties (Sprint 1)
    LaneProperties,
    ShoulderProperties,
    MedianProperties,
    CrossSectionTemplate,
    SectionAssignment,
)







def register():
    """Register property groups"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register properties on Object type
    bpy.types.Object.alignment_pi = PointerProperty(type=AlignmentPIProperties)
    bpy.types.Object.alignment_tangent = PointerProperty(type=AlignmentTangentProperties)
    bpy.types.Object.alignment_curve = PointerProperty(type=AlignmentCurveProperties)
    bpy.types.Object.alignment_root = PointerProperty(type=AlignmentRootProperties)
    
    # Day 4: Section assignment collection
    bpy.types.Object.section_assignments = bpy.props.CollectionProperty(
        type=SectionAssignment,
        name="Section Assignments",
        description="Cross-section template assignments by station"
    )
    
    # Cross-section templates collection
    bpy.types.Scene.cross_section_templates = bpy.props.CollectionProperty(
        type=CrossSectionTemplate,
        name="Cross Section Templates",
        description="Library of cross-section templates"
    )
    
    print("âœ“ BlenderCivil v0.3.0: Property system registered")


def unregister():
    """Unregister property groups"""
    # Remove Day 4 properties
    if hasattr(bpy.types.Object, "section_assignments"):
        del bpy.types.Object.section_assignments
    if hasattr(bpy.types.Scene, "cross_section_templates"):
        del bpy.types.Scene.cross_section_templates
    
    # Remove Scene properties
    if hasattr(bpy.types.Scene, 'cross_section_templates'):
        del bpy.types.Scene.cross_section_templates
    
    # Remove properties from Object type
    del bpy.types.Object.alignment_pi
    del bpy.types.Object.alignment_tangent
    del bpy.types.Object.alignment_curve
    del bpy.types.Object.alignment_root
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
