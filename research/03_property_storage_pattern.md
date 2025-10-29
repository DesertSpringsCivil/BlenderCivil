# Property Storage Pattern - Everything in IFC

## 🎯 Core Discovery
Properties are NEVER stored in Blender. They're stored in IFC property sets and retrieved on-demand for display.

## 📍 Source Locations
- **File:** `src/bonsai/bonsai/bim/module/pset/operator.py`
- **File:** `src/bonsai/bonsai/bim/module/attribute/operator.py`

## 🔍 How Bonsai Stores Properties

### Writing Properties (to IFC)
```python
# Create or get property set
pset = ifcopenshell.api.run("pset.add_pset", 
    ifc_file,
    product=ifc_element,
    name="Pset_WallCommon")

# Edit properties IN THE IFC FILE
ifcopenshell.api.run("pset.edit_pset",
    ifc_file,
    pset=pset,
    properties={
        "IsExternal": True,
        "FireRating": "2HR",
        "ThermalTransmittance": 0.24
    })

# Blender object knows NOTHING about these values!
```

### Reading Properties (from IFC)
```python
def get_element_properties(blender_obj):
    """Get all properties from IFC"""
    element = get_ifc_entity(blender_obj)
    if not element:
        return {}
    
    # Get all property sets
    properties = {}
    for definition in element.IsDefinedBy:
        if definition.is_a("IfcRelDefinesByProperties"):
            property_set = definition.RelatingPropertyDefinition
            if property_set.is_a("IfcPropertySet"):
                for prop in property_set.HasProperties:
                    if prop.is_a("IfcPropertySingleValue"):
                        properties[prop.Name] = prop.NominalValue.wrappedValue
    
    return properties
```

## 💡 Key Insights

### Traditional Blender Way (WRONG for Native IFC)
```python
# ❌ DON'T DO THIS
obj["design_speed"] = 60
obj["num_lanes"] = 2
obj["surface_type"] = "Asphalt"
```

### Native IFC Way (CORRECT)
```python
# ✅ DO THIS
ifc = NativeIfcManager.get_file()
alignment = ifc.by_id(obj["ifc_definition_id"])

# Create property set in IFC
pset = ifcopenshell.api.run("pset.add_pset",
    ifc,
    product=alignment,
    name="Pset_AlignmentDesign")

# Store in IFC
ifcopenshell.api.run("pset.edit_pset",
    ifc,
    pset=pset,
    properties={
        "DesignSpeed": 60,
        "NumberOfLanes": 2,
        "SurfaceType": "Asphalt"
    })
```

## 🏗️ BlenderCivil Implementation
```python
class AlignmentProperties:
    """Helper for IFC property management"""
    
    @staticmethod
    def set_property(alignment_obj, prop_name, value):
        """Set property in IFC, not Blender"""
        ifc = NativeIfcManager.get_file()
        alignment = get_ifc_entity(alignment_obj)
        
        if not alignment:
            return
        
        # Get or create property set
        pset = get_or_create_pset(alignment, "Pset_AlignmentData")
        
        # Update IN IFC
        ifcopenshell.api.run("pset.edit_pset",
            ifc,
            pset=pset,
            properties={prop_name: value})
    
    @staticmethod
    def get_property(alignment_obj, prop_name):
        """Get property from IFC"""
        alignment = get_ifc_entity(alignment_obj)
        if not alignment:
            return None
        
        # Search through property sets
        for rel in alignment.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset.is_a("IfcPropertySet"):
                    for prop in pset.HasProperties:
                        if prop.Name == prop_name:
                            return prop.NominalValue.wrappedValue
        return None

# Usage in operators
class BC_OT_set_design_speed(Operator):
    def execute(self, context):
        obj = context.active_object
        
        # NOT: obj["design_speed"] = 60
        # BUT:
        AlignmentProperties.set_property(obj, "DesignSpeed", 60)
        
        return {'FINISHED'}
```

## 📊 Property Set Organization

### Standard Property Sets for Alignments
```python
# Pset_AlignmentDesign
- DesignSpeed
- DesignYear  
- TrafficVolume

# Pset_AlignmentGeometry  
- StartStation
- EndStation
- Length

# Pset_AlignmentCurveData (per curve)
- Radius
- Delta
- TangentLength
- ChordLength
```

## ⚠️ Critical Rules

1. **NEVER** use Blender custom properties for data
2. **ALWAYS** store in IFC property sets
3. **RETRIEVE** from IFC when displaying in UI
4. **UPDATE** IFC when user changes values

## 📝 Implementation Checklist

- [ ] Remove all custom properties from objects
- [ ] Create property set helpers
- [ ] Update UI to read from IFC
- [ ] Update operators to write to IFC
- [ ] Define standard property sets for civil