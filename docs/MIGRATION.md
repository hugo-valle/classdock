# Migration Guide: classroom-pilot → classdock

## For Existing Users

### Update Installation

If you have `classroom-pilot` installed, uninstall it and install `classdock`:

```bash
pip uninstall classroom-pilot
pip install classdock
```

### Update Commands

All commands now use `classdock` instead of `classroom-pilot`:

```bash
# Old: classroom-pilot assignments setup
# New: classdock assignments setup

# Old: classroom-pilot repos fetch
# New: classdock repos fetch

# Old: classroom-pilot secrets add
# New: classdock secrets add

# Old: classroom-pilot automation cron-install
# New: classdock automation cron-install
```

### Update Scripts and Code

If you have Python scripts that import the package, update your imports:

```python
# Old imports
from classroom_pilot import ConfigLoader
from classroom_pilot.config import ConfigValidator
from classroom_pilot.utils import setup_logging

# New imports
from classdock import ConfigLoader
from classdock.config import ConfigValidator
from classdock.utils import setup_logging
```

### Update Module Execution

If you run the package as a module:

```bash
# Old: python -m classroom_pilot
# New: python -m classdock
```

### Configuration Files

**Good news!** Your existing `assignment.conf` files remain fully compatible. No changes needed to your configuration files.

### Cron Jobs

If you have cron jobs set up with the old package name, you'll need to update them:

```bash
# Remove old cron jobs
classdock automation cron-remove

# Reinstall with new package name
classdock automation cron-install --config path/to/assignment.conf
```

The cron jobs will automatically use the new `classdock` command.

## Why ClassDock?

The rebrand from "classroom-pilot" to "classdock" brings several benefits:

### Shorter, More Memorable

- **Before**: `classroom-pilot` (16 characters)
- **After**: `classdock` (9 characters)
- Faster to type, easier to remember

### Modern CLI Conventions

Modern CLI tools favor short, punchy names:
- `docker`, `kubectl`, `gh`, `npm`
- `classdock` fits this pattern better than `classroom-pilot`

### Fresh Identity

- New branding for continued development
- Clean slate for version numbering (starting at 0.1.0)
- Better aligns with the tool's purpose: "docking" your classroom assignments

## What's the Same?

Everything that matters:

✅ **All functionality** - Every feature works exactly as before
✅ **Configuration files** - Your `assignment.conf` files are fully compatible
✅ **Workflow patterns** - Same command structure and usage patterns
✅ **GitHub integration** - Same GitHub API capabilities
✅ **Secret management** - Identical secret deployment mechanisms
✅ **Automation** - Same cron scheduling capabilities

The only changes are the package name, CLI command, and Python imports.

## Version Reset

ClassDock starts at version **0.1.0** to signal a fresh beginning:

- **classroom-pilot**: ended at v3.1.2
- **classdock**: starts at v0.1.0

This is a **semantic rebrand** - the version reset indicates a branding change, not a feature rollback. All features from classroom-pilot v3.1.2 are present in classdock v0.1.0.

## Timeline

- **classroom-pilot v3.1.3**: Published with deprecation notice (legacy support only)
- **classdock v0.1.0**: Initial release with full feature set
- **Future**: Active development continues under the ClassDock name

## Support

The old `classroom-pilot` package remains available on PyPI with a deprecation notice, but will receive limited updates. All future development happens in `classdock`.

## Questions?

If you encounter any issues during migration:

1. Check this migration guide
2. Review the [ClassDock documentation](https://github.com/hugo-valle/classdock#readme)
3. Open an issue on [GitHub](https://github.com/hugo-valle/classdock/issues)

## Quick Reference

| Aspect | classroom-pilot | classdock |
|--------|----------------|-----------|
| PyPI Package | `pip install classroom-pilot` | `pip install classdock` |
| CLI Command | `classroom-pilot` | `classdock` |
| Python Import | `from classroom_pilot` | `from classdock` |
| Module Run | `python -m classroom_pilot` | `python -m classdock` |
| GitHub Repo | `hugo-valle/classroom-pilot` | `hugo-valle/classdock` |
| Config Files | `assignment.conf` | `assignment.conf` (unchanged) |
| Version | v3.1.2 | v0.1.0 |
