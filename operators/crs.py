"""
BlenderCivil - Coordinate Reference System Operators

Operators for managing coordinate reference systems:
- Fetch CRS from OASYS API
- Apply CRS to scene
- Convert between coordinate systems
- Integrate with Bonsai georeferencing
"""

import bpy
import json
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty
from .. import preferences

# ============================================================================
# OASYS API OPERATORS
# ============================================================================

class CIVIL_OT_FetchCRS(Operator):
    """Fetch coordinate system from OASYS API"""
    bl_idname = "civil.fetch_crs"
    bl_label = "Fetch CRS from OASYS"
    bl_description = "Retrieve coordinate reference system from OASYS platform"
    bl_options = {'REGISTER'}
    
    plan_key: StringProperty(
        name="Plan Key",
        description="Key/filename of the plan in OASYS system",
        default=""
    )
    
    def execute(self, context):
        prefs = preferences.get_preferences(context)
        api_url = prefs.oasys_api_url
        
        if not api_url:
            self.report({'ERROR'}, "OASYS API URL not configured")
            return {'CANCELLED'}
        
        # TODO: Implement actual API call
        # For now, this is a placeholder
        
        try:
            import urllib.request
            import urllib.parse
            
            # Construct URL
            url = f"{api_url}/get-crs/{urllib.parse.quote(self.plan_key)}"
            
            # Add API key if available
            headers = {}
            if prefs.oasys_api_key:
                headers['X-API-Key'] = prefs.oasys_api_key
            
            # Make request
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
                # Apply CRS to scene
                crs = context.scene.civil_crs
                coord_sys = data.get("coordinate_system", {})
                
                crs.epsg_code = coord_sys.get("epsg_code", "")
                crs.coordinate_system_name = coord_sys.get("coordinate_system_name", "")
                crs.datum = coord_sys.get("datum", "")
                crs.projection = coord_sys.get("projection", "")
                crs.units = coord_sys.get("units", "meters")
                crs.vertical_datum = coord_sys.get("vertical_datum", "")
                crs.has_crs = True
                
                # Get scale factor from blender_setup if available
                blender_setup = data.get("blender_setup", {})
                if "scale_factor" in blender_setup:
                    crs.scale_factor = blender_setup["scale_factor"]
                
                self.report({'INFO'}, f"Applied CRS: {crs.coordinate_system_name}")
                return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to fetch CRS: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class CIVIL_OT_ListCRS(Operator):
    """List available CRS files from OASYS"""
    bl_idname = "civil.list_crs"
    bl_label = "List Available CRS"
    bl_description = "List coordinate systems available in OASYS"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        prefs = preferences.get_preferences(context)
        api_url = prefs.oasys_api_url
        
        if not api_url:
            self.report({'ERROR'}, "OASYS API URL not configured")
            return {'CANCELLED'}
        
        try:
            import urllib.request
            
            url = f"{api_url}/list-crs"
            
            headers = {}
            if prefs.oasys_api_key:
                headers['X-API-Key'] = prefs.oasys_api_key
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
                files = data.get("files", [])
                
                if files:
                    print("\nAvailable CRS files from OASYS:")
                    for file in files:
                        print(f"  - {file}")
                    self.report({'INFO'}, f"Found {len(files)} CRS files")
                else:
                    self.report({'INFO'}, "No CRS files found")
                
                return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to list CRS: {str(e)}")
            return {'CANCELLED'}

# ============================================================================
# MANUAL CRS OPERATORS
# ============================================================================

class CIVIL_OT_SetCRSManual(Operator):
    """Manually set coordinate reference system"""
    bl_idname = "civil.set_crs_manual"
    bl_label = "Set CRS Manually"
    bl_description = "Manually configure coordinate reference system"
    bl_options = {'REGISTER', 'UNDO'}
    
    epsg_code: StringProperty(
        name="EPSG Code",
        description="EPSG code (e.g., 2277 for NAD83 Texas Central)",
        default=""
    )
    
    crs_name: StringProperty(
        name="CRS Name",
        description="Coordinate system name",
        default=""
    )
    
    def execute(self, context):
        crs = context.scene.civil_crs
        
        crs.epsg_code = self.epsg_code
        crs.coordinate_system_name = self.crs_name
        crs.has_crs = True
        
        # Try to look up common EPSG codes
        if self.epsg_code:
            crs_info = self.get_epsg_info(self.epsg_code)
            if crs_info:
                crs.datum = crs_info.get("datum", "")
                crs.units = crs_info.get("units", "meters")
                crs.projection = crs_info.get("projection", "")
        
        self.report({'INFO'}, f"Set CRS: {crs.coordinate_system_name}")
        return {'FINISHED'}
    
    def get_epsg_info(self, epsg_code):
        """Get common EPSG code information"""
        # Dictionary of common civil engineering CRS
        common_epsg = {
            "2277": {
                "name": "NAD83 / Texas Central (ftUS)",
                "datum": "NAD83",
                "units": "US survey feet",
                "projection": "Lambert Conformal Conic"
            },
            "2278": {
                "name": "NAD83 / Texas Central",
                "datum": "NAD83",
                "units": "meters",
                "projection": "Lambert Conformal Conic"
            },
            "3857": {
                "name": "WGS 84 / Pseudo-Mercator",
                "datum": "WGS84",
                "units": "meters",
                "projection": "Mercator"
            },
            "4326": {
                "name": "WGS 84",
                "datum": "WGS84",
                "units": "degrees",
                "projection": "Geographic"
            },
        }
        
        return common_epsg.get(epsg_code)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class CIVIL_OT_ClearCRS(Operator):
    """Clear coordinate reference system"""
    bl_idname = "civil.clear_crs"
    bl_label = "Clear CRS"
    bl_description = "Remove coordinate reference system from scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        crs = context.scene.civil_crs
        
        crs.epsg_code = ""
        crs.coordinate_system_name = ""
        crs.datum = ""
        crs.projection = ""
        crs.units = "meters"
        crs.vertical_datum = ""
        crs.scale_factor = 1.0
        crs.has_crs = False
        
        self.report({'INFO'}, "CRS cleared")
        return {'FINISHED'}

# ============================================================================
# BONSAI INTEGRATION
# ============================================================================

class CIVIL_OT_ApplyCRSToBonsai(Operator):
    """Apply CRS to Bonsai georeferencing"""
    bl_idname = "civil.apply_crs_to_bonsai"
    bl_label = "Apply to Bonsai"
    bl_description = "Apply coordinate system to Bonsai/IFC georeferencing"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        crs = context.scene.civil_crs
        
        if not crs.has_crs:
            self.report({'WARNING'}, "No CRS set")
            return {'CANCELLED'}
        
        try:
            from bonsai.bim.ifc import IfcStore
            
            # TODO: Implement Bonsai CRS integration
            # This would set the IfcMapConversion and IfcProjectedCRS
            
            self.report({'INFO'}, "Applied CRS to Bonsai (placeholder)")
            return {'FINISHED'}
            
        except ImportError:
            self.report({'ERROR'}, "Bonsai addon not found")
            return {'CANCELLED'}

# ============================================================================
# REGISTRATION
# ============================================================================

classes = (
    CIVIL_OT_FetchCRS,
    CIVIL_OT_ListCRS,
    CIVIL_OT_SetCRSManual,
    CIVIL_OT_ClearCRS,
    CIVIL_OT_ApplyCRSToBonsai,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
