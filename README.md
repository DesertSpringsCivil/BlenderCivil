# BlenderCivil

**Civil engineering and infrastructure design tools for Blender**

BlenderCivil is a comprehensive addon that brings professional civil engineering workflows to Blender, with seamless integration with Bonsai (BlenderBIM) and IfcOpenShell for OpenBIM workflows.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Blender](https://img.shields.io/badge/blender-4.2%2B-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🛣️ Horizontal Alignment Design
- **PI Points**: Place Points of Intersection interactively
- **Tangent Lines**: Automatic tangent creation between PIs
- **Horizontal Curves**: Insert circular curves with custom radius
- **Station Markers**: Add stationing labels at any interval
- **Export/Import**: JSON format for interoperability

### 🌍 Coordinate Reference Systems
- **OASYS Integration**: Fetch CRS automatically from roadway plans
- **Manual Entry**: Support for EPSG codes and custom systems
- **Bonsai Integration**: Apply georeferencing to IFC exports
- **Common CRS Library**: Pre-configured civil engineering coordinate systems

### 🏗️ OpenBIM / IFC Support
- **IfcAlignment Entities**: Proper IFC alignment export
- **Georeferenced Models**: Include CRS in IFC files
- **Bonsai Compatibility**: Works alongside Bonsai addon
- **IfcReferent**: Station points and control points as IFC entities

## 📦 Installation

### Method 1: Blender Extensions (Recommended for Blender 4.2+)

1. Download the latest release from [Releases](https://github.com/your-username/BlenderCivil/releases)
2. Open Blender 4.2 or later
3. Go to `Edit > Preferences > Get Extensions`
4. Click the dropdown menu (▼) → `Install from Disk...`
5. Select the downloaded `.zip` file
6. Enable the addon in the Extensions list

### Method 2: Manual Installation

1. Download and extract the addon
2. Copy the `BlenderCivil` folder to:
   - **Windows**: `C:\Users\[username]\AppData\Roaming\Blender Foundation\Blender\[version]\extensions\user_default\`
   - **macOS**: `~/Library/Application Support/Blender/[version]/extensions/user_default/`
   - **Linux**: `~/.config/blender/[version]/extensions/user_default/`
3. Restart Blender
4. Enable addon in Preferences

## 🚀 Quick Start

1. Open Blender and press `N` to open the sidebar
2. Navigate to the **"Civil"** tab
3. Start by setting your coordinate system (optional but recommended)
4. Create a horizontal alignment:
   - Place 3D cursor (`Shift + Right Click`)
   - Click "Add PI at Cursor"
   - Repeat for multiple points
   - Click "Create Tangents"
   - Adjust curve radius
   - Click "Insert Curves"
   - Add station markers

## 📖 Documentation

- [User Guide](docs/user_guide.md) - Complete usage instructions
- [API Documentation](docs/api.md) - For developers and scripters
- [Bonsai Integration](docs/bonsai_integration.md) - IFC/OpenBIM workflows
- [OASYS Platform](docs/oasys_integration.md) - Cloud API integration

## 🔧 Requirements

- **Blender**: 4.2.0 or later
- **Python**: 3.11+ (included with Blender)
- **Optional**: [Bonsai](https://extensions.blender.org/add-ons/bonsai/) addon for IFC features
- **Optional**: [IfcOpenShell](https://ifcopenshell.org/) for advanced IFC operations

## 🏗️ Project Structure

```
BlenderCivil/
├── __init__.py                 # Main addon file
├── blender_manifest.toml       # Blender 4.2+ manifest
├── preferences.py              # Addon preferences
├── properties.py               # Custom properties
├── ui.py                       # User interface panels
├── operators/                  # Operators (tools)
│   ├── __init__.py
│   ├── alignment.py            # Horizontal alignment tools
│   ├── crs.py                  # Coordinate system management
│   └── utils.py                # Utility operators
├── docs/                       # Documentation
├── tests/                      # Unit tests
└── examples/                   # Example files
```

## 🤝 Integration with Other Tools

### Bonsai (BlenderBIM)
BlenderCivil is designed to work alongside Bonsai:
- Shares coordinate system data
- Exports IFC-compliant alignments
- Respects IFC project structure
- Compatible with Bonsai workflows

### OASYS Platform
Connect to the OASYS cloud platform:
- Automatic CRS extraction from PDF plans
- Cloud-based coordinate system management
- RESTful API integration
- No client-side dependencies

## 🛣️ Roadmap

### Version 0.2 (Planned)
- [ ] Vertical alignment design
- [ ] Profile view / elevation editor
- [ ] Vertical curve insertion (parabolic)
- [ ] Grade control

### Version 0.3 (Planned)
- [ ] Spiral curve transitions (clothoids)
- [ ] Superelevation transitions
- [ ] Cross-section templates
- [ ] Cut/fill visualization

### Version 0.4 (Planned)
- [ ] LandXML import/export
- [ ] IFC4x3 alignment support
- [ ] Earthwork calculations
- [ ] Mass haul diagrams

## 🐛 Known Issues

- Station markers may not orient correctly on steep grades (will be fixed in v0.2)
- Large curve radius values may cause performance issues
- Bonsai integration is basic (will be expanded)

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **IfcOpenShell Team**: For the incredible IFC library
- **Bonsai Contributors**: For pioneering OpenBIM in Blender
- **Blender Foundation**: For making Blender free and open source
- **OASYS Community**: For feedback and testing

## 📧 Contact

- **Project Homepage**: https://github.com/your-username/BlenderCivil
- **Issue Tracker**: https://github.com/your-username/BlenderCivil/issues
- **Discussions**: https://github.com/your-username/BlenderCivil/discussions

## 💖 Support

If you find BlenderCivil useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 📖 Improving documentation
- 💡 Suggesting features
- 🤝 Contributing code

---

**Built with ❤️ for the civil engineering community**
