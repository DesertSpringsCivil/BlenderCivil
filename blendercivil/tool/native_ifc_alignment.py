"""
Native IFC Alignment with PI-Driven Design
Sprint 1, Day 1 - Core Implementation

This module implements professional PI-driven horizontal alignment design
with TRUE native IFC storage.
"""

import ifcopenshell
import ifcopenshell.guid
import math

# Simple Vector class for testing (replaces Blender's mathutils)
class Vector:
    def __init__(self, coords):
        self.x = coords[0]
        self.y = coords[1]
    
    def __sub__(self, other):
        return Vector((self.x - other.x, self.y - other.y))
    
    def __add__(self, other):
        return Vector((self.x + other.x, self.y + other.y))
    
    def __mul__(self, scalar):
        return Vector((self.x * scalar, self.y * scalar))
    
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    
    @property
    def length(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalized(self):
        length = self.length
        if length == 0:
            return Vector((0, 0))
        return Vector((self.x / length, self.y / length))
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y


class NativeIfcAlignment:
    """Native IFC alignment with PI-driven design
    
    This class manages a complete IFC alignment with:
    - PI-based design methodology (like Civil 3D/OpenRoads)
    - Automatic tangent and curve generation
    - Native IFC 4.3 storage
    - Blender visualization support
    """
    
    def __init__(self, ifc_file, name="New Alignment"):
        """Initialize native IFC alignment
        
        Args:
            ifc_file: IfcOpenShell file object
            name: Name for the alignment
        """
        self.ifc = ifc_file
        self.alignment = None
        self.horizontal = None
        self.pis = []  # List of PI data dictionaries
        self.segments = []  # List of IFC segment entities
        
        # Create the IFC structure
        self.create_alignment_structure(name)
    
    def create_alignment_structure(self, name):
        """Create complete IFC alignment hierarchy
        
        Creates:
        - IfcAlignment (main entity)
        - IfcAlignmentHorizontal (horizontal component)
        - IfcRelNests (relationship)
        """
        # Create IfcAlignment
        self.alignment = self.ifc.create_entity("IfcAlignment",
            GlobalId=ifcopenshell.guid.new(),
            Name=name,
            Description="Native IFC alignment created with BlenderCivil",
            PredefinedType="USERDEFINED"
        )
        
        # Create IfcAlignmentHorizontal
        self.horizontal = self.ifc.create_entity("IfcAlignmentHorizontal",
            GlobalId=ifcopenshell.guid.new()
        )
        
        # Create nesting relationship
        self.ifc.create_entity("IfcRelNests",
            GlobalId=ifcopenshell.guid.new(),
            Name="AlignmentToHorizontal",
            Description="Horizontal alignment nested under alignment",
            RelatingObject=self.alignment,
            RelatedObjects=[self.horizontal]
        )
        
        print(f"[OK] Created native IFC alignment: '{name}'")
        print(f"   - IfcAlignment: {self.alignment.GlobalId}")
        print(f"   - IfcAlignmentHorizontal: {self.horizontal.GlobalId}")
    
    def add_pi(self, x, y, radius=0.0):
        """Add Point of Intersection (PI) to alignment
        
        Args:
            x: X coordinate (local)
            y: Y coordinate (local)
            radius: Curve radius at this PI (0 = no curve)
        
        Returns:
            dict: PI data including IFC point entity
        """
        pi_id = len(self.pis)
        
        # Create IFC point entity
        ifc_point = self.ifc.create_entity("IfcCartesianPoint",
            Coordinates=[float(x), float(y)]
        )
        
        # Store PI data
        pi_data = {
            'id': pi_id,
            'position': Vector((x, y)),
            'radius': radius,
            'ifc_point': ifc_point
        }
        
        self.pis.append(pi_data)
        
        print(f"[OK] Added PI {pi_id:03d} at ({x:.2f}, {y:.2f}), radius={radius:.2f}m")
        
        # Regenerate segments from PIs
        self.regenerate_segments()
        
        return pi_data
    
    def regenerate_segments(self):
        """Regenerate all IFC segments from current PIs
        
        This is the CORE of PI-driven design:
        - Takes list of PIs
        - Automatically generates tangents
        - Automatically inserts curves at PIs with radius > 0
        - Creates proper IFC segment entities
        """
        if len(self.pis) < 2:
            print("   [WARNING] Need at least 2 PIs to create segments")
            return
        
        print(f"Regenerating segments from {len(self.pis)} PIs...")
        
        # Clear existing segments (in production, would properly remove from IFC)
        self.segments = []
        
        current_station = 0.0
        
        # Process each PI
        for i in range(len(self.pis)):
            if i == 0:
                # First PI - create initial tangent to next PI
                if len(self.pis) > 1:
                    seg = self._create_tangent_segment(
                        self.pis[0]['position'],
                        self.pis[1]['position'],
                        current_station
                    )
                    self.segments.append(seg)
                    current_station += seg.DesignParameters.SegmentLength
                    print(f"   Segment {len(self.segments)-1}: LINE {seg.DesignParameters.SegmentLength:.2f}m")
            
            elif i == len(self.pis) - 1:
                # Last PI - no more segments after this
                pass
            
            else:
                # Middle PI - check if curve is needed
                prev_pi = self.pis[i-1]['position']
                curr_pi = self.pis[i]['position']
                next_pi = self.pis[i+1]['position']
                radius = self.pis[i]['radius']
                
                if radius > 0:
                    # Calculate curve geometry
                    curve_data = self._calculate_curve(prev_pi, curr_pi, next_pi, radius)
                    
                    if curve_data:
                        # Create curve segment
                        curve_seg = self._create_curve_segment(curve_data, current_station)
                        self.segments.append(curve_seg)
                        current_station += curve_seg.DesignParameters.SegmentLength
                        print(f"   Segment {len(self.segments)-1}: CIRCULARARC {curve_seg.DesignParameters.SegmentLength:.2f}m, R={radius:.2f}m")
                        
                        # Create exit tangent
                        exit_seg = self._create_tangent_segment(
                            curve_data['ec'],
                            next_pi,
                            current_station
                        )
                        self.segments.append(exit_seg)
                        current_station += exit_seg.DesignParameters.SegmentLength
                        print(f"   Segment {len(self.segments)-1}: LINE {exit_seg.DesignParameters.SegmentLength:.2f}m")
                else:
                    # No curve - just continue tangent
                    # (handled by next iteration)
                    pass
        
        # Update IFC nesting relationships
        self._update_ifc_nesting()
        
        print(f"[OK] Generated {len(self.segments)} segments, total length: {current_station:.2f}m")
    
    def _create_tangent_segment(self, start_pos, end_pos, start_station):
        """Create IFC tangent (LINE) segment
        
        Args:
            start_pos: Vector start position
            end_pos: Vector end position
            start_station: Starting station
        
        Returns:
            IfcAlignmentSegment entity
        """
        direction = end_pos - start_pos
        length = direction.length
        angle = math.atan2(direction.y, direction.x)
        
        segment = self.ifc.create_entity("IfcAlignmentSegment",
            GlobalId=ifcopenshell.guid.new(),
            Name=f"Tangent_{len(self.segments)}",
            DesignParameters=self.ifc.create_entity(
                "IfcAlignmentHorizontalSegment",
                StartPoint=self.ifc.create_entity("IfcCartesianPoint",
                    Coordinates=[float(start_pos.x), float(start_pos.y)]),
                StartDirection=float(angle),
                StartRadiusOfCurvature=0.0,
                EndRadiusOfCurvature=0.0,
                SegmentLength=float(length),
                PredefinedType="LINE"
            )
        )
        
        return segment
    
    def _create_curve_segment(self, curve_data, start_station):
        """Create IFC curve (CIRCULARARC) segment
        
        Args:
            curve_data: Dictionary with curve geometry
            start_station: Starting station
        
        Returns:
            IfcAlignmentSegment entity
        """
        segment = self.ifc.create_entity("IfcAlignmentSegment",
            GlobalId=ifcopenshell.guid.new(),
            Name=f"Curve_{len(self.segments)}",
            DesignParameters=self.ifc.create_entity(
                "IfcAlignmentHorizontalSegment",
                StartPoint=self.ifc.create_entity("IfcCartesianPoint",
                    Coordinates=[float(curve_data['bc'].x), float(curve_data['bc'].y)]),
                StartDirection=float(curve_data['start_direction']),
                StartRadiusOfCurvature=float(curve_data['radius']),
                EndRadiusOfCurvature=float(curve_data['radius']),
                SegmentLength=float(curve_data['arc_length']),
                PredefinedType="CIRCULARARC"
            )
        )
        
        return segment
    
    def _calculate_curve(self, prev_pi, curr_pi, next_pi, radius):
        """Calculate curve geometry from three PIs
        
        This is CIVIL ENGINEERING MATH:
        - Calculate deflection angle
        - Calculate tangent lengths
        - Calculate BC and EC points
        - Calculate arc length
        
        Args:
            prev_pi: Previous PI position
            curr_pi: Current PI position
            next_pi: Next PI position
            radius: Curve radius
        
        Returns:
            dict: Curve geometry data or None if invalid
        """
        # Get tangent vectors
        t1 = (curr_pi - prev_pi).normalized()
        t2 = (next_pi - curr_pi).normalized()
        
        # Calculate deflection angle (intersection angle)
        dot_product = max(-1, min(1, t1.dot(t2)))
        deflection = math.acos(dot_product)
        
        # Check if nearly straight
        if deflection < 0.001:  # ~0.06 degrees
            print(f"   [WARNING] Deflection too small at PI, skipping curve")
            return None
        
        # Calculate tangent length
        tangent_length = radius * math.tan(deflection / 2)
        
        # Calculate BC (Beginning of Curve) and EC (End of Curve)
        bc = curr_pi - t1 * tangent_length
        ec = curr_pi + t2 * tangent_length
        
        # Calculate arc length
        arc_length = radius * deflection
        
        # Start direction for curve
        start_direction = math.atan2(t1.y, t1.x)
        
        return {
            'bc': bc,
            'ec': ec,
            'radius': radius,
            'arc_length': arc_length,
            'deflection': deflection,
            'tangent_length': tangent_length,
            'start_direction': start_direction
        }
    
    def _update_ifc_nesting(self):
        """Update IFC nesting relationships
        
        Creates IfcRelNests to connect segments to horizontal alignment
        """
        if self.segments:
            # Create nesting relationship
            self.ifc.create_entity("IfcRelNests",
                GlobalId=ifcopenshell.guid.new(),
                Name="HorizontalToSegments",
                Description="Segments nested under horizontal alignment",
                RelatingObject=self.horizontal,
                RelatedObjects=self.segments
            )
    
    def get_stationing(self):
        """Get stationing information for all segments
        
        Returns:
            list: List of dicts with station, segment info
        """
        stationing = []
        current_station = 0.0
        
        for i, segment in enumerate(self.segments):
            params = segment.DesignParameters
            
            stationing.append({
                'station': current_station,
                'segment_type': params.PredefinedType,
                'length': params.SegmentLength,
                'start_point': params.StartPoint.Coordinates,
                'start_direction': params.StartDirection,
                'radius': params.StartRadiusOfCurvature,
                'segment': segment
            })
            
            current_station += params.SegmentLength
        
        return stationing
    
    def get_info(self):
        """Get alignment information summary
        
        Returns:
            dict: Summary of alignment data
        """
        total_length = sum(seg.DesignParameters.SegmentLength for seg in self.segments)
        
        return {
            'name': self.alignment.Name,
            'global_id': self.alignment.GlobalId,
            'num_pis': len(self.pis),
            'num_segments': len(self.segments),
            'total_length': total_length,
            'segments': self.get_stationing()
        }


# Example usage
if __name__ == "__main__":
    import ifcopenshell
    
    # Create IFC file
    ifc = ifcopenshell.file(schema="IFC4X3")
    
    # Create project
    project = ifc.create_entity("IfcProject",
        GlobalId=ifcopenshell.guid.new(),
        Name="BlenderCivil Sprint 1 Test"
    )
    
    # Create site
    site = ifc.create_entity("IfcSite",
        GlobalId=ifcopenshell.guid.new(),
        Name="Test Site"
    )
    
    # Create alignment with PIs
    print("\n" + "="*60)
    print("SPRINT 1 DAY 1: NATIVE IFC ALIGNMENT TEST")
    print("="*60 + "\n")
    
    alignment = NativeIfcAlignment(ifc, "Highway 101 Realignment")
    
    print("\nAdding PIs:")
    alignment.add_pi(0, 0, radius=0)        # Start point, no curve
    alignment.add_pi(100, 0, radius=150)    # PI with 150m radius curve
    alignment.add_pi(200, 100, radius=200)  # PI with 200m radius curve
    alignment.add_pi(300, 100, radius=0)    # End point, no curve
    
    print("\nAlignment Summary:")
    info = alignment.get_info()
    print(f"   Name: {info['name']}")
    print(f"   PIs: {info['num_pis']}")
    print(f"   Segments: {info['num_segments']}")
    print(f"   Total Length: {info['total_length']:.2f}m")
    
    print("\nSegment Details:")
    for i, seg_info in enumerate(info['segments']):
        print(f"   [{i}] Station {seg_info['station']:.2f}: {seg_info['segment_type']} "
              f"{seg_info['length']:.2f}m, R={seg_info['radius']:.2f}m")
    
    # Save IFC file
    filepath = "/home/claude/sprint1_day1_test.ifc"
    ifc.write(filepath)
    print(f"\n[OK] Saved to: {filepath}")
    print(f"   Total IFC entities: {len(list(ifc))}")
    print("\n" + "="*60)
    print("DAY 1 CORE IMPLEMENTATION: COMPLETE!")
    print("="*60 + "\n")
