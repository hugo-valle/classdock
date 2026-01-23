# 🔄 Single Source of Truth Version Management

## 🎯 **Problem Solved**

**Before**: Version was hardcoded in 3 places → maintenance nightmare
- `pyproject.toml` → `version = "3.1.0b1"`
- `__init__.py` → `__version__ = "3.1.0b1"`  
- `cli.py` → `"ClassDock v3.1.0b1"`

**After**: Version defined in ONE place → `pyproject.toml` only ✅

## 🔧 **Solution Implementation**

### **1. Single Source of Truth**
- ✅ **`pyproject.toml`** → Only place where version is defined
- ✅ **`__init__.py`** → Reads version dynamically from package metadata
- ✅ **`cli.py`** → Imports version from `__init__.py`

### **2. Dynamic Version Detection**
```python
# __init__.py
from ._version import get_version
__version__ = get_version()

# cli.py  
from . import __version__
typer.echo(f"ClassDock v{__version__}")
```

### **3. Smart Fallback System**
- **Production**: Uses `importlib.metadata` to read from installed package
- **Development**: Falls back to reading `pyproject.toml` directly
- **Error handling**: Graceful fallback to `0.0.0.dev`

## 📋 **Version Flow**

### **Production (Installed Package)**
```
pyproject.toml → pip install → package metadata → __version__
```

### **Development (Uninstalled)**
```
pyproject.toml → regex parser → __version__ + ".dev"
```

## 🚀 **Usage Examples**

### **Update Version (Only ONE place!)**
```toml
# pyproject.toml - ONLY place to change version
[project]
version = "3.2.0"  # ← Change ONLY here
```

### **Access Version Programmatically**
```python
from classdock import __version__
print(__version__)  # → "3.2.0"
```

### **CLI Version Command**
```bash
classdock --version
# Output: ClassDock v3.2.0
```

## 🔧 **Technical Implementation**

### **Version Utility (`_version.py`)**
```python
def get_version() -> str:
    try:
        # Try installed package metadata first
        return metadata.version("classdock")
    except metadata.PackageNotFoundError:
        # Fallback to pyproject.toml for development
        return _read_version_from_pyproject()
```

### **Fallback Parser**
```python
def _read_version_from_pyproject() -> str:
    # Read pyproject.toml directly
    # Parse version with regex
    # Return version + ".dev" suffix
```

## ✅ **Benefits**

### **1. Single Source of Truth**
- ✅ Update version in ONE place only
- ✅ No synchronization issues
- ✅ No risk of version mismatches

### **2. Development-Friendly**
- ✅ Works in both installed and development environments
- ✅ Clear `.dev` suffix for development versions
- ✅ Graceful fallback for edge cases

### **3. Production-Ready**
- ✅ Uses standard Python packaging metadata
- ✅ Compatible with pip, poetry, and other tools
- ✅ No external dependencies for version detection

### **4. Automation-Friendly**
- ✅ Workflows only need to update `pyproject.toml`
- ✅ All other files automatically get correct version
- ✅ No manual synchronization in CI/CD

## 🧪 **Testing Scenarios**

### **Scenario 1: Version Update**
```bash
# 1. Update ONLY pyproject.toml
sed -i 's/version = "3.1.0b2"/version = "3.2.0"/' pyproject.toml

# 2. Reinstall package
poetry install

# 3. All version references updated automatically
poetry run python -c "from classdock import __version__; print(__version__)"
# → "3.2.0"

poetry run classdock --version  
# → "ClassDock v3.2.0"
```

### **Scenario 2: Development Mode**
```bash
# Without installing package, version still works
cd /tmp
python -c "
import sys
sys.path.insert(0, '/path/to/classdock')
from classdock import __version__
print(__version__)
"
# → "3.2.0.dev"
```

## 🔄 **Migration Guide**

### **Old Workflow (3 places to update)**
```bash
# 1. Update pyproject.toml
sed -i 's/version = "3.1.0b2"/version = "3.2.0"/' pyproject.toml

# 2. Update __init__.py  
sed -i 's/__version__ = "3.1.0b2"/__version__ = "3.2.0"/' __init__.py

# 3. Update cli.py
sed -i 's/v3.1.0b2/v3.2.0/' cli.py

# Risk: Forgetting one place = version mismatch 😞
```

### **New Workflow (1 place only)**
```bash
# 1. Update ONLY pyproject.toml
sed -i 's/version = "3.1.0b2"/version = "3.2.0"/' pyproject.toml

# 2. Reinstall if needed
poetry install

# Done! All other files automatically use new version ✅
```

## 🎯 **Summary**

- **🎯 Single Source**: `pyproject.toml` is the ONLY place to define version
- **🔄 Dynamic Loading**: All other files read version automatically  
- **🛡️ Fallback System**: Works in both production and development
- **🚀 Zero Maintenance**: No more version synchronization issues

**Result**: Update version in ONE place, everything else just works! 🚀

---

*This system eliminates version management headaches and ensures consistency across all components.*