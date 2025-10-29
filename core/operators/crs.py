"""
CRS (Coordinate Reference System) operators with EPSG.io API integration.

Provides operators for CRS lookup, search, and management using the EPSG.io API.
"""

import bpy
import json
import urllib.request
import urllib.parse
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, IntProperty, CollectionProperty

# ============================================================================
# EPSG.io API Helper Functions
# ============================================================================

def fetch_crs_from_epsg_io(epsg_code, timeout=5):
    """
    Fetch CRS information from EPSG.io API.
    
    Args:
        epsg_code: EPSG code as integer or string
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with CRS info or None if failed
    """
    try:
        url = f"https://epsg.io/{epsg_code}.json"
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'BlenderCivil/0.3.0'}
        )
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))

            # EPSG.io now returns PROJ JSON format directly
            # Check if this is a valid CRS response
            if 'name' in data and 'id' in data:
                # Extract EPSG code from id field
                code = data['id'].get('code') if isinstance(data.get('id'), dict) else None
                
                return {
                    'code': code,
                    'name': data.get('name'),
                    'kind': data.get('type'),  # CRS type (e.g., ProjectedCRS, GeographicCRS)
                    'area': data.get('area'),
                    'bbox': data.get('bbox'),
                    'unit': None,  # Would need to extract from coordinate_system
                    'proj4': None,  # Not in PROJ JSON format
                    'wkt': None,   # Not in PROJ JSON format
                    'accuracy': None,
                    'deprecated': data.get('deprecated', False)
                }

            return None
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # EPSG code not found
        raise
    except Exception as e:
        print(f"EPSG.io API error: {e}")
        return None


def search_crs_by_name(query, kind='CRS', timeout=5):
    """
    Search for CRS by name using EPSG.io API.
    
    Args:
        query: Search query string
        kind: Type filter ('CRS', 'DATUM', etc.)
        timeout: Request timeout in seconds
        
    Returns:
        List of matching CRS dictionaries
    """
    try:
        # Build search URL
        params = {
            'format': 'json',
            'q': query
        }
        
        if kind:
            params['kind'] = kind
        
        url = f"https://epsg.io/?{urllib.parse.urlencode(params)}"
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': 'BlenderCivil/0.3.0'}
        )
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            results = []
            if 'results' in data:
                for result in data['results'][:20]:  # Limit to 20 results
                    results.append({
                        'code': result.get('code'),
                        'name': result.get('name'),
                        'kind': result.get('kind'),
                        'area': result.get('area'),
                        'deprecated': result.get('deprecated', False)
                    })
            
            return results
            
    except Exception as e:
        print(f"EPSG.io search error: {e}")
        return []


# ============================================================================
# CRS Lookup Operators
# ============================================================================

class CIVIL_OT_LookupEPSG(Operator):
    """Lookup CRS information from EPSG code using EPSG.io API"""
    bl_idname = "civil.lookup_epsg"
    bl_label = "Lookup EPSG Code"
    bl_description = "Fetch CRS name and details from EPSG.io database"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        georef = context.scene.bc_georeferencing
        
        if georef.epsg_code == 0:
            self.report({'ERROR'}, "Enter an EPSG code first")
            return {'CANCELLED'}
        
        # Show lookup in progress
        self.report({'INFO'}, f"Looking up EPSG:{georef.epsg_code}...")
        
        # Fetch from API
        crs_info = fetch_crs_from_epsg_io(georef.epsg_code)
        
        if crs_info is None:
            self.report({'ERROR'}, f"EPSG:{georef.epsg_code} not found")
            return {'CANCELLED'}
        
        # Check if deprecated
        if crs_info.get('deprecated'):
            self.report({'WARNING'}, f"EPSG:{georef.epsg_code} is deprecated")
        
        # Update CRS name
        georef.crs_name = crs_info['name']
        
        # Show success with details
        area = crs_info.get('area', 'Unknown area')
        self.report({'INFO'}, f"Found: {crs_info['name']} ({area})")
        
        return {'FINISHED'}


class CIVIL_OT_SearchCRS(Operator):
    """Search for CRS by name using EPSG.io API"""
    bl_idname = "civil.search_crs"
    bl_label = "Search CRS"
    bl_description = "Search for coordinate reference systems by name"
    bl_options = {'REGISTER'}
    
    search_query: StringProperty(
        name="Search",
        description="CRS search query (e.g., 'NAD83 UTM', 'WGS84')",
        default=""
    )
    
    def execute(self, context):
        if not self.search_query:
            self.report({'ERROR'}, "Enter a search query")
            return {'CANCELLED'}
        
        # Search API
        results = search_crs_by_name(self.search_query)
        
        if not results:
            self.report({'WARNING'}, f"No results found for '{self.search_query}'")
            return {'CANCELLED'}
        
        # Store results in scene for display
        scene = context.scene
        scene.bc_crs_search_results.clear()
        
        for result in results:
            item = scene.bc_crs_search_results.add()
            item.epsg_code = result['code']
            item.crs_name = result['name']
            item.area = result.get('area', '')
            item.deprecated = result.get('deprecated', False)
        
        self.report({'INFO'}, f"Found {len(results)} results")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        # Use CRS name as initial search query
        georef = context.scene.bc_georeferencing
        if georef.crs_name:
            self.search_query = georef.crs_name
        
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "search_query")


