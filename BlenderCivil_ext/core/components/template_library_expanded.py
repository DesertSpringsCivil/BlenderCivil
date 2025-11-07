"""
Expanded Template Library for BlenderCivil Cross-Sections
Comprehensive AASHTO and International Standard Templates

Sprint 4 Day 5 - Template Library Expansion
"""

import bpy
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# Import components when integrated
# from components import (
#     AssemblyComponent, LaneComponent, ShoulderComponent, 
#     CurbComponent, DitchComponent
# )
# from native_ifc_cross_section import RoadAssembly


@dataclass
class TemplateMetadata:
    """Metadata for a template."""
    name: str
    category: str  # 'AASHTO', 'Austroads', 'UK', 'Custom'
    standard: str  # e.g., 'AASHTO Green Book 2018'
    description: str
    typical_speed: str  # e.g., '50 mph (80 km/h)'
    design_vehicle: str  # e.g., 'SU (Single Unit Truck)'
    terrain: str  # 'Flat', 'Rolling', 'Mountainous'
    functional_class: str  # 'Rural', 'Urban', 'Interstate'


class TemplateLibraryExpanded:
    """
    Comprehensive template library with AASHTO, Austroads, and UK standards.
    
    Categories:
    - AASHTO (American Association of State Highway and Transportation Officials)
    - Austroads (Australian and New Zealand standards)
    - UK Design Manual for Roads and Bridges (DMRB)
    - Custom/International
    """
    
    # ==================== AASHTO TEMPLATES ====================
    
    @staticmethod
    def create_aashto_two_lane_rural(name: str = "AASHTO Two-Lane Rural Highway") -> 'RoadAssembly':
        """
        AASHTO Two-Lane Rural Highway (60 mph design)
        
        Configuration:
        - 2 lanes @ 3.6m (12 ft) each
        - Paved shoulders: 2.4m (8 ft) each side
        - 4:1 foreslope ditches
        - -2% cross slope
        
        Standard: AASHTO Green Book 2018, Chapter 5
        Design Speed: 60 mph (95 km/h)
        ADT: < 2,000 vpd
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='AASHTO',
            standard='AASHTO Green Book 2018',
            description='Standard two-lane rural highway with paved shoulders',
            typical_speed='60 mph (95 km/h)',
            design_vehicle='P (Passenger Car)',
            terrain='Rolling',
            functional_class='Rural'
        )
        
        # Right side (build outward from centerline)
        right_lane = LaneComponent.create_standard_travel_lane("RIGHT")
        right_lane.width = 3.6
        right_lane.cross_slope = -0.02
        
        right_shoulder = ShoulderComponent.create_paved_shoulder("RIGHT", 2.4)
        right_shoulder.cross_slope = -0.04
        
        right_ditch = DitchComponent.create_standard_ditch("RIGHT")
        
        assembly.add_component(right_lane)
        assembly.add_component(right_shoulder, attach_to=right_lane)
        assembly.add_component(right_ditch, attach_to=right_shoulder)
        
        # Left side
        left_lane = LaneComponent.create_standard_travel_lane("LEFT")
        left_lane.width = 3.6
        left_lane.cross_slope = -0.02
        
        left_shoulder = ShoulderComponent.create_paved_shoulder("LEFT", 2.4)
        left_shoulder.cross_slope = -0.04
        
        left_ditch = DitchComponent.create_standard_ditch("LEFT")
        
        assembly.add_component(left_lane)
        assembly.add_component(left_shoulder, attach_to=left_lane)
        assembly.add_component(left_ditch, attach_to=left_shoulder)
        
        return assembly
    
    @staticmethod
    def create_aashto_interstate(name: str = "AASHTO Interstate Highway") -> 'RoadAssembly':
        """
        AASHTO Interstate Highway (70 mph design, one direction)
        
        Configuration:
        - Inside shoulder: 3.0m (10 ft) paved
        - 2 travel lanes @ 3.6m (12 ft) each
        - Outside shoulder: 3.6m (12 ft) paved
        - 6:1 foreslope (clear zone requirement)
        - -2% cross slope
        
        Standard: AASHTO Green Book 2018, Chapter 7
        Design Speed: 70 mph (110 km/h)
        ADT: > 20,000 vpd per direction
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='AASHTO',
            standard='AASHTO Green Book 2018',
            description='Interstate highway, one direction with full shoulders',
            typical_speed='70 mph (110 km/h)',
            design_vehicle='WB-67 (Interstate Semi)',
            terrain='Flat to Rolling',
            functional_class='Interstate'
        )
        
        # Inside (left) shoulder
        inside_shoulder = ShoulderComponent.create_interstate_shoulder("LEFT")
        inside_shoulder.width = 3.0
        inside_shoulder.cross_slope = -0.02
        
        # Lane 1 (inside lane)
        lane1 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane1.width = 3.6
        lane1.cross_slope = -0.02
        
        # Lane 2 (outside lane)
        lane2 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane2.width = 3.6
        lane2.cross_slope = -0.02
        
        # Outside shoulder
        outside_shoulder = ShoulderComponent.create_interstate_shoulder("RIGHT")
        outside_shoulder.width = 3.6
        outside_shoulder.cross_slope = -0.04
        
        # Ditch with gentle slope for clear zone
        outside_ditch = DitchComponent.create_standard_ditch("RIGHT")
        outside_ditch.foreslope = 6.0  # 6:1 for clear zone
        
        # Build from inside out
        assembly.add_component(inside_shoulder)
        assembly.add_component(lane1, attach_to=inside_shoulder)
        assembly.add_component(lane2, attach_to=lane1)
        assembly.add_component(outside_shoulder, attach_to=lane2)
        assembly.add_component(outside_ditch, attach_to=outside_shoulder)
        
        return assembly
    
    @staticmethod
    def create_aashto_arterial_urban(name: str = "AASHTO Urban Arterial") -> 'RoadAssembly':
        """
        AASHTO Urban Arterial (45 mph design)
        
        Configuration:
        - Vertical curb and gutter (both sides)
        - 2 travel lanes @ 3.6m (12 ft) each
        - Parking lane: 2.4m (8 ft) both sides
        - -2% crown (center high point)
        
        Standard: AASHTO Green Book 2018, Chapter 6
        Design Speed: 45 mph (70 km/h)
        ADT: 5,000-15,000 vpd
        """
        from components import LaneComponent, CurbComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='AASHTO',
            standard='AASHTO Green Book 2018',
            description='Urban arterial with curb, gutter, and parking',
            typical_speed='45 mph (70 km/h)',
            design_vehicle='P (Passenger Car)',
            terrain='Urban',
            functional_class='Urban Principal Arterial'
        )
        
        # Right side
        right_travel = LaneComponent.create_standard_travel_lane("RIGHT")
        right_travel.width = 3.6
        right_travel.cross_slope = -0.02
        
        right_parking = LaneComponent.create_parking_lane("RIGHT")
        right_parking.width = 2.4
        right_parking.cross_slope = -0.02
        
        right_curb = CurbComponent.create_curb_and_gutter("RIGHT")
        
        assembly.add_component(right_travel)
        assembly.add_component(right_parking, attach_to=right_travel)
        assembly.add_component(right_curb, attach_to=right_parking)
        
        # Left side
        left_travel = LaneComponent.create_standard_travel_lane("LEFT")
        left_travel.width = 3.6
        left_travel.cross_slope = -0.02
        
        left_parking = LaneComponent.create_parking_lane("LEFT")
        left_parking.width = 2.4
        left_parking.cross_slope = -0.02
        
        left_curb = CurbComponent.create_curb_and_gutter("LEFT")
        
        assembly.add_component(left_travel)
        assembly.add_component(left_parking, attach_to=left_travel)
        assembly.add_component(left_curb, attach_to=left_parking)
        
        return assembly
    
    @staticmethod
    def create_aashto_collector(name: str = "AASHTO Rural Collector") -> 'RoadAssembly':
        """
        AASHTO Rural Collector (50 mph design)
        
        Configuration:
        - 2 lanes @ 3.3m (11 ft) each
        - Gravel shoulders: 1.2m (4 ft) each side
        - 4:1 foreslope ditches
        - -2% cross slope
        
        Standard: AASHTO Green Book 2018, Chapter 5
        Design Speed: 50 mph (80 km/h)
        ADT: 400-2,000 vpd
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='AASHTO',
            standard='AASHTO Green Book 2018',
            description='Rural collector with narrow lanes and gravel shoulders',
            typical_speed='50 mph (80 km/h)',
            design_vehicle='SU (Single Unit Truck)',
            terrain='Rolling to Mountainous',
            functional_class='Rural Collector'
        )
        
        # Right side
        right_lane = LaneComponent.create_standard_travel_lane("RIGHT")
        right_lane.width = 3.3  # Narrower for collector
        right_lane.cross_slope = -0.02
        
        right_shoulder = ShoulderComponent.create_gravel_shoulder("RIGHT", 1.2)
        right_shoulder.cross_slope = -0.06  # Steeper for gravel
        
        right_ditch = DitchComponent.create_standard_ditch("RIGHT")
        
        assembly.add_component(right_lane)
        assembly.add_component(right_shoulder, attach_to=right_lane)
        assembly.add_component(right_ditch, attach_to=right_shoulder)
        
        # Left side
        left_lane = LaneComponent.create_standard_travel_lane("LEFT")
        left_lane.width = 3.3
        left_lane.cross_slope = -0.02
        
        left_shoulder = ShoulderComponent.create_gravel_shoulder("LEFT", 1.2)
        left_shoulder.cross_slope = -0.06
        
        left_ditch = DitchComponent.create_standard_ditch("LEFT")
        
        assembly.add_component(left_lane)
        assembly.add_component(left_shoulder, attach_to=left_lane)
        assembly.add_component(left_ditch, attach_to=left_shoulder)
        
        return assembly
    
    @staticmethod
    def create_aashto_local_road(name: str = "AASHTO Local Road") -> 'RoadAssembly':
        """
        AASHTO Local Road (30 mph design)
        
        Configuration:
        - 2 lanes @ 3.0m (10 ft) each
        - Gravel shoulders: 0.6m (2 ft) each side
        - Simple ditch sections
        - -2% cross slope
        
        Standard: AASHTO Green Book 2018, Chapter 5
        Design Speed: 30 mph (50 km/h)
        ADT: < 400 vpd
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='AASHTO',
            standard='AASHTO Green Book 2018',
            description='Minimum local road with minimal shoulders',
            typical_speed='30 mph (50 km/h)',
            design_vehicle='P (Passenger Car)',
            terrain='Any',
            functional_class='Local Road'
        )
        
        # Right side
        right_lane = LaneComponent.create_standard_travel_lane("RIGHT")
        right_lane.width = 3.0  # Minimum width
        right_lane.cross_slope = -0.02
        
        right_shoulder = ShoulderComponent.create_gravel_shoulder("RIGHT", 0.6)
        right_shoulder.cross_slope = -0.06
        
        right_ditch = DitchComponent.create_standard_ditch("RIGHT")
        right_ditch.depth = 0.3  # Shallow ditch
        
        assembly.add_component(right_lane)
        assembly.add_component(right_shoulder, attach_to=right_lane)
        assembly.add_component(right_ditch, attach_to=right_shoulder)
        
        # Left side
        left_lane = LaneComponent.create_standard_travel_lane("LEFT")
        left_lane.width = 3.0
        left_lane.cross_slope = -0.02
        
        left_shoulder = ShoulderComponent.create_gravel_shoulder("LEFT", 0.6)
        left_shoulder.cross_slope = -0.06
        
        left_ditch = DitchComponent.create_standard_ditch("LEFT")
        left_ditch.depth = 0.3
        
        assembly.add_component(left_lane)
        assembly.add_component(left_shoulder, attach_to=left_lane)
        assembly.add_component(left_ditch, attach_to=left_shoulder)
        
        return assembly
    
    # ==================== AUSTROADS TEMPLATES ====================
    
    @staticmethod
    def create_austroads_rural_single(name: str = "Austroads Rural Single Carriageway") -> 'RoadAssembly':
        """
        Austroads Rural Single Carriageway (100 km/h design)
        
        Configuration:
        - 2 lanes @ 3.5m each
        - Sealed shoulders: 2.5m each side
        - Safety barriers where required
        - -2.5% cross slope (Australian standard)
        
        Standard: Austroads Guide to Road Design Part 3
        Design Speed: 100 km/h
        AADT: < 3,000 vpd
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='Austroads',
            standard='Austroads Guide to Road Design Part 3',
            description='Rural single carriageway with sealed shoulders',
            typical_speed='100 km/h',
            design_vehicle='B-Double',
            terrain='Rural',
            functional_class='Rural Arterial'
        )
        
        # Right side
        right_lane = LaneComponent.create_standard_travel_lane("RIGHT")
        right_lane.width = 3.5
        right_lane.cross_slope = -0.025  # Australian standard
        
        right_shoulder = ShoulderComponent.create_paved_shoulder("RIGHT", 2.5)
        right_shoulder.cross_slope = -0.04
        
        right_ditch = DitchComponent.create_standard_ditch("RIGHT")
        right_ditch.foreslope = 4.0
        
        assembly.add_component(right_lane)
        assembly.add_component(right_shoulder, attach_to=right_lane)
        assembly.add_component(right_ditch, attach_to=right_shoulder)
        
        # Left side
        left_lane = LaneComponent.create_standard_travel_lane("LEFT")
        left_lane.width = 3.5
        left_lane.cross_slope = -0.025
        
        left_shoulder = ShoulderComponent.create_paved_shoulder("LEFT", 2.5)
        left_shoulder.cross_slope = -0.04
        
        left_ditch = DitchComponent.create_standard_ditch("LEFT")
        left_ditch.foreslope = 4.0
        
        assembly.add_component(left_lane)
        assembly.add_component(left_shoulder, attach_to=left_lane)
        assembly.add_component(left_ditch, attach_to=left_shoulder)
        
        return assembly
    
    @staticmethod
    def create_austroads_motorway(name: str = "Austroads Motorway/Freeway") -> 'RoadAssembly':
        """
        Austroads Motorway/Freeway (110 km/h design, one direction)
        
        Configuration:
        - Left shoulder: 1.0m paved (minimum)
        - 3 travel lanes @ 3.5m each
        - Right shoulder: 3.0m paved
        - Safety barriers on both sides
        - -2.5% cross slope
        
        Standard: Austroads Guide to Road Design Part 3
        Design Speed: 110 km/h
        AADT: > 15,000 vpd per direction
        """
        from components import LaneComponent, ShoulderComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='Austroads',
            standard='Austroads Guide to Road Design Part 3',
            description='Motorway/freeway with 3 lanes, one direction',
            typical_speed='110 km/h',
            design_vehicle='B-Double',
            terrain='Urban to Rural',
            functional_class='Motorway/Freeway'
        )
        
        # Inside (left) shoulder
        inside_shoulder = ShoulderComponent.create_paved_shoulder("LEFT", 1.0)
        inside_shoulder.cross_slope = -0.025
        
        # Lane 1 (inside)
        lane1 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane1.width = 3.5
        lane1.cross_slope = -0.025
        
        # Lane 2 (middle)
        lane2 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane2.width = 3.5
        lane2.cross_slope = -0.025
        
        # Lane 3 (outside)
        lane3 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane3.width = 3.5
        lane3.cross_slope = -0.025
        
        # Outside shoulder
        outside_shoulder = ShoulderComponent.create_paved_shoulder("RIGHT", 3.0)
        outside_shoulder.cross_slope = -0.04
        
        # Build from inside out
        assembly.add_component(inside_shoulder)
        assembly.add_component(lane1, attach_to=inside_shoulder)
        assembly.add_component(lane2, attach_to=lane1)
        assembly.add_component(lane3, attach_to=lane2)
        assembly.add_component(outside_shoulder, attach_to=lane3)
        
        return assembly
    
    @staticmethod
    def create_austroads_urban_arterial(name: str = "Austroads Urban Arterial") -> 'RoadAssembly':
        """
        Austroads Urban Arterial (60 km/h design)
        
        Configuration:
        - Mountable curb (both sides)
        - 2 lanes @ 3.3m each
        - Parking lane: 2.5m both sides
        - -2.5% cross slope
        
        Standard: Austroads Guide to Road Design Part 3
        Design Speed: 60 km/h
        AADT: 3,000-10,000 vpd
        """
        from components import LaneComponent, CurbComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='Austroads',
            standard='Austroads Guide to Road Design Part 3',
            description='Urban arterial with parking and mountable curbs',
            typical_speed='60 km/h',
            design_vehicle='Rigid Truck',
            terrain='Urban',
            functional_class='Urban Arterial'
        )
        
        # Right side
        right_travel = LaneComponent.create_standard_travel_lane("RIGHT")
        right_travel.width = 3.3
        right_travel.cross_slope = -0.025
        
        right_parking = LaneComponent.create_parking_lane("RIGHT")
        right_parking.width = 2.5
        right_parking.cross_slope = -0.025
        
        right_curb = CurbComponent.create_mountable_curb("RIGHT")
        
        assembly.add_component(right_travel)
        assembly.add_component(right_parking, attach_to=right_travel)
        assembly.add_component(right_curb, attach_to=right_parking)
        
        # Left side
        left_travel = LaneComponent.create_standard_travel_lane("LEFT")
        left_travel.width = 3.3
        left_travel.cross_slope = -0.025
        
        left_parking = LaneComponent.create_parking_lane("LEFT")
        left_parking.width = 2.5
        left_parking.cross_slope = -0.025
        
        left_curb = CurbComponent.create_mountable_curb("LEFT")
        
        assembly.add_component(left_travel)
        assembly.add_component(left_parking, attach_to=left_travel)
        assembly.add_component(left_curb, attach_to=left_parking)
        
        return assembly
    
    # ==================== UK DMRB TEMPLATES ====================
    
    @staticmethod
    def create_uk_single_carriageway(name: str = "UK Single Carriageway (DMRB)") -> 'RoadAssembly':
        """
        UK Single Carriageway (100 km/h / 60 mph design)
        
        Configuration:
        - 2 lanes @ 3.65m each (UK standard)
        - Hard strips: 1.0m each side
        - Verges with drainage
        - -2.5% crossfall (UK term)
        
        Standard: UK DMRB CD 127 (Cross-sections and headrooms)
        Design Speed: 100 km/h (60 mph)
        AADT: < 13,000 vpd
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='UK DMRB',
            standard='DMRB CD 127',
            description='Single carriageway with hard strips',
            typical_speed='100 km/h (60 mph)',
            design_vehicle='Articulated Lorry',
            terrain='Rural',
            functional_class='All-Purpose Single Carriageway'
        )
        
        # Right side
        right_lane = LaneComponent.create_standard_travel_lane("RIGHT")
        right_lane.width = 3.65  # UK standard
        right_lane.cross_slope = -0.025  # UK "crossfall"
        
        right_hardstrip = ShoulderComponent.create_paved_shoulder("RIGHT", 1.0)
        right_hardstrip.cross_slope = -0.025
        
        right_verge = DitchComponent.create_standard_ditch("RIGHT")
        right_verge.foreslope = 3.0  # UK verge slope
        
        assembly.add_component(right_lane)
        assembly.add_component(right_hardstrip, attach_to=right_lane)
        assembly.add_component(right_verge, attach_to=right_hardstrip)
        
        # Left side
        left_lane = LaneComponent.create_standard_travel_lane("LEFT")
        left_lane.width = 3.65
        left_lane.cross_slope = -0.025
        
        left_hardstrip = ShoulderComponent.create_paved_shoulder("LEFT", 1.0)
        left_hardstrip.cross_slope = -0.025
        
        left_verge = DitchComponent.create_standard_ditch("LEFT")
        left_verge.foreslope = 3.0
        
        assembly.add_component(left_lane)
        assembly.add_component(left_hardstrip, attach_to=left_lane)
        assembly.add_component(left_verge, attach_to=left_hardstrip)
        
        return assembly
    
    @staticmethod
    def create_uk_dual_carriageway(name: str = "UK Dual Carriageway (DMRB)") -> 'RoadAssembly':
        """
        UK Dual Carriageway (120 km/h / 70 mph design, one direction)
        
        Configuration:
        - Central reserve hard strip: 1.0m
        - 2 lanes @ 3.65m each
        - Hard shoulder: 3.3m (UK wide hard shoulder)
        - Verge with safety fence
        - -2.5% crossfall
        
        Standard: UK DMRB CD 127
        Design Speed: 120 km/h (70 mph)
        AADT: > 13,000 vpd per direction
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='UK DMRB',
            standard='DMRB CD 127',
            description='Dual carriageway with wide hard shoulder, one direction',
            typical_speed='120 km/h (70 mph)',
            design_vehicle='Articulated Lorry',
            terrain='Rural to Urban',
            functional_class='Dual Carriageway'
        )
        
        # Central reserve hard strip (left)
        central_hardstrip = ShoulderComponent.create_paved_shoulder("LEFT", 1.0)
        central_hardstrip.cross_slope = -0.025
        
        # Lane 1 (inside, near central reserve)
        lane1 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane1.width = 3.65
        lane1.cross_slope = -0.025
        
        # Lane 2 (outside)
        lane2 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane2.width = 3.65
        lane2.cross_slope = -0.025
        
        # Hard shoulder (right)
        hard_shoulder = ShoulderComponent.create_paved_shoulder("RIGHT", 3.3)
        hard_shoulder.cross_slope = -0.04
        
        # Verge
        verge = DitchComponent.create_standard_ditch("RIGHT")
        verge.foreslope = 3.0
        
        # Build from inside out
        assembly.add_component(central_hardstrip)
        assembly.add_component(lane1, attach_to=central_hardstrip)
        assembly.add_component(lane2, attach_to=lane1)
        assembly.add_component(hard_shoulder, attach_to=lane2)
        assembly.add_component(verge, attach_to=hard_shoulder)
        
        return assembly
    
    @staticmethod
    def create_uk_motorway(name: str = "UK Motorway (DMRB)") -> 'RoadAssembly':
        """
        UK Motorway (120 km/h / 70 mph design, one direction)
        
        Configuration:
        - Central reserve: 3.5m minimum
        - 3 lanes @ 3.65m each
        - Hard shoulder: 3.3m
        - Verge with drainage
        - -2.5% crossfall
        
        Standard: UK DMRB CD 127
        Design Speed: 120 km/h (70 mph)
        AADT: > 20,000 vpd per direction
        """
        from components import LaneComponent, ShoulderComponent, DitchComponent
        from native_ifc_cross_section import RoadAssembly
        
        assembly = RoadAssembly(name)
        assembly.metadata = TemplateMetadata(
            name=name,
            category='UK DMRB',
            standard='DMRB CD 127',
            description='Motorway with 3 lanes and hard shoulder, one direction',
            typical_speed='120 km/h (70 mph)',
            design_vehicle='Articulated Lorry',
            terrain='Any',
            functional_class='Motorway'
        )
        
        # Central reserve (simplified, left side)
        central_reserve = ShoulderComponent.create_paved_shoulder("LEFT", 1.75)  # Half of 3.5m
        central_reserve.cross_slope = -0.025
        
        # Lane 1 (inside, near central reserve)
        lane1 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane1.width = 3.65
        lane1.cross_slope = -0.025
        
        # Lane 2 (middle)
        lane2 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane2.width = 3.65
        lane2.cross_slope = -0.025
        
        # Lane 3 (outside)
        lane3 = LaneComponent.create_standard_travel_lane("RIGHT")
        lane3.width = 3.65
        lane3.cross_slope = -0.025
        
        # Hard shoulder
        hard_shoulder = ShoulderComponent.create_paved_shoulder("RIGHT", 3.3)
        hard_shoulder.cross_slope = -0.04
        
        # Verge
        verge = DitchComponent.create_standard_ditch("RIGHT")
        verge.foreslope = 3.0
        
        # Build from inside out
        assembly.add_component(central_reserve)
        assembly.add_component(lane1, attach_to=central_reserve)
        assembly.add_component(lane2, attach_to=lane1)
        assembly.add_component(lane3, attach_to=lane2)
        assembly.add_component(hard_shoulder, attach_to=lane3)
        assembly.add_component(verge, attach_to=hard_shoulder)
        
        return assembly
    
    # ==================== TEMPLATE REGISTRY ====================
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, callable]:
        """
        Get all available templates.
        
        Returns:
            Dictionary mapping template names to factory functions
        """
        return {
            # AASHTO Templates
            'AASHTO Two-Lane Rural': cls.create_aashto_two_lane_rural,
            'AASHTO Interstate': cls.create_aashto_interstate,
            'AASHTO Urban Arterial': cls.create_aashto_arterial_urban,
            'AASHTO Rural Collector': cls.create_aashto_collector,
            'AASHTO Local Road': cls.create_aashto_local_road,
            
            # Austroads Templates
            'Austroads Rural Single': cls.create_austroads_rural_single,
            'Austroads Motorway': cls.create_austroads_motorway,
            'Austroads Urban Arterial': cls.create_austroads_urban_arterial,
            
            # UK DMRB Templates
            'UK Single Carriageway': cls.create_uk_single_carriageway,
            'UK Dual Carriageway': cls.create_uk_dual_carriageway,
            'UK Motorway': cls.create_uk_motorway,
        }
    
    @classmethod
    def get_templates_by_category(cls, category: str) -> Dict[str, callable]:
        """
        Get templates filtered by category.
        
        Args:
            category: 'AASHTO', 'Austroads', 'UK DMRB', or 'All'
            
        Returns:
            Dictionary of templates in that category
        """
        all_templates = cls.get_all_templates()
        
        if category == 'All':
            return all_templates
        
        return {name: func for name, func in all_templates.items() 
                if category in name}
    
    @classmethod
    def list_templates(cls) -> List[Tuple[str, str, str]]:
        """
        List all templates with metadata.
        
        Returns:
            List of tuples: (name, category, description)
        """
        templates_info = []
        
        # We'll need to actually create each template to get metadata
        # In practice, we'd cache this or store metadata separately
        template_metadata = [
            ('AASHTO Two-Lane Rural', 'AASHTO', 'Standard two-lane rural highway with paved shoulders'),
            ('AASHTO Interstate', 'AASHTO', 'Interstate highway, one direction with full shoulders'),
            ('AASHTO Urban Arterial', 'AASHTO', 'Urban arterial with curb, gutter, and parking'),
            ('AASHTO Rural Collector', 'AASHTO', 'Rural collector with narrow lanes and gravel shoulders'),
            ('AASHTO Local Road', 'AASHTO', 'Minimum local road with minimal shoulders'),
            ('Austroads Rural Single', 'Austroads', 'Rural single carriageway with sealed shoulders'),
            ('Austroads Motorway', 'Austroads', 'Motorway/freeway with 3 lanes, one direction'),
            ('Austroads Urban Arterial', 'Austroads', 'Urban arterial with parking and mountable curbs'),
            ('UK Single Carriageway', 'UK DMRB', 'Single carriageway with hard strips'),
            ('UK Dual Carriageway', 'UK DMRB', 'Dual carriageway with wide hard shoulder, one direction'),
            ('UK Motorway', 'UK DMRB', 'Motorway with 3 lanes and hard shoulder, one direction'),
        ]
        
        return template_metadata


# ==================== BLENDER UI INTEGRATION ====================

class BLENDERCIVIL_OT_load_template(bpy.types.Operator):
    """Load a standard cross-section template"""
    bl_idname = "blendercivil.load_template"
    bl_label = "Load Template"
    bl_options = {'REGISTER', 'UNDO'}
    
    template_name: bpy.props.StringProperty(
        name="Template Name",
        description="Name of the template to load"
    )
    
    def execute(self, context):
        """Load the selected template."""
        try:
            templates = TemplateLibraryExpanded.get_all_templates()
            
            if self.template_name not in templates:
                self.report({'ERROR'}, f"Template '{self.template_name}' not found")
                return {'CANCELLED'}
            
            # Create the assembly from template
            factory_func = templates[self.template_name]
            assembly = factory_func()
            
            # Add to scene (this would integrate with existing system)
            # manager = get_manager()
            # manager.add_assembly(assembly)
            
            self.report({'INFO'}, f"Loaded template: {self.template_name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load template: {str(e)}")
            return {'CANCELLED'}


class BLENDERCIVIL_OT_template_browser(bpy.types.Operator):
    """Browse and select from template library"""
    bl_idname = "blendercivil.template_browser"
    bl_label = "Template Browser"
    bl_options = {'REGISTER', 'UNDO'}
    
    category_filter: bpy.props.EnumProperty(
        name="Category",
        description="Filter templates by category",
        items=[
            ('All', 'All Templates', 'Show all available templates'),
            ('AASHTO', 'AASHTO', 'American standards'),
            ('Austroads', 'Austroads', 'Australian/NZ standards'),
            ('UK DMRB', 'UK DMRB', 'UK Design Manual'),
        ],
        default='All'
    )
    
    def invoke(self, context, event):
        """Show template selection dialog."""
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        """Draw the template browser UI."""
        layout = self.layout
        
        # Category filter
        layout.prop(self, "category_filter")
        layout.separator()
        
        # List templates
        templates = TemplateLibraryExpanded.list_templates()
        filtered_templates = [t for t in templates if self.category_filter == 'All' or self.category_filter in t[0]]
        
        box = layout.box()
        box.label(text=f"Available Templates ({len(filtered_templates)}):", icon='PRESET')
        
        for name, category, description in filtered_templates:
            row = box.row()
            row.operator("blendercivil.load_template", text=name).template_name = name
            row.label(text=f"[{category}]")
    
    def execute(self, context):
        """Execute is called when dialog is confirmed."""
        return {'FINISHED'}


# ==================== MODULE SUMMARY ====================

def get_template_summary() -> str:
    """
    Get a summary of all available templates.
    
    Returns:
        Formatted string with template count and categories
    """
    templates = TemplateLibraryExpanded.list_templates()
    
    categories = {}
    for name, category, desc in templates:
        if category not in categories:
            categories[category] = []
        categories[category].append(name)
    
    summary = "BlenderCivil Cross-Section Template Library\n"
    summary += "=" * 50 + "\n\n"
    summary += f"Total Templates: {len(templates)}\n\n"
    
    for category, names in sorted(categories.items()):
        summary += f"{category} ({len(names)} templates):\n"
        for name in names:
            summary += f"  - {name}\n"
        summary += "\n"
    
    return summary


if __name__ == "__main__":
    # Print template summary
    print(get_template_summary())
