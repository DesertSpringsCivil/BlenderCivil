# Sprint 1 Kickoff: PI-Driven Horizontal Alignments
**Duration:** 5 Days  
**Start Date:** October 29, 2025  
**Theme:** "PIs in Pure IFC"  
**Status:** ðŸŽ¯ READY TO BEGIN

---

## 🎯 Sprint 1 Goal

**Implement professional PI-driven horizontal alignment design with TRUE native IFC storage.**

Every PI, every tangent, every curve lives in the IFC file from creation - just like Civil 3D workflow, but in native IFC format.

---

## âœ… Pre-Sprint Checklist

### Foundation Ready?

- [x] **NativeIfcManager complete** - Core system operational
- [x] **File operations working** - Save/load tested
- [x] **Blender integration** - Visualization system ready
- [x] **Round-trip validated** - 100% data integrity
- [x] **Architecture documented** - Patterns clear
- [x] **Team confident** - Ready to build

**Status:** ðŸŸ¢ ALL SYSTEMS GO!

---

## ðŸ"‹ Sprint 1 Day-by-Day Plan

### Day 1: IFC Alignment Structure

**Morning (4 hours):** IFC Schema Deep Dive
- Study IFC 4.3 alignment structure in detail
- Understand IfcAlignment hierarchy
- Research IfcAlignmentHorizontal
- Document IfcAlignmentSegment parameters

**Afternoon (4 hours):** Implement Core Structure
- Create `NativeIfcAlignment` class
- Implement PI data model
- Create segment generation logic
- Test basic structure

**Deliverable:** Core IFC alignment class with PI support

---

### Day 2: Blender Visualization Layer

**Morning (4 hours):** Create Blender Objects for IFC
- Create `AlignmentVisualizer` class
- Generate PI empties
- Generate segment curves
- Link all to IFC entities

**Afternoon (4 hours):** Interactive PI Editing
- Implement PI move operator
- Real-time IFC updates
- Automatic segment regeneration
- Visual feedback

**Deliverable:** Interactive PI editing in Blender

---

### Day 3: UI Panel for Native IFC

**Morning (4 hours):** Native IFC Panel
- Create main IFC panel
- File operations UI
- Alignment tools UI
- PI tools UI

**Afternoon (4 hours):** Operators
- Create alignment operator
- Add PI operator
- Insert PI operator
- Delete PI operator

**Deliverable:** Complete UI for alignment authoring

---

### Day 4: Advanced IFC Operations

**Morning (4 hours):** Segment Properties
- Add design parameters (speed, superelevation)
- Create property sets (Pset_AlignmentDesign)
- Associate with segments
- UI for properties

**Afternoon (4 hours):** Testing & Validation
- Create validation operator
- Check IFC structure
- Verify continuity
- Test edge cases

**Deliverable:** Professional-grade IFC output

---

### Day 5: Integration Testing

**Morning (4 hours):** Complete Workflow Test
- Create new project
- Add 5 PIs
- Edit interactively
- Save and reload
- Verify in IFC viewer

**Afternoon (4 hours):** Documentation
- User guide
- Developer notes
- Demo video script
- Sprint 1 summary

**Deliverable:** Complete PI-driven alignment system

---

## 🎓 What You Need to Know

### IFC 4.3 Alignment Basics

**Hierarchy:**
```
IfcAlignment
â""â"€â"€ IfcAlignmentHorizontal (via IfcRelNests)
    â"œâ"€â"€ IfcAlignmentSegment [0] - Tangent
    â"œâ"€â"€ IfcAlignmentSegment [1] - Curve
    â"œâ"€â"€ IfcAlignmentSegment [2] - Tangent
    â""â"€â"€ IfcAlignmentSegment [3] - Curve
```

**Segment Types:**
- `LINE` - Straight tangent
- `CIRCULARARC` - Circular curve
- `CLOTHOID` - Spiral transition (Sprint 2)

**Key Properties:**
- `StartPoint` - IfcCartesianPoint (x, y)
- `StartDirection` - Angle in radians
- `SegmentLength` - Length in meters
- `StartRadiusOfCurvature` - For curves
- `PredefinedType` - LINE, CIRCULARARC, etc.

### PI Method Overview

**What is a PI?**
- Point of Intersection
- Where two tangents would meet
- Defines alignment geometry

**How it Works:**
1. User places PIs
2. System calculates tangents between PIs
3. System inserts curves at PIs (based on radius)
4. Result: Smooth alignment

**Example:**
```
PI1 (0,0) --tangent--> PI2 (100,0) --tangent--> PI3 (200,100)
                           ^
                       (curve here)
```

---

## 🔧 Key Classes to Implement

### NativeIfcAlignment

