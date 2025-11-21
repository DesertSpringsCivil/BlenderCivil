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
Terrain Sampling Operators
Operators for sampling elevation data from terrain meshes
"""

import bpy
from bpy.props import FloatProperty, StringProperty
from mathutils import Vector
from ..core import alignment_registry
from ..ui.alignment_properties import get_active_alignment_ifc


class BC_OT_sample_terrain_from_mesh(bpy.types.Operator):
    """Sample terrain elevation data from a mesh object along active horizontal alignment"""
    bl_idname = "bc.sample_terrain_from_mesh"
    bl_label = "Sample Terrain from Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    terrain_mesh: StringProperty(
        name="Terrain Mesh",
        description="Select the terrain mesh object to sample",
        default=""
    )

    sample_interval: FloatProperty(
        name="Sample Interval",
        description="Distance between sample points (meters)",
        default=10.0,
        min=0.1,
        max=100.0,
        unit='LENGTH'
    )

    raycast_offset: FloatProperty(
        name="Raycast Offset",
        description="Height above alignment to start raycast (meters)",
        default=1000.0,
        min=10.0,
        max=10000.0,
        unit='LENGTH'
    )

    def execute(self, context):
        """Execute the terrain sampling operation"""
        # Validate terrain mesh selection
        if not self.terrain_mesh:
            self.report({'ERROR'}, "No terrain mesh selected")
            return {'CANCELLED'}

        # Look up the mesh object by name
        mesh_obj = bpy.data.objects.get(self.terrain_mesh)
        if not mesh_obj:
            self.report({'ERROR'}, f"Mesh object '{self.terrain_mesh}' not found")
            return {'CANCELLED'}

        if mesh_obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object is not a mesh")
            return {'CANCELLED'}

        # Get active horizontal alignment
        active_alignment_ifc = get_active_alignment_ifc(context)
        if not active_alignment_ifc:
            self.report({'ERROR'}, "No active horizontal alignment")
            return {'CANCELLED'}

        # Get alignment object from registry
        alignment_obj = alignment_registry.get_alignment(active_alignment_ifc.GlobalId)
        if not alignment_obj:
            self.report({'ERROR'}, "Alignment not found in registry")
            return {'CANCELLED'}

        # Check if alignment has segments
        if not alignment_obj.segments:
            self.report({'ERROR'}, "Alignment has no segments")
            return {'CANCELLED'}

        # Get total alignment length
        total_length = sum(seg.DesignParameters.SegmentLength
                          for seg in alignment_obj.segments
                          if hasattr(seg.DesignParameters, 'SegmentLength'))

        if total_length <= 0:
            self.report({'ERROR'}, "Alignment has zero length")
            return {'CANCELLED'}

        # Sample terrain along alignment
        try:
            terrain_points = self._sample_terrain_from_mesh(
                mesh_obj,
                alignment_obj,
                total_length,
                self.sample_interval,
                self.raycast_offset
            )

            if not terrain_points:
                self.report({'WARNING'}, "No terrain data sampled (mesh may be out of range)")
                return {'CANCELLED'}

            # Store terrain points in profile view data
            from ..core.profile_view_overlay import get_profile_overlay
            overlay = get_profile_overlay()

            # Clear existing terrain
            overlay.data.clear_terrain()

            # Add sampled terrain points
            for station, elevation in terrain_points:
                overlay.data.add_terrain_point(station, elevation)

            # Update view extents
            overlay.data.update_view_extents()

            # Refresh overlay if enabled
            if overlay.enabled:
                overlay.refresh(context)

            self.report({'INFO'},
                       f"Sampled {len(terrain_points)} terrain points from mesh '{mesh_obj.name}'")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error sampling terrain: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

    def _sample_terrain_from_mesh(self, mesh_obj, alignment_obj, total_length, interval, offset):
        """
        Sample elevation data from mesh along the alignment using raycasting.

        Args:
            mesh_obj: Blender mesh object
            alignment_obj: Alignment object
            total_length: Total length of alignment (m)
            interval: Sample interval (m)
            offset: Height offset for raycast origin (m)

        Returns:
            List of (station, elevation) tuples
        """
        terrain_points = []

        # Get mesh data with transformations applied
        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh_eval = mesh_obj.evaluated_get(depsgraph)

        # Sample along alignment at regular intervals
        distance = 0.0
        while distance <= total_length:
            # Get 2D position at this distance along alignment
            position_2d = self._get_alignment_position_at_distance(
                alignment_obj, distance
            )

            if position_2d is None:
                distance += interval
                continue

            x, y = position_2d

            # Create raycast from above the terrain downward
            ray_origin = Vector((x, y, offset))
            ray_direction = Vector((0, 0, -1))  # Straight down

            # Perform raycast
            success, location, normal, index = mesh_eval.ray_cast(
                ray_origin,
                ray_direction,
                distance=offset * 2  # Max distance to search
            )

            if success:
                # Get elevation (Z coordinate)
                elevation = location.z

                # Get station value for this distance
                station = alignment_obj.get_station_at_distance(distance)
                terrain_points.append((station, elevation))

                print(f"[TerrainSampling] Distance {distance:.1f}m → Station {station:.1f}m, Elevation {elevation:.2f}m")

            distance += interval

        return terrain_points

    def _get_alignment_position_at_distance(self, alignment_obj, distance):
        """
        Get 2D position (x, y) at a distance along the alignment.

        Args:
            alignment_obj: Alignment object
            distance: Distance along alignment (m)

        Returns:
            (x, y) tuple or None
        """
        cumulative_distance = 0.0

        for segment in alignment_obj.segments:
            params = segment.DesignParameters
            segment_length = params.SegmentLength

            if cumulative_distance + segment_length >= distance:
                # Position is in this segment
                local_distance = distance - cumulative_distance

                if params.PredefinedType == "LINE":
                    # Linear segment
                    start_point = params.StartPoint.Coordinates
                    direction_angle = params.StartDirection

                    import math
                    x = start_point[0] + local_distance * math.cos(direction_angle)
                    y = start_point[1] + local_distance * math.sin(direction_angle)

                    return (x, y)

                elif params.PredefinedType == "CIRCULARARC":
                    # Circular arc segment
                    import math

                    start_point = params.StartPoint.Coordinates
                    radius = abs(params.StartRadiusOfCurvature)
                    start_direction = params.StartDirection
                    signed_radius = params.StartRadiusOfCurvature

                    # Calculate center of circle
                    if signed_radius > 0:  # LEFT turn (CCW)
                        center_angle = start_direction + math.pi / 2
                    else:  # RIGHT turn (CW)
                        center_angle = start_direction - math.pi / 2

                    center_x = start_point[0] + radius * math.cos(center_angle)
                    center_y = start_point[1] + radius * math.sin(center_angle)

                    # Calculate angle traveled along arc
                    arc_angle = local_distance / radius
                    if signed_radius < 0:  # CW turn
                        arc_angle = -arc_angle

                    # Current angle on circle
                    current_angle = start_direction + arc_angle
                    if signed_radius > 0:  # LEFT
                        current_angle -= math.pi / 2
                    else:  # RIGHT
                        current_angle += math.pi / 2

                    # Position on circle
                    x = center_x + radius * math.cos(current_angle)
                    y = center_y + radius * math.sin(current_angle)

                    return (x, y)

            cumulative_distance += segment_length

        return None

    def invoke(self, context, event):
        """Show dialog to select mesh and configure sampling"""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        """Draw operator properties in dialog"""
        layout = self.layout

        # Terrain mesh selection
        layout.label(text="Select Terrain Mesh:", icon='MESH_DATA')
        layout.prop_search(self, "terrain_mesh", context.scene, "objects", text="")

        # Show mesh info if selected
        if self.terrain_mesh:
            mesh_obj = bpy.data.objects.get(self.terrain_mesh)
            if mesh_obj:
                box = layout.box()
                box.label(text=f"Mesh: {mesh_obj.name}", icon='CHECKMARK')
                if mesh_obj.type == 'MESH':
                    mesh_data = mesh_obj.data
                    box.label(text=f"Vertices: {len(mesh_data.vertices):,}")
                    box.label(text=f"Faces: {len(mesh_data.polygons):,}")
                else:
                    box.label(text="WARNING: Not a mesh!", icon='ERROR')

        layout.separator()

        # Sampling parameters
        layout.label(text="Sampling Parameters:")
        layout.prop(self, "sample_interval")
        layout.prop(self, "raycast_offset")


class BC_OT_clear_terrain_data(bpy.types.Operator):
    """Clear terrain elevation data from profile view"""
    bl_idname = "bc.clear_terrain_data"
    bl_label = "Clear Terrain Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Clear terrain data from profile view overlay"""
        from ..core.profile_view_overlay import get_profile_overlay
        overlay = get_profile_overlay()

        # Clear terrain points
        overlay.data.clear_terrain()

        # Update view extents
        overlay.data.update_view_extents()

        # Refresh overlay if enabled
        if overlay.enabled:
            overlay.refresh(context)

        self.report({'INFO'}, "Cleared terrain data")
        return {'FINISHED'}


# Registration
classes = (
    BC_OT_sample_terrain_from_mesh,
    BC_OT_clear_terrain_data,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()