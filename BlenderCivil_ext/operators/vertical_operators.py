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
Vertical Alignment Operators
Handles all vertical alignment operations in Blender
"""

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, StringProperty, IntProperty


class BC_OT_AddPVI(Operator):
    """Add a new PVI to the vertical alignment"""
    bl_idname = "bc.add_pvi"
    bl_label = "Add PVI"
    bl_description = "Add a Point of Vertical Intersection"
    bl_options = {'REGISTER', 'UNDO'}
    
    station: FloatProperty(
        name="Station",
        description="Station location (m)",
        default=0.0,
        min=0.0,
    )
    
    elevation: FloatProperty(
        name="Elevation",
        description="Elevation at station (m)",
        default=0.0,
    )
    
    curve_length: FloatProperty(
        name="Curve Length",
        description="Vertical curve length (m)",
        default=0.0,
        min=0.0,
    )
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        
        # Check if station already exists
        for pvi in vertical.pvis:
            if abs(pvi.station - self.station) < 0.001:
                self.report({'ERROR'}, f"PVI already exists at station {self.station:.3f}m")
                return {'CANCELLED'}
        
        # Add new PVI
        pvi = vertical.pvis.add()
        pvi.station = self.station
        pvi.elevation = self.elevation
        pvi.curve_length = self.curve_length
        pvi.design_speed = vertical.design_speed
        
        # Sort PVIs by station
        pvis_list = list(vertical.pvis)
        pvis_list.sort(key=lambda p: p.station)
        vertical.pvis.clear()
        for sorted_pvi in pvis_list:
            new_pvi = vertical.pvis.add()
            new_pvi.station = sorted_pvi.station
            new_pvi.elevation = sorted_pvi.elevation
            new_pvi.curve_length = sorted_pvi.curve_length
            new_pvi.design_speed = sorted_pvi.design_speed
        
        # Trigger recalculation
        bpy.ops.bc.calculate_grades()
        bpy.ops.bc.generate_segments()
        bpy.ops.bc.validate_vertical()
        
        self.report({'INFO'}, f"Added PVI at station {self.station:.3f}m")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BC_OT_RemovePVI(Operator):
    """Remove the selected PVI"""
    bl_idname = "bc.remove_pvi"
    bl_label = "Remove PVI"
    bl_description = "Remove the selected Point of Vertical Intersection"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) > 0 and vertical.active_pvi_index >= 0
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        
        if vertical.active_pvi_index < len(vertical.pvis):
            station = vertical.pvis[vertical.active_pvi_index].station
            vertical.pvis.remove(vertical.active_pvi_index)
            
            # Adjust active index
            if vertical.active_pvi_index >= len(vertical.pvis):
                vertical.active_pvi_index = max(0, len(vertical.pvis) - 1)
            
            # Trigger recalculation
            bpy.ops.bc.calculate_grades()
            bpy.ops.bc.generate_segments()
            bpy.ops.bc.validate_vertical()
            
            self.report({'INFO'}, f"Removed PVI at station {station:.3f}m")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No PVI selected")
            return {'CANCELLED'}


class BC_OT_EditPVI(Operator):
    """Edit the selected PVI"""
    bl_idname = "bc.edit_pvi"
    bl_label = "Edit PVI"
    bl_description = "Edit the selected Point of Vertical Intersection"
    bl_options = {'REGISTER', 'UNDO'}
    
    station: FloatProperty(
        name="Station",
        description="Station location (m)",
        default=0.0,
        min=0.0,
    )
    
    elevation: FloatProperty(
        name="Elevation",
        description="Elevation at station (m)",
        default=0.0,
    )
    
    curve_length: FloatProperty(
        name="Curve Length",
        description="Vertical curve length (m)",
        default=0.0,
        min=0.0,
    )
    
    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) > 0 and vertical.active_pvi_index >= 0
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        
        if vertical.active_pvi_index < len(vertical.pvis):
            pvi = vertical.pvis[vertical.active_pvi_index]
            old_station = pvi.station
            
            # Update PVI
            pvi.station = self.station
            pvi.elevation = self.elevation
            pvi.curve_length = self.curve_length
            
            # Re-sort if station changed
            if abs(old_station - self.station) > 0.001:
                pvis_list = list(vertical.pvis)
                pvis_list.sort(key=lambda p: p.station)
                vertical.pvis.clear()
                for sorted_pvi in pvis_list:
                    new_pvi = vertical.pvis.add()
                    new_pvi.station = sorted_pvi.station
                    new_pvi.elevation = sorted_pvi.elevation
                    new_pvi.curve_length = sorted_pvi.curve_length
                    new_pvi.design_speed = sorted_pvi.design_speed
            
            # Trigger recalculation
            bpy.ops.bc.calculate_grades()
            bpy.ops.bc.generate_segments()
            bpy.ops.bc.validate_vertical()
            
            self.report({'INFO'}, f"Updated PVI at station {self.station:.3f}m")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No PVI selected")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        vertical = context.scene.bc_vertical
        
        if vertical.active_pvi_index < len(vertical.pvis):
            pvi = vertical.pvis[vertical.active_pvi_index]
            self.station = pvi.station
            self.elevation = pvi.elevation
            self.curve_length = pvi.curve_length
            return context.window_manager.invoke_props_dialog(self)
        else:
            return {'CANCELLED'}


class BC_OT_DesignVerticalCurve(Operator):
    """Design vertical curve using K-value"""
    bl_idname = "bc.design_vertical_curve"
    bl_label = "Design Curve"
    bl_description = "Calculate curve length from K-value and grade change"
    bl_options = {'REGISTER', 'UNDO'}
    
    k_value: FloatProperty(
        name="K-Value",
        description="Curve parameter (m/%)",
        default=30.0,
        min=0.0,
    )
    
    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) > 0 and vertical.active_pvi_index >= 0
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        
        if vertical.active_pvi_index < len(vertical.pvis):
            pvi = vertical.pvis[vertical.active_pvi_index]
            
            # Ensure grades are calculated
            if pvi.grade_in == 0 and pvi.grade_out == 0:
                self.report({'WARNING'}, "Calculate grades first (need adjacent PVIs)")
                return {'CANCELLED'}
            
            # Calculate grade change (A-value)
            grade_change = abs(pvi.grade_out - pvi.grade_in) * 100  # Convert to percent
            
            if grade_change < 0.01:
                self.report({'WARNING'}, "Grade change too small for curve design")
                return {'CANCELLED'}
            
            # Calculate curve length: L = K × A
            curve_length = self.k_value * grade_change
            pvi.curve_length = curve_length
            pvi.k_value = self.k_value
            
            # Determine curve type
            if pvi.grade_in > pvi.grade_out:
                curve_type = "Crest"
                min_k = vertical.min_k_crest
            else:
                curve_type = "Sag"
                min_k = vertical.min_k_sag
            
            pvi.curve_type_display = curve_type
            
            # Check against minimum
            if self.k_value < min_k:
                self.report({'WARNING'}, 
                    f"{curve_type} curve K={self.k_value:.1f} < minimum {min_k:.1f}")
            
            # Trigger recalculation
            bpy.ops.bc.generate_segments()
            bpy.ops.bc.validate_vertical()
            
            self.report({'INFO'}, 
                f"Designed {curve_type} curve: L={curve_length:.2f}m, K={self.k_value:.1f}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No PVI selected")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        vertical = context.scene.bc_vertical
        
        if vertical.active_pvi_index < len(vertical.pvis):
            pvi = vertical.pvis[vertical.active_pvi_index]
            
            # Determine curve type and suggest appropriate K-value
            if pvi.grade_in > pvi.grade_out:
                self.k_value = max(vertical.min_k_crest, 30.0)
            else:
                self.k_value = max(vertical.min_k_sag, 20.0)
            
            return context.window_manager.invoke_props_dialog(self)
        else:
            return {'CANCELLED'}


class BC_OT_CalculateGrades(Operator):
    """Calculate grades between all PVIs"""
    bl_idname = "bc.calculate_grades"
    bl_label = "Calculate Grades"
    bl_description = "Calculate grades between all PVIs"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) >= 2
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        pvis = list(vertical.pvis)
        
        if len(pvis) < 2:
            self.report({'WARNING'}, "Need at least 2 PVIs to calculate grades")
            return {'CANCELLED'}
        
        # Calculate grades between consecutive PVIs
        for i in range(len(pvis) - 1):
            pvi1 = pvis[i]
            pvi2 = pvis[i + 1]
            
            # Calculate grade
            rise = pvi2.elevation - pvi1.elevation
            run = pvi2.station - pvi1.station
            
            if run == 0:
                self.report({'ERROR'}, f"PVIs at same station: {pvi1.station:.3f}m")
                return {'CANCELLED'}
            
            grade = rise / run  # Decimal grade
            
            # Set grades
            pvi1.grade_out = grade
            pvi2.grade_in = grade
        
        # Calculate grade changes and K-values
        for i in range(1, len(pvis) - 1):
            pvi = pvis[i]
            pvi.grade_change = abs(pvi.grade_out - pvi.grade_in)
            
            # Calculate K-value if curve exists
            if pvi.curve_length > 0:
                grade_change_percent = pvi.grade_change * 100
                if grade_change_percent > 0.01:
                    pvi.k_value = pvi.curve_length / grade_change_percent
                    
                    # Determine curve type
                    if pvi.grade_in > pvi.grade_out:
                        pvi.curve_type_display = "Crest"
                    else:
                        pvi.curve_type_display = "Sag"
                else:
                    pvi.k_value = 0.0
                    pvi.curve_type_display = "None"
            else:
                pvi.k_value = 0.0
                pvi.curve_type_display = "None"
        
        # Update statistics
        if len(pvis) > 0:
            vertical.total_length = pvis[-1].station - pvis[0].station
            vertical.elevation_min = min(p.elevation for p in pvis)
            vertical.elevation_max = max(p.elevation for p in pvis)
        
        self.report({'INFO'}, f"Calculated grades for {len(pvis)} PVIs")
        return {'FINISHED'}


class BC_OT_GenerateSegments(Operator):
    """Generate vertical segments from PVIs"""
    bl_idname = "bc.generate_segments"
    bl_label = "Generate Segments"
    bl_description = "Generate tangent and curve segments from PVIs"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) >= 2
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        pvis = list(vertical.pvis)
        
        if len(pvis) < 2:
            self.report({'WARNING'}, "Need at least 2 PVIs to generate segments")
            return {'CANCELLED'}
        
        # Clear existing segments
        vertical.segments.clear()
        
        current_station = pvis[0].station
        current_elevation = pvis[0].elevation
        
        for i in range(len(pvis) - 1):
            pvi = pvis[i]
            next_pvi = pvis[i + 1]
            grade = pvi.grade_out
            
            # Check if PVI has a curve
            if pvi.curve_length > 0 and i > 0:
                # Tangent before curve
                curve_length = pvi.curve_length
                bvc_station = pvi.station - curve_length / 2
                
                if bvc_station > current_station:
                    # Add tangent segment
                    seg = vertical.segments.add()
                    seg.segment_type = "TANGENT"
                    seg.start_station = current_station
                    seg.end_station = bvc_station
                    seg.length = bvc_station - current_station
                    seg.start_elevation = current_elevation
                    seg.end_elevation = current_elevation + (bvc_station - current_station) * grade
                    seg.grade = grade
                    
                    current_station = bvc_station
                    current_elevation = seg.end_elevation
                
                # Add curve segment
                evc_station = pvi.station + curve_length / 2
                seg = vertical.segments.add()
                seg.segment_type = "CURVE"
                seg.start_station = current_station
                seg.end_station = evc_station
                seg.length = curve_length
                seg.start_elevation = current_elevation
                # Approximate end elevation (simplified)
                seg.end_elevation = current_elevation + curve_length * (grade + next_pvi.grade_in) / 2
                seg.grade = (grade + next_pvi.grade_in) / 2  # Average grade
                
                current_station = evc_station
                current_elevation = seg.end_elevation
        
        # Final tangent to last PVI
        if current_station < pvis[-1].station:
            seg = vertical.segments.add()
            seg.segment_type = "TANGENT"
            seg.start_station = current_station
            seg.end_station = pvis[-1].station
            seg.length = pvis[-1].station - current_station
            seg.start_elevation = current_elevation
            seg.end_elevation = pvis[-1].elevation
            seg.grade = (pvis[-1].elevation - current_elevation) / (pvis[-1].station - current_station)
        
        self.report({'INFO'}, f"Generated {len(vertical.segments)} segments")
        return {'FINISHED'}


class BC_OT_ValidateVertical(Operator):
    """Validate vertical alignment against design standards"""
    bl_idname = "bc.validate_vertical"
    bl_label = "Validate"
    bl_description = "Validate vertical alignment against design standards"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) >= 2
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        pvis = list(vertical.pvis)
        
        errors = []
        warnings = []
        
        # Check minimum PVIs
        if len(pvis) < 2:
            errors.append("Need at least 2 PVIs")
            vertical.is_valid = False
            vertical.validation_message = "; ".join(errors)
            return {'FINISHED'}
        
        # Check station ordering
        for i in range(len(pvis) - 1):
            if pvis[i].station >= pvis[i + 1].station:
                errors.append(f"PVI {i+1} station not increasing")
        
        # Check K-values against minimums
        for i, pvi in enumerate(pvis):
            if pvi.curve_length > 0:
                if pvi.k_value < 0.01:
                    warnings.append(f"PVI {i+1}: K-value not calculated")
                elif pvi.curve_type_display == "Crest":
                    if pvi.k_value < vertical.min_k_crest:
                        warnings.append(
                            f"PVI {i+1}: Crest K={pvi.k_value:.1f} < min {vertical.min_k_crest:.1f}"
                        )
                elif pvi.curve_type_display == "Sag":
                    if pvi.k_value < vertical.min_k_sag:
                        warnings.append(
                            f"PVI {i+1}: Sag K={pvi.k_value:.1f} < min {vertical.min_k_sag:.1f}"
                        )
        
        # Update validation status
        if len(errors) > 0:
            vertical.is_valid = False
            vertical.validation_message = "ERRORS: " + "; ".join(errors)
            self.report({'ERROR'}, vertical.validation_message)
        elif len(warnings) > 0:
            vertical.is_valid = True
            vertical.validation_message = "WARNINGS: " + "; ".join(warnings)
            self.report({'WARNING'}, vertical.validation_message)
        else:
            vertical.is_valid = True
            vertical.validation_message = "All checks passed"
            self.report({'INFO'}, "Validation passed")
        
        return {'FINISHED'}


class BC_OT_QueryStation(Operator):
    """Query elevation and grade at a station"""
    bl_idname = "bc.query_station"
    bl_label = "Query Station"
    bl_description = "Get elevation and grade at specified station"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) >= 2
    
    def execute(self, context):
        vertical = context.scene.bc_vertical
        station = vertical.query_station
        
        # Find segment containing station
        found = False
        for seg in vertical.segments:
            if seg.start_station <= station <= seg.end_station:
                found = True
                
                # Calculate elevation and grade
                x = station - seg.start_station
                length = seg.length
                
                if seg.segment_type == "TANGENT":
                    # Linear interpolation
                    t = x / length if length > 0 else 0
                    elevation = seg.start_elevation + t * (seg.end_elevation - seg.start_elevation)
                    grade = seg.grade
                else:
                    # Curve segment (simplified - use average)
                    t = x / length if length > 0 else 0
                    elevation = seg.start_elevation + t * (seg.end_elevation - seg.start_elevation)
                    grade = seg.grade
                
                vertical.query_elevation = elevation
                vertical.query_grade = grade
                vertical.query_grade_percent = grade * 100
                
                self.report({'INFO'}, 
                    f"Station {station:.3f}m: Elev={elevation:.3f}m, Grade={grade*100:.2f}%")
                break
        
        if not found:
            self.report({'WARNING'}, f"Station {station:.3f}m not in alignment range")
            vertical.query_elevation = 0.0
            vertical.query_grade = 0.0
            vertical.query_grade_percent = 0.0
        
        return {'FINISHED'}


class BC_OT_TraceTerrainAsVertical(Operator):
    """Create vertical alignment by tracing terrain data"""
    bl_idname = "bc.trace_terrain_as_vertical"
    bl_label = "Trace Terrain as Alignment"
    bl_description = "Create IFC vertical alignment by tracing sampled terrain data"
    bl_options = {'REGISTER', 'UNDO'}

    pvi_interval: FloatProperty(
        name="PVI Interval",
        description="Distance between PVIs (meters)",
        default=5.0,
        min=1.0,
        max=50.0,
    )

    alignment_name: StringProperty(
        name="Alignment Name",
        description="Name for the vertical alignment",
        default="Terrain Trace",
    )

    @classmethod
    def poll(cls, context):
        # Check if terrain data exists
        from ..core.profile_view_overlay import get_profile_overlay
        overlay = get_profile_overlay()
        return overlay and len(overlay.data.terrain_points) > 0

    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        from ..core.native_ifc_vertical_alignment import VerticalAlignment
        from ..core.native_ifc_manager import NativeIfcManager
        from ..ui.alignment_properties import get_active_alignment_ifc
        import numpy as np

        # Get terrain data
        overlay = get_profile_overlay()
        if not overlay or len(overlay.data.terrain_points) == 0:
            self.report({'ERROR'}, "No terrain data available")
            return {'CANCELLED'}

        terrain_points = overlay.data.terrain_points

        # Sort terrain points by station
        terrain_points.sort(key=lambda p: p.station)

        # Get station range
        min_station = terrain_points[0].station
        max_station = terrain_points[-1].station

        # Create stations at regular intervals
        num_pvis = int((max_station - min_station) / self.pvi_interval) + 1
        pvi_stations = np.linspace(min_station, max_station, num_pvis)

        # Interpolate terrain elevations at PVI stations
        terrain_stations = np.array([p.station for p in terrain_points])
        terrain_elevations = np.array([p.elevation for p in terrain_points])

        pvi_elevations = np.interp(pvi_stations, terrain_stations, terrain_elevations)

        # Create VerticalAlignment object
        valign = VerticalAlignment(
            name=self.alignment_name,
            description=f"Traced from terrain data at {self.pvi_interval}m intervals"
        )

        # Add PVIs (no curves - all tangents)
        for station, elevation in zip(pvi_stations, pvi_elevations):
            valign.add_pvi(
                station=float(station),
                elevation=float(elevation),
                curve_length=0.0  # No curves - pure tangent alignment
            )

        # Get active horizontal alignment
        active_alignment_ifc = get_active_alignment_ifc(context)
        if not active_alignment_ifc:
            self.report({'ERROR'}, "No active horizontal alignment")
            return {'CANCELLED'}

        # Get IFC file
        ifc = NativeIfcManager.get_file()
        if not ifc:
            self.report({'ERROR'}, "No IFC file loaded")
            return {'CANCELLED'}

        # Export vertical alignment to IFC
        try:
            vertical_ifc = valign.to_ifc(ifc, horizontal_alignment=active_alignment_ifc)

            # Create Blender Empty to represent vertical alignment in Outliner
            valign.create_blender_empty(vertical_ifc, horizontal_alignment=active_alignment_ifc)

            # Add vertical alignment to profile view
            if overlay:
                # Clear old vertical alignments and add the new one
                overlay.data.clear_vertical_alignments()
                overlay.data.add_vertical_alignment(valign)
                overlay.data.select_vertical_alignment(0)  # Auto-select it
                overlay.data.update_view_extents()
                print(f"[Terrain Trace] Added vertical alignment to profile view")

            # Save IFC file
            NativeIfcManager.save_file()

            self.report({'INFO'},
                       f"Created vertical alignment '{self.alignment_name}' with {len(valign.pvis)} PVIs")

            # Print summary to console
            print("\n" + "="*60)
            print(valign.summary())
            print("="*60 + "\n")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to create vertical alignment: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

    def invoke(self, context, event):
        # Set default name based on active alignment
        from ..ui.alignment_properties import get_active_alignment_ifc
        active_alignment_ifc = get_active_alignment_ifc(context)
        if active_alignment_ifc:
            self.alignment_name = f"{active_alignment_ifc.Name} - Terrain Trace"

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        # Get terrain info
        from ..core.profile_view_overlay import get_profile_overlay
        overlay = get_profile_overlay()

        if overlay and len(overlay.data.terrain_points) > 0:
            box = layout.box()
            box.label(text=f"Terrain Data: {len(overlay.data.terrain_points)} points", icon='CHECKMARK')

            terrain_points = overlay.data.terrain_points
            min_station = min(p.station for p in terrain_points)
            max_station = max(p.station for p in terrain_points)

            box.label(text=f"Station Range: {min_station:.1f}m - {max_station:.1f}m")

            # Calculate number of PVIs
            num_pvis = int((max_station - min_station) / self.pvi_interval) + 1
            box.label(text=f"Will create: {num_pvis} PVIs", icon='INFO')

        layout.separator()

        # Settings
        layout.label(text="Alignment Settings:")
        layout.prop(self, "alignment_name")
        layout.prop(self, "pvi_interval")

        layout.separator()
        layout.label(text="Note: All segments will be tangents (no curves)", icon='INFO')


class BC_OT_ClearVerticalAlignment(Operator):
    """Clear all PVIs and segments"""
    bl_idname = "bc.clear_vertical"
    bl_label = "Clear All"
    bl_description = "Clear all PVIs and segments (cannot be undone)"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        vertical = context.scene.bc_vertical
        return len(vertical.pvis) > 0

    def execute(self, context):
        vertical = context.scene.bc_vertical

        num_pvis = len(vertical.pvis)
        vertical.pvis.clear()
        vertical.segments.clear()
        vertical.is_valid = False
        vertical.validation_message = "No PVIs defined"

        self.report({'INFO'}, f"Cleared {num_pvis} PVIs")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class BC_OT_SelectVerticalAlignment(Operator):
    """Select a vertical alignment for display in profile view"""
    bl_idname = "bc.select_vertical_alignment"
    bl_label = "Select Vertical Alignment"
    bl_description = "Select this vertical alignment for display in the profile viewer"
    bl_options = {'REGISTER', 'UNDO'}

    alignment_index: bpy.props.IntProperty(
        name="Alignment Index",
        description="Index of vertical alignment to select",
        default=0
    )

    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay

        # Get profile view overlay
        overlay = get_profile_overlay()
        if not overlay:
            self.report({'ERROR'}, "Profile view not available")
            return {'CANCELLED'}

        # Select the vertical alignment
        if overlay.data.select_vertical_alignment(self.alignment_index):
            valign = overlay.data.get_vertical_alignment(self.alignment_index)
            if valign:
                self.report({'INFO'}, f"Selected vertical alignment: {valign.name}")

                # Refresh the profile view
                if overlay.enabled:
                    overlay.refresh(context)

                # Redraw the 3D view to update the overlay
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()

                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to get vertical alignment")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, f"Invalid alignment index: {self.alignment_index}")
            return {'CANCELLED'}


# Registration
classes = (
    BC_OT_AddPVI,
    BC_OT_RemovePVI,
    BC_OT_EditPVI,
    BC_OT_DesignVerticalCurve,
    BC_OT_CalculateGrades,
    BC_OT_GenerateSegments,
    BC_OT_ValidateVertical,
    BC_OT_QueryStation,
    BC_OT_TraceTerrainAsVertical,
    BC_OT_ClearVerticalAlignment,
    BC_OT_SelectVerticalAlignment,
)


def register():
    """Register operator classes"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("  [+] Vertical alignment operators registered")


def unregister():
    """Unregister operator classes"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("  [-] Vertical alignment operators unregistered")


if __name__ == "__main__":
    register()
