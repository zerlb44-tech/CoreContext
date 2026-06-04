# PyPI Release Guide

To publish CoreContext on PyPI:

## Prerequisites

```bash
pip install build twine
```

## Steps

1. **Update version** in `pyproject.toml`:
   ```toml
   [tool.poetry]
   version = "0.1.0"
   ```

2. **Update CHANGELOG.md** with new version and changes

3. **Build distribution**:
   ```bash
   python -m build
   ```
   This creates `dist/corecontext-0.1.0-py3-none-any.whl` and `dist/corecontext-0.1.0.tar.gz`

4. **Create PyPI account** at https://pypi.org/account/register/

5. **Create `.pypirc`** in home directory (optional, for authentication):
   ```ini
   [distutils]
   index-servers =
       pypi

   [pypi]
   repository = https://upload.pypi.org/legacy/
   username = your_username
   ```

6. **Upload to TestPyPI** (first time):
   ```bash
   twine upload --repository testpypi dist/*
   ```
   Test: `pip install -i https://test.pypi.org/simple/ corecontext`

7. **Upload to PyPI** (production):
   ```bash
   twine upload dist/*
   ```

8. **Verify**:
   ```bash
   pip install corecontext
   corecontext --help
   ```

## After Release

- Tag the release: `git tag v0.1.0`
- Push tag: `git push origin v0.1.0`
- GitHub will auto-create a release

## Checklist

- [ ] Version updated
- [ ] CHANGELOG updated
- [ ] All tests passing
- [ ] Build successful
- [ ] PyPI account ready
- [ ] Upload successful
- [ ] Installation test passed
- [ ] Git tag created
