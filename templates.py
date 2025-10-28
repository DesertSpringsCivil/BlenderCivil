"""
BlenderCivil - Cross-Section Template Factory
Sprint 1 Day 2: Standard Template Library

This module provides factory functions for creating standard,
DOT-compliant cross-section templates.

Author: BlenderCivil Development Team
Date: October 27, 2025
"""

import bpy


def create_rural_2lane_template(scene):
    """
    Create standard rural 2-lane highway template.
    
    Specifications (AASHTO Green Book):
    - 2 lanes @ 12' each = 24' traveled way
    - 8' paved shoulders each side
    - -2% normal crown (lanes slope away from center)
    - -4% shoulder slope
    - Total width: 40' (shoulder to shoulder)
    
    Returns:
        CrossSectionTemplate: The created template
    """
    template = scene.cross_section_templates.add()
    
    # Basic identification
    template.name = "Rural 2-Lane"
    template.template_type = 'RURAL'
    template.description = "Standard rural 2-lane highway with paved shoulders"
    template.symmetrical = True
    template.crown_type = 'NORMAL'
    
    # Left side (1 lane)
    template.lanes_left.count = 1
    template.lanes_left.width = 12.0  # feet
    template.lanes_left.cross_slope = -0.02  # -2%
    
    # Right side (1 lane)
    template.lanes_right.count = 1
    template.lanes_right.width = 12.0  # feet
    template.lanes_right.cross_slope = -0.02  # -2%
    
    # Left shoulder
    template.shoulder_left.width = 8.0  # feet
    template.shoulder_left.slope = -0.04  # -4%
    template.shoulder_left.type = 'PAVED'
    
    # Right shoulder
    template.shoulder_right.width = 8.0  # feet
    template.shoulder_right.slope = -0.04  # -4%
    template.shoulder_right.type = 'PAVED'
    
    # No median for 2-lane
    template.has_median = False
    
    # Default station range
    template.start_station = 0.0
    template.end_station = 10000.0  # 10,000 feet
    
    print("Created: " + template.name)
    print("   Total width: 40' (shoulder to shoulder)")
    print("   Traveled way: 24' (2 x 12')")
    
    return template


def create_urban_4lane_arterial_template(scene):
    """Create urban 4-lane arterial with curb & gutter."""
    template = scene.cross_section_templates.add()
    
    template.name = "Urban 4-Lane Arterial"
    template.template_type = 'URBAN'
    template.description = "Urban 4-lane arterial with curb and gutter"
    template.symmetrical = True
    template.crown_type = 'NORMAL'
    
    template.lanes_left.count = 2
    template.lanes_left.width = 11.0
    template.lanes_left.cross_slope = -0.02
    
    template.lanes_right.count = 2
    template.lanes_right.width = 11.0
    template.lanes_right.cross_slope = -0.02
    
    template.shoulder_left.width = 2.0
    template.shoulder_left.slope = -0.02
    template.shoulder_left.type = 'PAVED'
    
    template.shoulder_right.width = 2.0
    template.shoulder_right.slope = -0.02
    template.shoulder_right.type = 'PAVED'
    
    template.has_median = False
    template.start_station = 0.0
    template.end_station = 10000.0
    
    print("Created: " + template.name)
    print("   Total width: 48' (curb to curb)")
    print("   Traveled way: 44' (4 x 11')")
    
    return template


def create_highway_divided_template(scene):
    """Create divided highway with median barrier."""
    template = scene.cross_section_templates.add()
    
    template.name = "Highway Divided 4-Lane"
    template.template_type = 'HIGHWAY'
    template.description = "Divided highway with 2 lanes each direction and median barrier"
    template.symmetrical = True
    template.crown_type = 'NORMAL'
    
    template.lanes_left.count = 2
    template.lanes_left.width = 12.0
    template.lanes_left.cross_slope = -0.02
    
    template.lanes_right.count = 2
    template.lanes_right.width = 12.0
    template.lanes_right.cross_slope = -0.02
    
    template.shoulder_left.width = 10.0
    template.shoulder_left.slope = -0.04
    template.shoulder_left.type = 'PAVED'
    
    template.shoulder_right.width = 10.0
    template.shoulder_right.slope = -0.04
    template.shoulder_right.type = 'PAVED'
    
    template.has_median = True
    template.median.width = 20.0
    template.median.type = 'BARRIER'
    template.median.left_slope = -0.02
    template.median.right_slope = -0.02
    
    template.start_station = 0.0
    template.end_station = 10000.0
    
    print("Created: " + template.name)
    print("   Total width: ~100' (including median)")
    print("   Each direction: 2 lanes @ 12'")
    
    return template


def create_local_street_parking_template(scene):
    """Create local residential street with parking lanes."""
    template = scene.cross_section_templates.add()
    
    template.name = "Local Street with Parking"
    template.template_type = 'URBAN'
    template.description = "Residential street with parking lanes both sides"
    template.symmetrical = True
    template.crown_type = 'NORMAL'
    
    template.lanes_left.count = 1
    template.lanes_left.width = 10.0
    template.lanes_left.cross_slope = -0.02
    
    template.lanes_right.count = 1
    template.lanes_right.width = 10.0
    template.lanes_right.cross_slope = -0.02
    
    template.shoulder_left.width = 8.0
    template.shoulder_left.slope = -0.02
    template.shoulder_left.type = 'PAVED'
    
    template.shoulder_right.width = 8.0
    template.shoulder_right.slope = -0.02
    template.shoulder_right.type = 'PAVED'
    
    template.has_median = False
    template.start_station = 0.0
    template.end_station = 5000.0
    
    print("Created: " + template.name)
    print("   Total width: 36' (curb to curb)")
    print("   Traveled way: 20' (2 x 10')")
    
    return template


def create_bike_lane_template(scene):
    """Create street with dedicated bike lanes."""
    template = scene.cross_section_templates.add()
    
    template.name = "Complete Street with Bike Lanes"
    template.template_type = 'URBAN'
    template.description = "Urban street with protected bike lanes"
    template.symmetrical = True
    template.crown_type = 'NORMAL'
    
    template.lanes_left.count = 1
    template.lanes_left.width = 11.0
    template.lanes_left.cross_slope = -0.02
    
    template.lanes_right.count = 1
    template.lanes_right.width = 11.0
    template.lanes_right.cross_slope = -0.02
    
    template.shoulder_left.width = 8.0
    template.shoulder_left.slope = -0.02
    template.shoulder_left.type = 'PAVED'
    
    template.shoulder_right.width = 8.0
    template.shoulder_right.slope = -0.02
    template.shoulder_right.type = 'PAVED'
    
    template.has_median = False
    template.start_station = 0.0
    template.end_station = 10000.0
    
    print("Created: " + template.name)
    print("   Total width: 42' (curb to curb)")
    print("   Traveled way: 22' (2 x 11')")
    
    return template


def create_all_standard_templates(scene):
    """Create all 5 standard templates in one go."""
    print("=" * 60)
    print("CREATING STANDARD TEMPLATE LIBRARY")
    print("=" * 60)
    
    templates = []
    templates.append(create_rural_2lane_template(scene))
    templates.append(create_urban_4lane_arterial_template(scene))
    templates.append(create_highway_divided_template(scene))
    templates.append(create_local_street_parking_template(scene))
    templates.append(create_bike_lane_template(scene))
    
    print("=" * 60)
    print("COMPLETE! Created " + str(len(templates)) + " standard templates")
    print("=" * 60)
    
    return templates
