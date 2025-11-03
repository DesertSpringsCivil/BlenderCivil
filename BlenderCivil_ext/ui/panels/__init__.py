"""
BlenderCivil UI Panels
"""

from . import georeferencing_panel

def register():
    georeferencing_panel.register()

def unregister():
    georeferencing_panel.unregister()
