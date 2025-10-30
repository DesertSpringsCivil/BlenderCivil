"""
Native IFC Manager
Manages the IFC file and Blender object relationships
"""

import bpy
import math
import ifcopenshell
import ifcopenshell.guid
from mathutils import Vector


class NativeIfcManager:
    """Manages the IFC file and Blender object relationships"""
    
    file = None
    filepath = None
    project = None
    site = None
    
    @classmethod
    def new_file(cls, schema="IFC4X3"):
        """Create new IFC file with basic structure"""
        cls.file = ifcopenshell.file(schema=schema)
        
        # Create project
        cls.project = cls.file.create_entity("IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            Name="BlenderCivil Sprint 1")
        
        # Create site
        cls.site = cls.file.create_entity("IfcSite",
            GlobalId=ifcopenshell.guid.new(),
            Name="Test Site")
        
        return cls.file
    
    @classmethod
    def get_file(cls):
        """Get active IFC file"""
        if cls.file is None:
            cls.new_file()
        return cls.file
    
    @classmethod
    def link_object(cls, blender_obj, ifc_entity):
        """Link Blender object to IFC entity"""
        blender_obj["ifc_definition_id"] = ifc_entity.id()
        blender_obj["ifc_class"] = ifc_entity.is_a()
        blender_obj["GlobalId"] = ifc_entity.GlobalId
    
    @classmethod
    def get_entity(cls, blender_obj):
        """Get IFC entity from Blender object"""
        if "ifc_definition_id" in blender_obj:
            return cls.file.by_id(blender_obj["ifc_definition_id"])
        return None

