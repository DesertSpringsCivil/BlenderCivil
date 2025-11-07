"""
BlenderCivil - Native IFC Manager with Complete Spatial Hierarchy
Creates and visualizes the full IFC structure in Blender's outliner

This module creates the proper IFC spatial structure:
    IfcProject
    └── IfcSite
        └── IfcRoad

And visualizes it in Blender with organizational collections for:
    - Alignments
    - Geomodels
"""

import bpy
import ifcopenshell
import ifcopenshell.guid


class NativeIfcManager:
    """
    Manages IFC file lifecycle and Blender visualization of IFC hierarchy.
    
    Creates the proper spatial structure per IFC 4.3 (IFC4X3) standards,
    and visualizes it in Blender's outliner for user clarity.
    """
    
    # Class-level state
    file = None
    filepath = None
    project = None
    site = None
    road = None
    
    # Blender collections for organizing entities
    project_collection = None
    site_collection = None
    road_collection = None
    alignments_collection = None
    geomodels_collection = None
    
    @classmethod
    def new_file(cls, schema="IFC4X3"):
        """
        Create new IFC file with complete spatial hierarchy.
        
        Creates IFC structure:
            IfcProject → IfcSite → IfcRoad
            
        And Blender visualization:
            Project (Empty)
            └── Site (Empty)
                ├── Road (Empty)
                ├── Alignments (Collection)
                └── Geomodels (Collection)
        
        Args:
            schema: IFC schema version (default: IFC4X3)
            
        Returns:
            dict: Contains 'ifc_file', 'project_collection', and entity references
        """
        # Clear any existing data
        cls.clear()
        
        # ==========================================
        # STEP 1: Create IFC Spatial Structure
        # ==========================================
        
        cls.file = ifcopenshell.file(schema=schema)
        
        # Create IfcProject (top level)
        cls.project = cls.file.create_entity(
            "IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            Name="BlenderCivil Project",
            Description="Civil engineering project"
        )
        
        # Create IfcSite
        cls.site = cls.file.create_entity(
            "IfcSite",
            GlobalId=ifcopenshell.guid.new(),
            Name="Site",
            Description="Project site"
        )
        
        # Create IfcRoad
        cls.road = cls.file.create_entity(
            "IfcRoad",
            GlobalId=ifcopenshell.guid.new(),
            Name="Road",
            Description="Road facility"
        )
        
        # Establish relationships
        # Project → Site
        cls.file.create_entity(
            "IfcRelAggregates",
            GlobalId=ifcopenshell.guid.new(),
            Name="ProjectContainsSite",
            Description="Project spatial decomposition",
            RelatingObject=cls.project,
            RelatedObjects=[cls.site]
        )
        
        # Site → Road
        cls.file.create_entity(
            "IfcRelAggregates",
            GlobalId=ifcopenshell.guid.new(),
            Name="SiteContainsRoad",
            Description="Site spatial decomposition",
            RelatingObject=cls.site,
            RelatedObjects=[cls.road]
        )
        
        # ==========================================
        # STEP 2: Create Blender Visualization
        # ==========================================
        
        cls._create_blender_hierarchy()
        
        print("✅ Created IFC spatial hierarchy with Blender visualization")
        print(f"   IFC Entities: {len(cls.file.by_type('IfcRoot'))} total")
        print(f"   Blender Collections: Project → Site → Road, Alignments, Geomodels")
        
        return {
            'ifc_file': cls.file,
            'project_collection': cls.project_collection,
            'project': cls.project,
            'site': cls.site,
            'road': cls.road
        }
    
    @classmethod
    def _create_blender_hierarchy(cls):
        """
        Create Blender objects and collections that mirror the IFC hierarchy.
        
        Structure created:
            [Collection] BlenderCivil Project
                [Empty] Site
                    [Empty] Road
                    [Collection] Alignments
                    [Collection] Geomodels
        """
        
        # Create main project collection
        cls.project_collection = bpy.data.collections.new("BlenderCivil Project")
        bpy.context.scene.collection.children.link(cls.project_collection)
        
        # ==========================================
        # Project Level - Empty object
        # ==========================================
        
        project_empty = bpy.data.objects.new("📂 Project", None)
        project_empty.empty_display_type = 'CUBE'
        project_empty.empty_display_size = 5.0
        cls.project_collection.objects.link(project_empty)
        
        # Link to IFC
        cls.link_object(project_empty, cls.project)
        
        # ==========================================
        # Site Level - Empty object (child of Project)
        # ==========================================
        
        site_empty = bpy.data.objects.new("🌍 Site", None)
        site_empty.empty_display_type = 'CUBE'
        site_empty.empty_display_size = 4.0
        site_empty.parent = project_empty
        cls.project_collection.objects.link(site_empty)
        
        # Link to IFC
        cls.link_object(site_empty, cls.site)
        
        # ==========================================
        # Road Level - Empty object (child of Site)
        # ==========================================
        
        road_empty = bpy.data.objects.new("🛣️  Road", None)
        road_empty.empty_display_type = 'CUBE'
        road_empty.empty_display_size = 3.0
        road_empty.parent = site_empty
        cls.project_collection.objects.link(road_empty)
        
        # Link to IFC
        cls.link_object(road_empty, cls.road)
        
        # ==========================================
        # Organizational Empties (No separate collections needed)
        # ==========================================

        # Alignments empty - visual parent for alignments
        alignments_empty = bpy.data.objects.new("📏 Alignments", None)
        alignments_empty.empty_display_type = 'SPHERE'
        alignments_empty.empty_display_size = 2.0
        alignments_empty.parent = site_empty
        cls.project_collection.objects.link(alignments_empty)

        # Store reference to alignments empty (instead of collection)
        cls.alignments_collection = alignments_empty

        # Geomodels empty - visual parent for geomodels
        geomodels_empty = bpy.data.objects.new("🌏 Geomodels", None)
        geomodels_empty.empty_display_type = 'SPHERE'
        geomodels_empty.empty_display_size = 2.0
        geomodels_empty.parent = site_empty
        cls.project_collection.objects.link(geomodels_empty)

        # Store reference to geomodels empty (instead of collection)
        cls.geomodels_collection = geomodels_empty
        
        print("✅ Blender hierarchy created in outliner")
    
    @classmethod
    def open_file(cls, filepath):
        """
        Load existing IFC file and create Blender visualization.
        
        Args:
            filepath: Path to IFC file
            
        Returns:
            IfcFile: The loaded IFC file
        """
        cls.clear()
        cls.file = ifcopenshell.open(filepath)
        cls.filepath = filepath
        
        # Find key entities
        projects = cls.file.by_type("IfcProject")
        if projects:
            cls.project = projects[0]
        
        sites = cls.file.by_type("IfcSite")
        if sites:
            cls.site = sites[0]
            
        roads = cls.file.by_type("IfcRoad")
        if roads:
            cls.road = roads[0]
        
        # Create Blender visualization
        cls._create_blender_hierarchy()
        
        # Load existing alignments
        alignments = cls.file.by_type("IfcAlignment")
        for alignment in alignments:
            # TODO: Create visualization for each alignment
            pass
        
        print(f"✅ Loaded IFC file: {filepath}")
        print(f"   Entities: {len(cls.file.by_type('IfcRoot'))}")
        
        return cls.file
    
    @classmethod
    def save_file(cls, filepath=None):
        """
        Write IFC file to disk.
        
        Args:
            filepath: Path to save file (uses stored filepath if None)
        """
        if filepath:
            cls.filepath = filepath
        
        if not cls.filepath:
            raise ValueError("No filepath specified")
        
        if not cls.file:
            raise ValueError("No IFC file to save")
        
        cls.file.write(cls.filepath)
        
        # Store filepath in scene
        bpy.context.scene["ifc_filepath"] = cls.filepath
        
        print(f"✅ Saved IFC file: {cls.filepath}")
    
    @classmethod
    def get_file(cls):
        """
        Get the active IFC file, creating one if needed.
        
        Returns:
            IfcFile: The active IFC file
        """
        if cls.file is None:
            cls.new_file()
        return cls.file
    
    @classmethod
    def get_project(cls):
        """Get IfcProject entity"""
        if cls.project is None and cls.file:
            projects = cls.file.by_type("IfcProject")
            if projects:
                cls.project = projects[0]
        return cls.project
    
    @classmethod
    def get_site(cls):
        """Get IfcSite entity"""
        if cls.site is None and cls.file:
            sites = cls.file.by_type("IfcSite")
            if sites:
                cls.site = sites[0]
        return cls.site
    
    @classmethod
    def get_road(cls):
        """Get IfcRoad entity"""
        if cls.road is None and cls.file:
            roads = cls.file.by_type("IfcRoad")
            if roads:
                cls.road = roads[0]
        return cls.road

    @classmethod
    def get_project_collection(cls):
        """Get Blender collection for the project"""
        if cls.project_collection is None:
            # Try to find existing collection
            if "BlenderCivil Project" in bpy.data.collections:
                cls.project_collection = bpy.data.collections["BlenderCivil Project"]
        return cls.project_collection

    @classmethod
    def get_alignments_collection(cls):
        """Get Blender empty for alignments (parent object)"""
        if cls.alignments_collection is None:
            # Try to find existing empty object
            if "📏 Alignments" in bpy.data.objects:
                cls.alignments_collection = bpy.data.objects["📏 Alignments"]
        return cls.alignments_collection

    @classmethod
    def get_geomodels_collection(cls):
        """Get Blender empty for geomodels (parent object)"""
        if cls.geomodels_collection is None:
            # Try to find existing empty object
            if "🌏 Geomodels" in bpy.data.objects:
                cls.geomodels_collection = bpy.data.objects["🌏 Geomodels"]
        return cls.geomodels_collection
    
    @classmethod
    def link_object(cls, blender_obj, ifc_entity):
        """
        Link Blender object to IFC entity.
        
        Stores minimal data in Blender object:
        - ifc_definition_id: Link to IFC entity
        - ifc_class: IFC entity type
        - GlobalId: IFC standard identifier
        
        Args:
            blender_obj: Blender object
            ifc_entity: IFC entity to link
        """
        blender_obj["ifc_definition_id"] = ifc_entity.id()
        blender_obj["ifc_class"] = ifc_entity.is_a()
        blender_obj["GlobalId"] = ifc_entity.GlobalId
    
    @classmethod
    def get_entity(cls, blender_obj):
        """
        Retrieve IFC entity from Blender object.
        
        Args:
            blender_obj: Blender object with IFC link
            
        Returns:
            IFC entity or None
        """
        if "ifc_definition_id" in blender_obj:
            return cls.file.by_id(blender_obj["ifc_definition_id"])
        return None
    
    @classmethod
    def clear(cls):
        """Clear all IFC data and Blender collections"""
        cls.file = None
        cls.filepath = None
        cls.project = None
        cls.site = None
        cls.road = None
        
        # Remove Blender collections if they exist
        if cls.project_collection and cls.project_collection.name in bpy.data.collections:
            bpy.data.collections.remove(cls.project_collection)
        
        cls.project_collection = None
        cls.site_collection = None
        cls.road_collection = None
        cls.alignments_collection = None
        cls.geomodels_collection = None
        
        print("✅ Cleared IFC data and Blender hierarchy")
    
    @classmethod
    def get_info(cls):
        """
        Get information about current IFC file.
        
        Returns:
            dict: File information
        """
        if cls.file is None:
            return {
                'loaded': False,
                'message': 'No IFC file loaded'
            }
        
        return {
            'loaded': True,
            'filepath': cls.filepath,
            'schema': cls.file.schema,
            'entities': len(cls.file.by_type("IfcRoot")),
            'project': cls.project.Name if cls.project else None,
            'site': cls.site.Name if cls.site else None,
            'road': cls.road.Name if cls.road else None,
            'alignments': len(cls.file.by_type("IfcAlignment")),
            'geomodels': len(cls.file.by_type("IfcGeomodel"))
        }


