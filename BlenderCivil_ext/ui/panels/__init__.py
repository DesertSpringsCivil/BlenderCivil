"""
BlenderCivil UI Panels
"""

from . import georeferencing_panel
from . import vertical_alignment_panel

def register():
    georeferencing_panel.register()
    vertical_alignment_panel.register()

def unregister():
    vertical_alignment_panel.unregister()
    georeferencing_panel.unregister()
