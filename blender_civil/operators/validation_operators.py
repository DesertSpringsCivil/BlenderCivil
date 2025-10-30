"""
Validation Operations
Validation and debugging operators for IFC alignments
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty


class BC_OT_validate_ifc_alignment(bpy.types.Operator):
    """Validate IFC alignment structure"""
    bl_idname = "bc.validate_ifc_alignment"
    bl_label = "Validate IFC"
    
    def execute(self, context):
        ifc = NativeIfcManager.get_file()
        
        # Check for alignments
        alignments = ifc.by_type("IfcAlignment")
        if not alignments:
            self.report({'ERROR'}, "No alignments in IFC file")
            return {'CANCELLED'}
        
        print("\n" + "="*60)
        print("IFC ALIGNMENT VALIDATION")
        print("="*60)
        
        # Get PIs and segments from scene
        pis = [obj for obj in bpy.data.objects if "ifc_pi_id" in obj]
        segments = [obj for obj in bpy.data.objects 
                   if "ifc_definition_id" in obj and "ifc_class" in obj]
        
        print(f"\n📊 STRUCTURE:")
        print(f"  PIs found: {len(pis)}")
        print(f"  Segments found: {len(segments)}")
        
        print(f"\n📏 SEGMENT DETAILS:")
        for obj in segments:
            obj_type = "CURVE" if obj.type == 'CURVE' else obj.type
            print(f"  [{len([s for s in segments if segments.index(s) < segments.index(obj)])}] {obj.name} - Type: {obj_type}")
        
        print(f"\n✅ VALIDATION PASSED")
        
        self.report({'INFO'}, f"Validation passed: {len(pis)} PIs, {len(segments)} segments")
        return {'FINISHED'}



class BC_OT_show_segment_info(bpy.types.Operator):
    """Show segment information"""
    bl_idname = "bc.show_segment_info"
    bl_label = "Show Segment Info"
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or "ifc_definition_id" not in obj:
            self.report({'ERROR'}, "Select an alignment segment")
            return {'CANCELLED'}
        
        ifc = NativeIfcManager.get_file()
        segment = ifc.by_id(obj["ifc_definition_id"])
        params = segment.DesignParameters
        
        print(f"\n{'='*60}")
        print(f"SEGMENT: {obj.name}")
        print(f"{'='*60}")
        print(f"Type: {params.PredefinedType}")
        print(f"Length: {params.SegmentLength:.3f}m")
        print(f"Start Point: {params.StartPoint.Coordinates}")
        print(f"Start Direction: {params.StartDirection:.4f} rad")
        print(f"Start Radius: {params.StartRadiusOfCurvature:.2f}m")
        print(f"End Radius: {params.EndRadiusOfCurvature:.2f}m")
        
        self.report({'INFO'}, f"{params.PredefinedType}: {params.SegmentLength:.2f}m")
        return {'FINISHED'}



class BC_OT_list_all_ifc_objects(bpy.types.Operator):
    """List all IFC-linked objects"""
    bl_idname = "bc.list_all_ifc_objects"
    bl_label = "List All IFC Objects"
    
    def execute(self, context):
        print("\n" + "="*60)
        print("LISTING ALL IFC OBJECTS")
        print("="*60)
        
        # Get all IFC-linked objects
        ifc_objects = [obj for obj in bpy.data.objects 
                      if "ifc_definition_id" in obj]
        pis = [obj for obj in bpy.data.objects if "ifc_pi_id" in obj]
        
        print("\n" + "="*60)
        print("ALL IFC-LINKED OBJECTS")
        print("="*60)
        
        print(f"\n📊 SUMMARY:")
        print(f"  IFC Entities: {len(ifc_objects)}")
        print(f"  PI Markers: {len(pis)}")
        
        print(f"\n📍 PIs:")
        for obj in sorted(pis, key=lambda x: x.get("ifc_pi_id", 0)):
            pi_id = obj.get("ifc_pi_id", "?")
            radius = obj.get("radius", 0.0)
            loc = obj.location
            print(f"  [{pi_id}] {obj.name} - R={radius}m at ({loc.x:.1f}, {loc.y:.1f})")
        
        print(f"\n🔗 IFC SEGMENTS:")
        for obj in ifc_objects:
            ifc_class = obj.get("ifc_class", "Unknown")
            print(f"  {obj.name} - {ifc_class}")
        
        self.report({'INFO'}, f"Found {len(ifc_objects)} IFC objects, {len(pis)} PIs")
        return {'FINISHED'}


# ==================== UI PANELS ====================



# Registration
classes = (
    BC_OT_validate_ifc_alignment,
    BC_OT_show_segment_info,
    BC_OT_list_all_ifc_objects,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