```python
class NativeIfcAlignment:
    """Native IFC alignment with PI-driven design"""
    
    def __init__(self, ifc_file, name):
        self.ifc = ifc_file
        self.alignment = None      # IfcAlignment
        self.horizontal = None     # IfcAlignmentHorizontal
        self.pis = []              # List of PI data
        self.segments = []         # List of IFC segments
        
    def create_alignment_structure(self, name):
        """Create IfcAlignment + IfcAlignmentHorizontal"""
        
    def add_pi(self, x, y, radius=0.0):
        """Add PI and regenerate segments"""
        
    def regenerate_segments(self):
        """Recalculate all segments from PIs"""
        
    def create_tangent_segment(self, start, end):
        """Create IFC LINE segment"""
        
    def create_curve_segment(self, curve_data):
        """Create IFC CIRCULARARC segment"""
        
    def calculate_curve(self, prev_pi, curr_pi, next_pi, radius):
        """Calculate curve geometry"""
```

### AlignmentVisualizer

```python
class AlignmentVisualizer:
    """Create Blender visualization of IFC alignment"""
    
    def __init__(self, native_alignment):
        self.alignment = native_alignment
        self.collection = None
        self.pi_objects = []
        self.segment_objects = []
        
    def setup_collection(self):
        """Create Blender collection"""
        
    def create_pi_object(self, pi_data):
        """Create Empty for PI"""
        
    def create_segment_curve(self, ifc_segment):
        """Create Blender curve for segment"""
        
    def update_visualization(self):
        """Refresh all Blender objects"""
```

---

## 📊 Success Criteria

### Minimum Viable Product

By end of Sprint 1, you must be able to:

âœ… **Create** native IFC alignment  
âœ… **Add** PIs interactively  
âœ… **Move** PIs with automatic updates  
âœ… **Save** IFC file with complete data  
âœ… **Load** IFC file and continue editing  
âœ… **Open** IFC file in external viewer  

### Quality Standards

- [ ] All data in IFC (zero Blender properties)
- [ ] 100% data integrity (round-trip test)
- [ ] Smooth user experience (no crashes)
- [ ] Clear error messages
- [ ] Professional visualization
- [ ] IFC 4.3 compliance

---

## 🎯 Key Deliverables

### Code

**Core System:**
- `native_alignment.py` - NativeIfcAlignment class
- `alignment_visualizer.py` - AlignmentVisualizer class
- `alignment_operators.py` - Blender operators
- `alignment_ui.py` - UI panels

**Tests:**
- `test_alignment.py` - Unit tests
- `test_pi_workflow.py` - Integration test
- `test_ifc_output.py` - IFC validation

### Documentation

- User guide for PI method
- Developer notes on alignment logic
- Sprint 1 summary
- Demo video script

### Demo Materials

- Sample IFC files
- Before/after comparisons
- Screenshots/GIFs
- Video demonstration

---

## âš ï¸ Known Challenges

### Technical Challenges

**1. Curve Calculation**
- Need accurate tangent-curve-tangent geometry
- Must handle edge cases (straight sections)
- Precision is critical

**Solution:** Use proven civil engineering formulas, test extensively.

**2. Segment Continuity**
- Segments must connect perfectly
- No gaps or overlaps
- Directions must match

**Solution:** Validation function, continuous testing.

**3. IFC Relationships**
- Proper nesting with IfcRelNests
- Segment ordering
- Clean hierarchy

**Solution:** Follow IFC 4.3 spec exactly, validate structure.

### UI/UX Challenges

**1. PI Manipulation**
- Need smooth, responsive editing
- Real-time visual feedback
- Undo/redo support

**Solution:** Modal operators, depsgraph handlers, proper state management.

**2. Visual Clarity**
- PIs must be distinct
- Tangents vs curves clear
- Selection feedback

**Solution:** Color coding, distinct markers, selection highlighting.

---

## 💡 Pro Tips

### Development Best Practices

**1. Test Early, Test Often**
```python
# After every change, test:
- Create alignment
- Add 3 PIs
- Save IFC
- Load IFC
- Verify data
```

**2. Use Print Debugging**
```python
print(f"Created segment: {segment.Name}")
print(f"  Type: {params.PredefinedType}")
print(f"  Length: {params.SegmentLength}")
print(f"  IFC ID: {segment.id()}")
```

**3. Validate IFC Structure**
```python
# After creating entities, check:
alignments = ifc.by_type("IfcAlignment")
print(f"Alignments: {len(alignments)}")

for alignment in alignments:
    # Check nested entities
    for rel in ifc.by_type("IfcRelNests"):
        if rel.RelatingObject == alignment:
            print(f"  Contains: {len(rel.RelatedObjects)} items")
```

**4. Keep IFC File Open**
```python
# During development, keep a viewer open:
# - FreeCAD
# - IFC.js viewer
# - Blender with Bonsai

# Save after each change, reload in viewer
# Catches IFC structure issues immediately
```

---

