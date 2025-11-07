# BlenderCivil v0.3.0 - Quick Installation Guide

## 📦 Installation Steps

### Step 1: Prepare the Files

You have the complete `BlenderCivil_v2` folder with these files:
```
BlenderCivil_v2/
├── __init__.py                 (Main addon file)
├── properties_v2.py            (Property system)
├── alignment_objects_v2.py     (Object creation)
├── operators_v2.py             (Operators)
├── handlers_v2.py              (Auto-update handler)
├── ui_v2.py                    (User interface)
├── test_alignment_v2.py        (Test script)
├── README.md                   (Full documentation)
└── PHASE1_COMPLETE.md          (Summary)
```

### Step 2: Install in Blender

**Option A: ZIP Installation (Recommended)**

1. Create a ZIP file of the `BlenderCivil_v2` folder:
   - **Windows:** Right-click → Send to → Compressed (zipped) folder
   - **Mac:** Right-click → Compress "BlenderCivil_v2"
   - **Linux:** `cd /path/to/folder && zip -r BlenderCivil_v2.zip BlenderCivil_v2/`

2. Open Blender (version 4.0 or higher)

3. Go to: **Edit → Preferences → Add-ons**

4. Click **"Install..."** button

5. Select the ZIP file you created

6. Enable the addon by checking the box next to **"BlenderCivil v0.3.0"**

7. Verify installation:
   - Check console (Window → Toggle System Console)
   - Should see: `✓ BlenderCivil v0.3.0 ready!`

**Option B: Manual Installation (For Development)**

1. Find your Blender addons folder:
   - **Windows:** `C:\Users\<YourName>\AppData\Roaming\Blender Foundation\Blender\<version>\scripts\addons\`
   - **Mac:** `~/Library/Application Support/Blender/<version>/scripts/addons/`
   - **Linux:** `~/.config/blender/<version>/scripts/addons/`

2. Copy the entire `BlenderCivil_v2` folder there

3. Restart Blender

4. Enable the addon in Preferences

### Step 3: Verify Installation

1. Press **N** in the 3D viewport to open the sidebar

2. You should see a **"Civil"** tab

3. Click on it to see the "Professional Alignment (v0.3)" panel

### Step 4: Run Test (Optional)

1. In Blender, open the **Text Editor** (change an area to Text Editor)

2. Click **"Open"** and select `test_alignment_v2.py`

3. Press **Alt+P** to run the script

4. Check the console for test results

5. You should see a test alignment created in the viewport!

## 🚀 First Use

### Create Your First Alignment

1. **Add PI points:**
   - Press **Shift+A** → Empty → Arrows
   - Name them: `PI_001`, `PI_002`, `PI_003`, etc.
   - Position them along your desired route

2. **Create alignment:**
   - Press **N** → Civil tab
   - Set name, radius, design speed
   - Click **"Create Professional Alignment"**

3. **Interactive design:**
   - Select any PI
   - Press **G** to move it
   - Watch the alignment update automatically! ✨

## 📖 Next Steps

- Read the **README.md** for full documentation
- Read **PHASE1_COMPLETE.md** for what we built
- Experiment with moving PIs
- Check the console output for details

## 🐛 Troubleshooting

**"Module not found" error:**
- Make sure ALL files are in the `BlenderCivil_v2` folder
- Reinstall the addon

**Can't see Civil tab:**
- Press N in viewport
- Make sure addon is enabled
- Check console for error messages

**Auto-update not working:**
- Must use G key (not Python scripts)
- Check if auto-update is enabled in UI
- Try toggling it OFF then ON

## ✅ Success Checklist

- [ ] Addon installed
- [ ] Civil tab visible
- [ ] Test script runs successfully
- [ ] Can create alignments
- [ ] Can move PIs with G key
- [ ] Alignment auto-updates

## 🎉 You're Ready!

You now have a professional-grade, IFC-compatible alignment design system in Blender!

**Enjoy designing! 🛣️✨**
