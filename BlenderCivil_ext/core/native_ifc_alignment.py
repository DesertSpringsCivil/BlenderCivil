# ==============================================================================
# BlenderCivil - Civil Engineering Tools for Blender
# Copyright (c) 2024-2025 Michael Yoder / Desert Springs Civil Engineering PLLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Primary Author: Michael Yoder
# Company: Desert Springs Civil Engineering PLLC
# ==============================================================================

"""
Native IFC Alignment (Updated)
PI-driven horizontal alignment - PIs are pure intersection points (NO RADIUS!)
"""

import bpy
import math
import ifcopenshell
import ifcopenshell.guid
from mathutils import Vector


class SimpleVector:
    def __init__(self, x, y=0):
        if isinstance(x, (list, tuple)):
            self.x = float(x[0])
            self.y = float(x[1])
        else:
            self.x = float(x)
            self.y = float(y)
    
    def __sub__(self, other):
        return SimpleVector(self.x - other.x, self.y - other.y)
    
    def __add__(self, other):
        return SimpleVector(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return SimpleVector(self.x * scalar, self.y * scalar)
    
    @property
    def length(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalized(self):
        l = self.length
        if l > 0:
            return SimpleVector(self.x / l, self.y / l)
        return SimpleVector(0, 0)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y

# ==================== NATIVE IFC ALIGNMENT ====================

class NativeIfcAlignment:
    """Native IFC alignment with PI-driven design - PIs are pure intersection points"""
    
    def __init__(self, ifc_file, name="New Alignment", alignment_entity=None):
        self.ifc = ifc_file
        self.alignment = None
        self.horizontal = None
        self.pis = []  # PIs have NO radius property!
        self.segments = []

        if alignment_entity:
            # Load from existing IFC alignment
            self.load_from_ifc(alignment_entity)
        else:
            # Create new alignment structure
            self.create_alignment_structure(name)

        # Register for updates
        self.auto_update = True
        from .complete_update_system import register_alignment
        register_alignment(self)

    @property
    def name(self):
        """Get alignment name from IFC entity."""
        if self.alignment:
            return self.alignment.Name
        return "Unnamed Alignment"

    def __del__(self):
        """Cleanup when alignment is deleted."""
        try:
            from .complete_update_system import unregister_alignment
            unregister_alignment(self)
        except:
            pass

    def create_alignment_structure(self, name):
        """Create IFC alignment hierarchy"""
        self.alignment = self.ifc.create_entity("IfcAlignment",
            GlobalId=ifcopenshell.guid.new(),
            Name=name,
            PredefinedType="USERDEFINED")

        self.horizontal = self.ifc.create_entity("IfcAlignmentHorizontal",
            GlobalId=ifcopenshell.guid.new())

        self.ifc.create_entity("IfcRelNests",
            GlobalId=ifcopenshell.guid.new(),
            Name="AlignmentToHorizontal",
            RelatingObject=self.alignment,
            RelatedObjects=[self.horizontal])

    def load_from_ifc(self, alignment_entity):
        """
        Load alignment from existing IFC entity.
        Reconstructs PIs and segments from saved IFC data.

        Args:
            alignment_entity: IfcAlignment entity from loaded IFC file
        """
        self.alignment = alignment_entity

        # Find horizontal alignment
        for rel in alignment_entity.IsNestedBy or []:
            for obj in rel.RelatedObjects:
                if obj.is_a("IfcAlignmentHorizontal"):
                    self.horizontal = obj
                    break

        if not self.horizontal:
            print(f"[Alignment] Warning: No horizontal alignment found for {alignment_entity.Name}")
            return

        # Load segments
        segments = []
        for rel in self.horizontal.IsNestedBy or []:
            for obj in rel.RelatedObjects:
                if obj.is_a("IfcAlignmentSegment"):
                    segments.append(obj)

        # Sort segments by order (if they have sequence numbers in names)
        # For now, trust the order from IFC file
        self.segments = segments

        # Reconstruct PIs from segments
        self._reconstruct_pis_from_segments()

        print(f"[Alignment] Loaded '{alignment_entity.Name}': {len(self.pis)} PIs, {len(self.segments)} segments")

    def _reconstruct_pis_from_segments(self):
        """
        Reconstruct PI list from IFC segments.

        CRITICAL: PIs are at the THEORETICAL INTERSECTION of tangent lines,
        not at BC/EC points!

        Strategy:
        - Group segments into pattern: [LINE, (optional CURVE), LINE, ...]
        - Calculate PI as intersection of tangent bearings
        - Attach curve data to interior PIs
        """
        if not self.segments:
            return

        self.pis = []

        # Parse segments into tangent/curve groups
        i = 0
        while i < len(self.segments):
            segment = self.segments[i]
            design_params = segment.DesignParameters

            if not design_params:
                i += 1
                continue

            if design_params.PredefinedType == "LINE":
                # This is a tangent segment
                direction = design_params.StartDirection
                start_point = design_params.StartPoint
                start_pos = SimpleVector(start_point.Coordinates[0], start_point.Coordinates[1])
                length = design_params.SegmentLength

                # Calculate tangent end point
                end_x = start_pos.x + length * math.cos(direction)
                end_y = start_pos.y + length * math.sin(direction)
                end_pos = SimpleVector(end_x, end_y)

                # Add PI at start of first tangent
                if len(self.pis) == 0:
                    pi_data = {
                        'id': 0,
                        'position': start_pos,
                        'ifc_point': self.ifc.create_entity("IfcCartesianPoint",
                            Coordinates=[float(start_pos.x), float(start_pos.y)])
                    }
                    self.pis.append(pi_data)

                # Check if there's a curve after this tangent
                has_curve = False
                if i + 1 < len(self.segments):
                    next_seg = self.segments[i + 1]
                    if next_seg.DesignParameters and next_seg.DesignParameters.PredefinedType == "CIRCULARARC":
                        has_curve = True
                        curve_seg = next_seg
                        curve_params = curve_seg.DesignParameters

                if has_curve and i + 2 < len(self.segments):
                    # We have: tangent1 -> curve -> tangent2
                    # Calculate PI as intersection of tangent1 and tangent2 directions

                    # Get tangent2 direction
                    tangent2_seg = self.segments[i + 2]
                    if tangent2_seg.DesignParameters and tangent2_seg.DesignParameters.PredefinedType == "LINE":
                        t2_dir = tangent2_seg.DesignParameters.StartDirection

                        # Calculate PI from curve geometry
                        # BC = end of tangent1, EC = start of tangent2
                        bc = end_pos  # End of current tangent
                        ec_point = curve_params.StartPoint  # Start of curve
                        # Actually, need to calculate EC from curve
                        curve_length = curve_params.SegmentLength
                        radius = abs(curve_params.StartRadiusOfCurvature)
                        deflection = curve_length / radius

                        # Calculate tangent length: T = R * tan(Δ/2)
                        tangent_length = radius * math.tan(deflection / 2)

                        # PI = BC + T * tangent1_direction
                        t1_unit = SimpleVector(math.cos(direction), math.sin(direction))
                        pi_pos = bc + t1_unit * tangent_length

                        # Add PI with curve data
                        pi_data = {
                            'id': len(self.pis),
                            'position': pi_pos,
                            'ifc_point': self.ifc.create_entity("IfcCartesianPoint",
                                Coordinates=[float(pi_pos.x), float(pi_pos.y)]),
                            'curve': {
                                'radius': radius,
                                'arc_length': curve_length,
                                'deflection': deflection,
                                'bc': bc,
                                'ec': None,  # Calculate later
                                'start_direction': direction,
                                'turn_direction': 'LEFT' if curve_params.StartRadiusOfCurvature > 0 else 'RIGHT'
                            }
                        }
                        self.pis.append(pi_data)

                        # Skip the curve and move to tangent2
                        i += 2
                    else:
                        # No tangent2, just add end of tangent1 as PI
                        pi_data = {
                            'id': len(self.pis),
                            'position': end_pos,
                            'ifc_point': self.ifc.create_entity("IfcCartesianPoint",
                                Coordinates=[float(end_x), float(end_y)])
                        }
                        self.pis.append(pi_data)
                        i += 1
                else:
                    # No curve, just add end of tangent as PI
                    pi_data = {
                        'id': len(self.pis),
                        'position': end_pos,
                        'ifc_point': self.ifc.create_entity("IfcCartesianPoint",
                            Coordinates=[float(end_x), float(end_y)])
                    }
                    self.pis.append(pi_data)
                    i += 1

            elif design_params.PredefinedType == "CIRCULARARC":
                # Standalone curve without being detected by tangent logic
                # This shouldn't happen in our workflow
                print(f"[Alignment] Warning: Standalone curve segment found at index {i}")
                i += 1
            else:
                i += 1

        print(f"[Alignment] Reconstructed {len(self.pis)} PIs from {len(self.segments)} segments")

    def add_pi(self, x, y):
        """Add PI to alignment - Pure intersection point, NO RADIUS!"""
        pi_data = {
            'id': len(self.pis),
            'position': SimpleVector(x, y),
            # NO RADIUS PROPERTY!
            'ifc_point': self.ifc.create_entity("IfcCartesianPoint",
                Coordinates=[float(x), float(y)])
        }
        
        self.pis.append(pi_data)
        self.regenerate_segments()
        return pi_data
    
    def regenerate_segments(self):
        """Regenerate IFC tangent segments from PIs
        
        Creates straight line segments between consecutive PIs.
        Curves are added separately via insert_curve_at_pi().
        """
        self.segments = []
        
        if len(self.pis) < 2:
            return
        
        # Create tangent lines between consecutive PIs
        for i in range(len(self.pis) - 1):
            curr_pi = self.pis[i]
            next_pi = self.pis[i + 1]
            
            # Simple tangent from this PI to next PI
            tangent_seg = self._create_tangent_segment(
                curr_pi['position'],
                next_pi['position']
            )
            self.segments.append(tangent_seg)
        
        self._update_ifc_nesting()
        
        print(f"[Alignment] Regenerated {len(self.segments)} tangent segments from {len(self.pis)} PIs")
    
    def _create_tangent_segment(self, start_pos, end_pos):
        """Create IFC tangent segment"""
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
    
    def insert_curve_at_pi(self, pi_index, radius):
        """Insert curve at specified PI with given radius
        
        This is called by the curve tool to add curves between tangents.
        
        Args:
            pi_index: Index of PI where curve should be inserted
            radius: Curve radius in meters
        
        Returns:
            Curve data dictionary
        """
        if pi_index <= 0 or pi_index >= len(self.pis) - 1:
            print(f"[Alignment] Cannot insert curve at PI {pi_index} (must be interior PI)")
            return None
        
        # Get the three PIs involved
        prev_pi = self.pis[pi_index - 1]
        curr_pi = self.pis[pi_index]
        next_pi = self.pis[pi_index + 1]
        
        # Calculate curve geometry
        curve_data = self._calculate_curve(
            prev_pi['position'],
            curr_pi['position'],
            next_pi['position'],
            radius
        )
        
        if not curve_data:
            print(f"[Alignment] Could not calculate curve at PI {pi_index}")
            return None
        
        # Store curve data with PI
        curr_pi['curve'] = curve_data
        
        # Regenerate all segments (now with curve consideration)
        self.regenerate_segments_with_curves()
        
        return curve_data
    
    def regenerate_segments_with_curves(self):
        """Regenerate segments considering curves at PIs

        This creates: Tangent → Curve → Tangent → Curve → Tangent
        where curves exist at PIs that have curve data.

        CRITICAL: Recalculates curve geometry from current PI positions!
        """
        self.segments = []

        if len(self.pis) < 2:
            return

        # STEP 1: Recalculate all curve geometries from current PI positions
        for i in range(len(self.pis)):
            pi = self.pis[i]

            # If this PI has a curve, recalculate its geometry
            if 'curve' in pi:
                # Need prev and next PI
                if i > 0 and i < len(self.pis) - 1:
                    prev_pi = self.pis[i - 1]
                    next_pi = self.pis[i + 1]

                    # Recalculate curve geometry with current PI positions
                    radius = pi['curve']['radius']  # Keep the original radius
                    updated_curve = self._calculate_curve(
                        prev_pi['position'],
                        pi['position'],
                        next_pi['position'],
                        radius
                    )

                    if updated_curve:
                        pi['curve'] = updated_curve
                    else:
                        # Curve is no longer valid (e.g., PIs became collinear)
                        del pi['curve']
                        print(f"[Alignment] Removed invalid curve at PI {i}")

        # STEP 2: Generate segments using updated curve data
        for i in range(len(self.pis) - 1):
            curr_pi = self.pis[i]
            next_pi = self.pis[i + 1]

            # Determine tangent start
            # If curr_pi has a curve, the previous tangent ended at BC,
            # and the curve went from BC to EC, so this tangent starts at EC
            if 'curve' in curr_pi:
                start_pos = curr_pi['curve']['ec']
            else:
                start_pos = curr_pi['position']

            # Determine tangent end
            # If next_pi has a curve, this tangent should end at BC (before the PI)
            if 'curve' in next_pi:
                end_pos = next_pi['curve']['bc']
            else:
                end_pos = next_pi['position']

            # Create tangent segment
            tangent = self._create_tangent_segment(start_pos, end_pos)
            self.segments.append(tangent)

            # Add curve at next PI if it exists
            # The curve goes from BC to EC around next_pi
            if 'curve' in next_pi:
                curve = self._create_curve_segment(next_pi['curve'], next_pi['id'])
                self.segments.append(curve)

        self._update_ifc_nesting()

        print(f"[Alignment] Regenerated {len(self.segments)} segments with curves")
    
    def _create_curve_segment(self, curve_data, pi_id=None):
        """Create IFC curve segment with SIGNED radius for turn direction"""
        name = f"Curve_{pi_id}" if pi_id is not None else f"Curve_{len(self.segments)}"
        
        # Use signed radius based on deflection angle
        signed_radius = curve_data['radius'] if curve_data['deflection'] > 0 else -curve_data['radius']
        
        segment = self.ifc.create_entity("IfcAlignmentSegment",
            GlobalId=ifcopenshell.guid.new(),
            Name=name,
            DesignParameters=self.ifc.create_entity(
                "IfcAlignmentHorizontalSegment",
                StartPoint=self.ifc.create_entity("IfcCartesianPoint",
                    Coordinates=[float(curve_data['bc'].x), float(curve_data['bc'].y)]),
                StartDirection=float(curve_data['start_direction']),
                StartRadiusOfCurvature=float(signed_radius),
                EndRadiusOfCurvature=float(signed_radius),
                SegmentLength=float(curve_data['arc_length']),
                PredefinedType="CIRCULARARC"
            )
        )
        return segment
    
    def _calculate_curve(self, prev_pi, curr_pi, next_pi, radius):
        """Calculate curve geometry from PIs with SIGNED deflection angle"""
        t1 = (curr_pi - prev_pi).normalized()
        t2 = (next_pi - curr_pi).normalized()
        
        # Calculate SIGNED deflection angle
        angle1 = math.atan2(t1.y, t1.x)
        angle2 = math.atan2(t2.y, t2.x)
        
        deflection = angle2 - angle1
        
        # Normalize to [-π, π]
        if deflection > math.pi:
            deflection -= 2 * math.pi
        elif deflection < -math.pi:
            deflection += 2 * math.pi
        
        # Check if deflection is too small
        if abs(deflection) < 0.001:
            return None
        
        # Calculate curve geometry
        tangent_length = radius * math.tan(abs(deflection) / 2)
        bc = curr_pi - t1 * tangent_length
        ec = curr_pi + t2 * tangent_length
        arc_length = radius * abs(deflection)
        
        return {
            'bc': bc,
            'ec': ec,
            'radius': radius,
            'arc_length': arc_length,
            'deflection': deflection,
            'start_direction': angle1,
            'turn_direction': 'LEFT' if deflection > 0 else 'RIGHT'
        }
    
    def _update_ifc_nesting(self):
        """Update IFC nesting relationships"""
        if self.segments:
            # Remove old nesting
            for rel in self.horizontal.IsNestedBy or []:
                self.ifc.remove(rel)
            
            # Create new nesting
            self.ifc.create_entity("IfcRelNests",
                GlobalId=ifcopenshell.guid.new(),
                Name="HorizontalToSegments",
                RelatingObject=self.horizontal,
                RelatedObjects=self.segments
            )