## 📚 Resources for Sprint 1

### Must-Read Documentation

**IFC 4.3 Alignment:**
- https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcAlignment.htm
- https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcAlignmentHorizontal.htm
- https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcAlignmentSegment.htm

**Alignment Geometry:**
- Civil 3D User Guide (PI method reference)
- AASHTO "A Policy on Geometric Design of Highways and Streets"
- Wikipedia: Horizontal curve design

**Code References:**
- Bonsai alignment code (if available)
- FreeCAD Road Workbench
- Our Sprint 0 code

### Community Resources

**Ask for Help:**
- OSArch Forum - Alignment design questions
- IfcOpenShell GitHub - IFC technical issues
- Blender Stack Exchange - UI/UX questions

**Share Progress:**
- Post updates on OSArch
- Share screenshots
- Get feedback early

---

## 🎬 Getting Started

### Day 1 Morning - First Steps

**1. Review Sprint 0 Code**
```bash
# Make sure you have:
- native_ifc_manager.py
- Test IFC files from Sprint 0
- Architecture documentation
```

**2. Set Up Development Environment**
```bash
# Open Blender
# Load native_ifc_manager.py
# Test that it works:
ifc = NativeIfcManager.new_file()
print(f"IFC loaded: {ifc is not None}")
```

**3. Study IFC Alignment Structure**
```python
# Create test alignment to understand structure
ifc = ifcopenshell.file(schema="IFC4X3")

alignment = ifc.create_entity("IfcAlignment", 
    GlobalId=ifcopenshell.guid.new(),
    Name="Study Alignment")

horizontal = ifc.create_entity("IfcAlignmentHorizontal",
    GlobalId=ifcopenshell.guid.new())

# Study the entities, explore properties
print(f"Alignment: {alignment}")
print(f"Horizontal: {horizontal}")
```

**4. Plan Your Implementation**
- Sketch out class structure
- Identify key methods
- List test cases
- Start coding!

---

## 🎯 Sprint 1 Vision

### What Success Looks Like

**End of Week 1:**

A civil engineer opens Blender, clicks "New IFC Alignment", places 5 PIs by clicking in the viewport, adjusts PI positions by dragging, sees tangents and curves generate automatically, saves the IFC file, opens it in Civil 3D, and sees perfect geometry.

**That's the goal.**

**That's what we're building.**

**That's Native IFC Civil Engineering.**

---

## ðŸ'ª You've Got This!

### Remember

âœ… You have a solid foundation (Sprint 0)  
âœ… You understand the architecture  
âœ… You have working examples  
âœ… You have documentation  
âœ… You have community support  

### When You Get Stuck

1. Check the architecture docs
2. Look at Sprint 0 code
3. Review IFC 4.3 spec
4. Ask on OSArch forum
5. Take a break and come back

### Stay Focused

**This week's ONE goal:**
**Professional PI-driven alignment design in native IFC.**

Everything else can wait.

---

## ðŸš€ Let's Begin!

### Sprint 1, Day 1 Starts Now

**First Task:** Open `Native_IFC_Sprint_1_PI_Alignments.md` and begin Day 1 implementation.

**First Code:** Create `native_alignment.py` with the `NativeIfcAlignment` class.

**First Test:** Create an alignment with 2 PIs and verify it in an IFC viewer.

---

## 🎉 You're Ready!

**Sprint 0:** âœ… Foundation Complete  
**Sprint 1:** ðŸš€ READY TO LAUNCH

**"From PIs to professional alignments - in pure native IFC."**

---

**Sprint 1 Kickoff Plan**  
**Date:** October 28, 2025  
**Status:** âœ… READY TO BEGIN  
**Confidence:** ðŸ"¥ HIGH  
**Next Action:** Start Day 1 implementation!

**Let's build something amazing!** ðŸŒŸðŸ›£ï¸

---

## 📋 Quick Reference

### Sprint 1 At-a-Glance

| Day | Focus | Key Deliverable |
|-----|-------|----------------|
| 1 | IFC Alignment Structure | NativeIfcAlignment class |
| 2 | Blender Visualization | AlignmentVisualizer class |
| 3 | UI Panel | Complete alignment UI |
| 4 | Advanced Operations | Properties & validation |
| 5 | Testing & Docs | Working system + guide |

### Critical Success Factors

1. âœ… Follow the golden pattern (IFC first, Blender second)
2. âœ… Test constantly (round-trip after every change)
3. âœ… Keep it simple (minimal complexity)
4. âœ… Document as you go (future you will thank you)
5. âœ… Ask for help (community is here)

### Emergency Contacts

- OSArch Forum: community.osarch.org
- IfcOpenShell Issues: github.com/IfcOpenShell/IfcOpenShell/issues
- Sprint 0 Reference: All documentation in /outputs

---

**NOW GO BUILD!** ðŸš€
