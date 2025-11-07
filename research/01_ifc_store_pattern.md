# The IfcStore Pattern - Heart of Native IFC

## 🎯 Core Discovery
Bonsai uses a singleton-like pattern where ONE IFC file exists for the entire Blender session. This is the most important pattern to understand.

## 📍 Source Location
- **File:** `src/bonsai/bonsai/bim/ifc.py`
- **Class:** `IfcStore`

## 🔍 How Bonsai Does It
```python
class IfcStore:
    """Singleton pattern for IFC file management"""
    path = None      # Path to .ifc file on disk
    file = None      # The actual ifcopenshell file object
    schema = None    # IFC schema version (IFC2X3, IFC4, IFC4X3)
    
    @staticmethod
    def get_file():
        """Always returns THE file"""
        return IfcStore.file
    
    @staticmethod
    def set_file(file):
        """Replace THE file"""
        IfcStore.file = file
```

## 💡 Key Insights

### 1. Class Variables, Not Instance
- `file` is a CLASS variable - shared by everything
- No `self.file` - it's `IfcStore.file`
- One truth for entire session

### 2. Static Methods
- All methods are `@staticmethod`
- No instantiation: Never do `store = IfcStore()`
- Always access via: `IfcStore.get_file()`

### 3. File Lifecycle
```
New Project:     IfcStore.file = ifcopenshell.file()
Open Project:    IfcStore.file = ifcopenshell.open(path)
Save Project:    IfcStore.file.write(path)
Close Project:   IfcStore.file = None
```

## 🏗️ BlenderCivil Implementation
```python
# native_ifc_manager.py
import ifcopenshell
import ifcopenshell.api

class NativeIfcManager:
    """Our version of IfcStore for BlenderCivil"""
    
    # THE file - class variable like Bonsai
    file = None
    filepath = None
    
    @classmethod
    def get_file(cls):
        """Get or create the IFC file"""
        if cls.file is None:
            cls.new_file()
        return cls.file
    
    @classmethod
    def new_file(cls):
        """Create new IFC file for roadway design"""
        cls.file = ifcopenshell.file(schema="IFC4X3")  # 4X3 for infrastructure!
        cls.filepath = None
        
        # Create required project structure
        project = ifcopenshell.api.run("root.create_entity", 
            cls.file, 
            ifc_class="IfcProject", 
            name="BlenderCivil Project")
        
        return cls.file
    
    @classmethod
    def open_file(cls, filepath):
        """Open existing IFC file"""
        cls.file = ifcopenshell.open(filepath)
        cls.filepath = filepath
        return cls.file
    
    @classmethod
    def save_file(cls, filepath=None):
        """Save the IFC file"""
        if filepath:
            cls.filepath = filepath
        if cls.filepath and cls.file:
            cls.file.write(cls.filepath)
            return True
        return False
```

## ⚠️ Critical Rules

1. **NEVER** create multiple IFC files accidentally
2. **ALWAYS** use `get_file()` to access the file
3. **NEVER** store IFC file in Blender objects
4. The IFC file **IS** the database

## 🎓 Why This Matters

Traditional CAD:
```
Design in CAD → Export to IFC (conversion, data loss)
```

Native IFC (Bonsai/BlenderCivil):
```
Design IS IFC → Save IFC directly (no conversion!)
```

## 📝 Implementation Checklist

- [ ] Create NativeIfcManager class
- [ ] Use class variables for file storage
- [ ] Implement get_file() pattern
- [ ] Never instantiate, always use class methods
- [ ] Test file persistence across operations