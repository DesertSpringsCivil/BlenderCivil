"""
BlenderCivil Operators

Organize operators by functional area:
- alignment: Horizontal and vertical alignment tools
- crs: Coordinate reference system management
- ifc: IFC export and Bonsai integration
- terrain: Terrain and site modeling
"""

from . import alignment
from . import crs
from . import utils

modules = (
    alignment,
    crs,
    utils,
)

def register():
    for module in modules:
        if hasattr(module, 'register'):
            module.register()

def unregister():
    for module in reversed(modules):
        if hasattr(module, 'unregister'):
            module.unregister()