# ============================================================================
# Utility Functions for Adding Entities to Proper Collections
# ============================================================================

def add_alignment_to_hierarchy(alignment_obj):
    """
    Add an alignment object to the hierarchy by parenting to Alignments empty.

    Args:
        alignment_obj: Blender object representing an alignment
    """
    parent_empty = NativeIfcManager.get_alignments_collection()
    if parent_empty and alignment_obj.parent != parent_empty:
        alignment_obj.parent = parent_empty
        print(f"✅ Added alignment '{alignment_obj.name}' to Alignments hierarchy")


def add_geomodel_to_hierarchy(geomodel_obj):
    """
    Add a geomodel object to the hierarchy by parenting to Geomodels empty.

    Args:
        geomodel_obj: Blender object representing a geomodel
    """
    parent_empty = NativeIfcManager.get_geomodels_collection()
    if parent_empty and geomodel_obj.parent != parent_empty:
        geomodel_obj.parent = parent_empty
        print(f"✅ Added geomodel '{geomodel_obj.name}' to Geomodels hierarchy")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    Test script - creates the full IFC hierarchy.
    Run this in Blender's Python console or as a script.
    """
    
    print("\n" + "="*60)
    print("BlenderCivil - Creating IFC Spatial Hierarchy")
    print("="*60 + "\n")
    
    # Create new IFC file with full hierarchy
    result = NativeIfcManager.new_file()
    
    print("\n" + "-"*60)
    print("IFC Structure Created:")
    print("-"*60)
    print(f"Schema: {result['ifc_file'].schema}")
    print(f"Project: {result['project'].Name}")
    print(f"Site: {result['site'].Name}")
    print(f"Road: {result['road'].Name}")
    
    print("\n" + "-"*60)
    print("Blender Outliner Structure:")
    print("-"*60)
    print("📂 BlenderCivil Project (Collection)")
    print("   ├── 📂 Project (Empty)")
    print("   └── 🌍 Site (Empty)")
    print("       ├── 🛣️  Road (Empty)")
    print("       ├── 📏 Alignments (Empty)")
    print("       └── 🌏 Geomodels (Empty)")

    print("\n" + "-"*60)
    print("Next Steps:")
    print("-"*60)
    print("1. User creates alignment → parented to Alignments empty")
    print("2. User creates geomodel → parented to Geomodels empty")
    print("3. Spatial structure visible in Blender outliner")
    print("4. IFC file maintains proper relationships")
    
    print("\n✅ Setup complete! Ready for user workflow.\n")
