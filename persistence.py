"""
BlenderCivil - Template Persistence System
Sprint 1 Day 4: Save/Load Templates to/from JSON

This module handles serialization and deserialization of cross-section templates.
"""

import bpy
import json
import os
from pathlib import Path


def get_user_templates_dir():
    """Get or create the user templates directory"""
    # Use Blender's user config directory
    config_path = bpy.utils.user_resource('CONFIG')
    templates_dir = Path(config_path) / "blendercivil" / "templates"
    
    # Create if doesn't exist
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    return str(templates_dir)


def template_to_dict(template):
    """Convert a CrossSectionTemplate to a dictionary"""
    data = {
        "name": template.name,
        "template_type": template.template_type,
        "description": template.description,
        "symmetrical": template.symmetrical,
        "crown_type": template.crown_type,
        "start_station": template.start_station,
        "end_station": template.end_station,
        
        "lanes_left": {
            "count": template.lanes_left.count,
            "width": template.lanes_left.width,
            "cross_slope": template.lanes_left.cross_slope,
        },
        
        "lanes_right": {
            "count": template.lanes_right.count,
            "width": template.lanes_right.width,
            "cross_slope": template.lanes_right.cross_slope,
        },
        
        "shoulder_left": {
            "width": template.shoulder_left.width,
            "slope": template.shoulder_left.slope,
            "type": template.shoulder_left.type,
        },
        
        "shoulder_right": {
            "width": template.shoulder_right.width,
            "slope": template.shoulder_right.slope,
            "type": template.shoulder_right.type,
        },
        
        "has_median": template.has_median,
    }
    
    if template.has_median:
        data["median"] = {
            "width": template.median.width,
            "type": template.median.type,
            "left_slope": template.median.left_slope,
            "right_slope": template.median.right_slope,
        }
    
    return data


def dict_to_template(data, scene):
    """Create a CrossSectionTemplate from a dictionary"""
    template = scene.cross_section_templates.add()
    
    # Basic properties
    template.name = data.get("name", "Imported Template")
    template.template_type = data.get("template_type", "CUSTOM")
    template.description = data.get("description", "")
    template.symmetrical = data.get("symmetrical", True)
    template.crown_type = data.get("crown_type", "CROWN")
    template.start_station = data.get("start_station", 0.0)
    template.end_station = data.get("end_station", 1000.0)
    
    # Lanes
    if "lanes_left" in data:
        template.lanes_left.count = data["lanes_left"].get("count", 1)
        template.lanes_left.width = data["lanes_left"].get("width", 12.0)
        template.lanes_left.cross_slope = data["lanes_left"].get("cross_slope", -0.02)
    
    if "lanes_right" in data:
        template.lanes_right.count = data["lanes_right"].get("count", 1)
        template.lanes_right.width = data["lanes_right"].get("width", 12.0)
        template.lanes_right.cross_slope = data["lanes_right"].get("cross_slope", -0.02)
    
    # Shoulders
    if "shoulder_left" in data:
        template.shoulder_left.width = data["shoulder_left"].get("width", 8.0)
        template.shoulder_left.slope = data["shoulder_left"].get("slope", -0.04)
        template.shoulder_left.type = data["shoulder_left"].get("type", "PAVED")
    
    if "shoulder_right" in data:
        template.shoulder_right.width = data["shoulder_right"].get("width", 8.0)
        template.shoulder_right.slope = data["shoulder_right"].get("slope", -0.04)
        template.shoulder_right.type = data["shoulder_right"].get("type", "PAVED")
    
    # Median
    template.has_median = data.get("has_median", False)
    if template.has_median and "median" in data:
        template.median.width = data["median"].get("width", 20.0)
        template.median.type = data["median"].get("type", "DEPRESSED")
        template.median.left_slope = data["median"].get("left_slope", -0.04)
        template.median.right_slope = data["median"].get("right_slope", 0.04)
    
    return template


def save_template_to_file(template, filepath):
    """Save a single template to a JSON file"""
    data = template_to_dict(template)
    
    # Add metadata
    data["_metadata"] = {
        "version": "1.0",
        "software": "BlenderCivil",
        "format": "CrossSectionTemplate"
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return True


def load_template_from_file(filepath, scene):
    """Load a single template from a JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Validate format
    if "_metadata" in data:
        if data["_metadata"].get("format") != "CrossSectionTemplate":
            raise ValueError("Invalid template format")
    
    template = dict_to_template(data, scene)
    return template


def save_templates_library(templates, filepath):
    """Save multiple templates to a JSON file"""
    library = {
        "_metadata": {
            "version": "1.0",
            "software": "BlenderCivil",
            "format": "TemplateLibrary",
            "count": len(templates)
        },
        "templates": [template_to_dict(t) for t in templates]
    }
    
    with open(filepath, 'w') as f:
        json.dump(library, f, indent=2)
    
    return True


def load_templates_library(filepath, scene, replace=False):
    """Load multiple templates from a JSON file"""
    with open(filepath, 'r') as f:
        library = json.load(f)
    
    # Validate format
    if "_metadata" not in library or library["_metadata"].get("format") != "TemplateLibrary":
        raise ValueError("Invalid library format")
    
    # Clear existing if replace
    if replace:
        scene.cross_section_templates.clear()
    
    # Load templates
    loaded = []
    for template_data in library.get("templates", []):
        template = dict_to_template(template_data, scene)
        loaded.append(template)
    
    return loaded


def export_scene_templates(scene, filepath):
    """Export all templates from the scene to a file"""
    templates = scene.cross_section_templates
    if len(templates) == 0:
        raise ValueError("No templates to export")
    
    return save_templates_library(templates, filepath)


def import_templates_to_scene(scene, filepath, replace=False):
    """Import templates from a file to the scene"""
    return load_templates_library(filepath, scene, replace=replace)


# Utility functions
def get_template_filepath(template_name):
    """Get the default filepath for a template"""
    templates_dir = get_user_templates_dir()
    # Sanitize filename
    safe_name = "".join(c for c in template_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    return os.path.join(templates_dir, f"{safe_name}.json")


def get_library_filepath(library_name="MyLibrary"):
    """Get the default filepath for a template library"""
    templates_dir = get_user_templates_dir()
    safe_name = "".join(c for c in library_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    return os.path.join(templates_dir, f"{safe_name}_Library.json")


def list_saved_templates():
    """List all saved template files"""
    templates_dir = get_user_templates_dir()
    templates = []
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(templates_dir, filename)
            templates.append((filepath, filename[:-5]))  # Remove .json extension
    
    return templates