class CIVIL_OT_SelectCRSFromSearch(Operator):
    """Select a CRS from search results"""
    bl_idname = "civil.select_crs_from_search"
    bl_label = "Select CRS"
    bl_description = "Apply selected CRS from search results"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: IntProperty()
    
    def execute(self, context):
        scene = context.scene
        
        if self.index >= len(scene.bc_crs_search_results):
            self.report({'ERROR'}, "Invalid selection")
            return {'CANCELLED'}
        
        # Get selected result
        result = scene.bc_crs_search_results[self.index]
        
        # Apply to georeferencing
        georef = scene.bc_georeferencing
        georef.epsg_code = result.epsg_code
        georef.crs_name = result.crs_name
        
        self.report({'INFO'}, f"Set CRS to EPSG:{result.epsg_code}")
        
        return {'FINISHED'}


class CIVIL_OT_SetCommonCRS(Operator):
    """Set a common/preset CRS"""
    bl_idname = "civil.set_common_crs"
    bl_label = "Set Common CRS"
    bl_description = "Quickly set a commonly used coordinate system"
    bl_options = {'REGISTER', 'UNDO'}
    
    epsg_code: IntProperty()
    crs_name: StringProperty()
    
    def execute(self, context):
        georef = context.scene.bc_georeferencing
        georef.epsg_code = self.epsg_code
        georef.crs_name = self.crs_name
        
        self.report({'INFO'}, f"Set CRS to {self.crs_name}")
        
        return {'FINISHED'}


# ============================================================================
# Legacy Operators (kept for compatibility)
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
        # Legacy operator - kept for backward compatibility
        self.report({'WARNING'}, "OASYS integration not yet implemented")
        return {'CANCELLED'}


class CIVIL_OT_ListCRS(Operator):
    """List available coordinate systems"""
    bl_idname = "civil.list_crs"
    bl_label = "List CRS"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Legacy operator
        self.report({'INFO'}, "Use Search CRS instead")
        return {'FINISHED'}


class CIVIL_OT_SetCRSManual(Operator):
    """Manually set CRS"""
    bl_idname = "civil.set_crs_manual"
    bl_label = "Set CRS Manually"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # This is now handled directly in the UI
        return {'FINISHED'}


class CIVIL_OT_ClearCRS(Operator):
    """Clear CRS information"""
    bl_idname = "civil.clear_crs"
    bl_label = "Clear CRS"
    bl_description = "Clear coordinate reference system settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        georef = context.scene.bc_georeferencing
        georef.crs_name = ""
        georef.epsg_code = 0
        
        self.report({'INFO'}, "CRS cleared")
        
        return {'FINISHED'}


class CIVIL_OT_ApplyCRSToBonsai(Operator):
    """Apply CRS to Bonsai IFC"""
    bl_idname = "civil.apply_crs_to_bonsai"
    bl_label = "Apply to Bonsai"
    bl_description = "Apply CRS settings to Bonsai IFC project"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # TODO: Implement Bonsai integration
        self.report({'WARNING'}, "Bonsai integration not yet implemented")
        return {'CANCELLED'}


# ============================================================================
# Property Group for Search Results
# ============================================================================

class CRSSearchResult(bpy.types.PropertyGroup):
    """Property group to store CRS search results"""
    epsg_code: IntProperty(name="EPSG Code")
    crs_name: StringProperty(name="CRS Name")
    area: StringProperty(name="Area of Use")
    deprecated: bpy.props.BoolProperty(name="Deprecated", default=False)


# ============================================================================
# Registration
# ============================================================================

classes = (
    CRSSearchResult,
    CIVIL_OT_LookupEPSG,
    CIVIL_OT_SearchCRS,
    CIVIL_OT_SelectCRSFromSearch,
    CIVIL_OT_SetCommonCRS,
    CIVIL_OT_FetchCRS,
    CIVIL_OT_ListCRS,
    CIVIL_OT_SetCRSManual,
    CIVIL_OT_ClearCRS,
    CIVIL_OT_ApplyCRSToBonsai,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register search results collection
    bpy.types.Scene.bc_crs_search_results = bpy.props.CollectionProperty(
        type=CRSSearchResult
    )
    
    print("✅ CRS operators registered (with EPSG.io API)")


def unregister():
    # Unregister search results collection
    del bpy.types.Scene.bc_crs_search_results
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
