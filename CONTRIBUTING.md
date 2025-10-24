# Contributing to BlenderCivil

Thank you for your interest in contributing to BlenderCivil! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- **Report Bugs**: Submit detailed bug reports
- **Suggest Features**: Propose new features or enhancements
- **Write Code**: Implement new features or fix bugs
- **Improve Documentation**: Enhance guides, examples, or API docs
- **Test**: Help test new releases and report issues

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Blender Version**: Which version you're using
2. **Addon Version**: BlenderCivil version
3. **Operating System**: Windows, macOS, or Linux
4. **Steps to Reproduce**: Detailed steps to recreate the issue
5. **Expected Behavior**: What you expected to happen
6. **Actual Behavior**: What actually happened
7. **Screenshots**: If applicable

## 💡 Suggesting Features

When suggesting features:

1. **Check Existing Issues**: Ensure it hasn't been suggested
2. **Use Case**: Describe your use case
3. **Mockups**: Include sketches or mockups if possible
4. **Bonsai Compatibility**: Consider IFC/OpenBIM implications

## 🔧 Development Setup

### Prerequisites

- Blender 4.2 or later
- Git
- Python 3.11+ (comes with Blender)
- Optional: VS Code with Python extension

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/BlenderCivil.git
   cd BlenderCivil
   ```

2. **Create Development Symlink**
   
   Instead of copying files, create a symlink from Blender's extensions directory to your development folder:
   
   **Windows (PowerShell as Administrator)**:
   ```powershell
   New-Item -ItemType SymbolicLink -Path "$env:APPDATA\Blender Foundation\Blender\4.2\extensions\user_default\BlenderCivil" -Target "C:\path\to\your\BlenderCivil"
   ```
   
   **macOS/Linux**:
   ```bash
   ln -s /path/to/your/BlenderCivil ~/Library/Application\ Support/Blender/4.2/extensions/user_default/BlenderCivil
   ```

3. **Enable Developer Mode in Blender**
   - Go to `Edit > Preferences > Interface`
   - Enable "Developer Extras"
   - Enable "Python Tooltips"

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Comment complex logic
- Maximum line length: 100 characters

### Code Structure

```python
"""
Module description

Brief description of what this module does
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty

class CIVIL_OT_ExampleOperator(Operator):
    """Short description for tooltip"""
    bl_idname = "civil.example_operator"
    bl_label = "Example Operator"
    bl_description = "Longer description of what this operator does"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Properties
    example_prop: StringProperty(
        name="Example",
        description="Description of this property",
        default=""
    )
    
    def execute(self, context):
        """Execute the operator"""
        # Your code here
        self.report({'INFO'}, "Operation completed")
        return {'FINISHED'}
```

### Naming Conventions

- **Operators**: `CIVIL_OT_OperatorName`
- **Panels**: `CIVIL_PT_PanelName`
- **Properties**: `CIVIL_PropertyGroup`
- **Functions**: `lowercase_with_underscores`
- **Constants**: `UPPERCASE_WITH_UNDERSCORES`

## 🧪 Testing

Before submitting a PR:

1. Test your changes in Blender
2. Test with and without Bonsai addon
3. Test on different platforms if possible
4. Check for console errors
5. Verify existing features still work

## 📝 Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, documented code
   - Follow the code style guidelines
   - Test thoroughly

3. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```
   
   Use conventional commit messages:
   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Docs:` for documentation
   - `Refactor:` for code refactoring
   - `Test:` for adding tests

4. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Provide a clear title and description
   - Reference related issues
   - Include screenshots if UI changes
   - Wait for review

## 🏗️ Architecture Guidelines

### Module Organization

- **operators/**: All operator classes
- **ui.py**: All UI panels
- **properties.py**: Property groups
- **preferences.py**: Addon preferences
- **utils/**: Helper functions and utilities

### Integration Points

When adding features, consider:

- **Bonsai Compatibility**: Don't break existing Bonsai workflows
- **IFC Standards**: Follow IFC specifications for infrastructure
- **OASYS API**: Use consistent patterns for API calls
- **Collections**: Use proper collection hierarchy

### Performance

- Avoid expensive operations in `draw()` methods
- Use efficient algorithms for geometry generation
- Consider memory usage for large projects
- Cache results when appropriate

## 🎓 Learning Resources

- [Blender Python API](https://docs.blender.org/api/current/)
- [IFC Documentation](https://standards.buildingsmart.org/IFC/)
- [IfcOpenShell Docs](https://docs.ifcopenshell.org/)
- [Bonsai Development](https://docs.bonsaibim.org/guides/development/)

## 📞 Communication

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Requests**: For code contributions

## 🙏 Recognition

Contributors will be:
- Listed in the project README
- Credited in release notes
- Acknowledged in commit history

Thank you for contributing to BlenderCivil! 🎉
