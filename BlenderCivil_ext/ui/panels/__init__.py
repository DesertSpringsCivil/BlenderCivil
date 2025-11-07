"""
BlenderCivil UI Panels
"""

from . import georeferencing_panel
from . import vertical_alignment_panel
from . import cross_section_panel
from . import visualization_panel

def register():
    georeferencing_panel.register()
    vertical_alignment_panel.register()
    cross_section_panel.register()
    visualization_panel.register()

def unregister():
    visualization_panel.unregister()
    cross_section_panel.unregister()
    vertical_alignment_panel.unregister()
    georeferencing_panel.unregister()
