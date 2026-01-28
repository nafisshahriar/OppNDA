# OppNDA Modern UI - Quick Reference Guide

## 🎯 Quick Start for Developers

### Installation
No additional dependencies required. All libraries already included in the project.

### Integration Points

#### 1. Pattern Builder
```javascript
// Already initialized in settings.html
// Components are draggable in the UI
// Pattern auto-saves via auto-save manager

// To customize presets, edit pattern-builder.js:
window.patternPresets = {
    'standard': ['scenario', 'router', 'seed', 'ttl', 'buffer', 'report'],
    'simple': ['scenario', 'router'],
    'custom': []
};
```

#### 2. Directory Browser
```javascript
// Usage in HTML:
<button onclick="openDirectoryBrowser('analysis')">Browse</button>

// JavaScript:
const browser = new DirectoryBrowser('containerId', {
    filterType: 'dirs',
    onSelectPath: (path) => {
        console.log('Selected:', path);
        markDirty('analysis', 'output_path', path);
    }
});
browser.browse('/some/path');
```

#### 3. Auto-Save
```javascript
// Already running globally
// To register a form element:
registerAutoSave(inputElement, 'analysis', 'field_name');

// Or manually trigger:
await triggerSave('analysis');
await saveAllChanges();
```

#### 4. Path Utilities (Python)
```python
from core.path_utils import resolve_absolute_path, validate_path

# Resolve paths
abs_path = resolve_absolute_path('~/my_config')

# Validate paths
is_valid, error = validate_path(abs_path, must_exist=True, must_be_dir=True)
```

---

## 📚 API Quick Reference

### `/api/browse-directory` (POST)
```json
// Request
{
    "path": "/home/user",
    "filter_type": "dirs"
}

// Response
{
    "success": true,
    "current_path": "/home/user",
    "directories": [{"name": "folder", "path": "/home/user/folder"}],
    "files": [{"name": "file.txt", "path": "...", "size": 1024}],
    "parent_path": "/home"
}
```

### `/api/resolve-path` (POST)
```json
// Request
{"path": "~/config"}

// Response
{
    "success": true,
    "absolute_path": "/home/user/config",
    "exists": true,
    "is_dir": true,
    "is_file": false
}
```

### `/api/save-config` (POST)
```json
// Request
{
    "config": "analysis",
    "changes": {"field": "value"}
}

// Response
{
    "success": true,
    "message": "analysis config auto-saved"
}
```

---

## 🛠️ Common Tasks

### Add Auto-Save to a Form
```html
<!-- Add data attributes -->
<input type="text" id="outputPath" name="output_path" 
       data-config="analysis" data-field="output_path">

<!-- JavaScript -->
<script>
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('outputPath');
    registerAutoSave(input, 'analysis', 'output_path');
});
</script>
```

### Open Directory Browser
```javascript
function openDirBrowser() {
    const browser = new DirectoryBrowser('browserContainer', {
        initialPath: '/home/user',
        filterType: 'all',
        onSelectPath: (path) => {
            document.getElementById('pathInput').value = path;
            markDirty('myConfig', 'path', path);
        }
    });
    browser.browse();
}
```

### Validate a User Path
```python
from core.path_utils import resolve_absolute_path, validate_path

user_input = request.json.get('path')
abs_path = resolve_absolute_path(user_input)

is_valid, error = validate_path(abs_path, must_exist=True)
if not is_valid:
    return jsonify({'error': error}), 400

# Use abs_path safely
```

### Handle Large Directories
```javascript
// For directories with >1000 items, add pagination:
const browser = new DirectoryBrowser('container', {
    filterType: 'dirs',
    pageSize: 50  // Add pagination support (future)
});
```

---

## 🐛 Debugging Tips

### Check Auto-Save Status
```javascript
// In browser console:
console.log(autoSaveManager.getHistory());
console.log(autoSaveManager.getPendingChanges('analysis'));
console.log(autoSaveManager.getLastSaveTime('analysis'));
```

### Test API Endpoints
```javascript
// Test directory browse:
fetch('/api/browse-directory', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path: '/home', filter_type: 'dirs'})
}).then(r => r.json()).then(console.log);

// Test path resolve:
fetch('/api/resolve-path', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path: '~'})
}).then(r => r.json()).then(console.log);
```

### Monitor Path Operations
```python
# Add logging to path_utils.py:
import logging
logging.basicConfig(level=logging.DEBUG)

# Then use:
logger = logging.getLogger(__name__)
logger.debug(f'Resolving path: {path}')
```

---

## 📝 Common Issues & Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Pattern builder not showing | Script not loaded | Check `pattern-builder.js` in settings.html |
| Directory browser empty | Path doesn't exist | Verify path and permissions |
| Auto-save not working | API error | Check `/api/save-config` accessibility |
| Paths show as relative | Not using resolve function | Use `resolve_absolute_path()` |
| Styles look broken | CSS not loaded | Check `settings-modern.css` link |

---

## 🔧 Configuration Options

### Auto-Save Tuning
```javascript
// In GUI/auto-save.js, modify:
const autoSaveManager = new AutoSaveManager({
    debounceDelay: 1500,        // ms - increase for slower connections
    endpoint: '/api/save-config',
    maxHistory: 10              // number of saves to track
});
```

### Pattern Builder Customization
```javascript
// In GUI/pattern-builder.js, modify:
const patternBuilder = new PatternBuilder({
    delimiter: '_',             // change separator
    components: [               // add/remove components
        'scenario', 'router', 'seed', 'ttl', 'buffer', 'report'
    ]
});
```

### Directory Browser Options
```javascript
new DirectoryBrowser('container', {
    initialPath: '~',           // starting directory
    filterType: 'dirs',         // 'dirs', 'files', or 'all'
    onSelectPath: callback,     // function(path)
    allowMultiSelect: false     // enable multi-select
});
```

---

## 📊 Performance Tips

1. **Large Directories**: Consider paginating if >1000 items
2. **Auto-Save Frequency**: 1.5s is optimal (don't reduce below 1s)
3. **Path Resolution**: Cache results if resolving same paths repeatedly
4. **CSS**: Don't modify both `settings.css` and `settings-modern.css` - use modern one

---

## 🚀 Production Deployment

### Pre-Deployment Checklist
- [ ] Run `python tests/test_modern_ui.py`
- [ ] Clear browser cache on production
- [ ] Verify all API endpoints accessible
- [ ] Test with real data
- [ ] Check file permissions on server
- [ ] Monitor auto-save logs
- [ ] Test on target browsers

### Deployment Steps
1. Copy all new files to production
2. Update `settings.html` with correct paths
3. Restart Flask application
4. Clear client-side cache
5. Test all features
6. Monitor error logs

---

## 📖 File Structure Reference

```
OppNDA/
├── GUI/
│   ├── pattern-builder.js          ← Drag-drop builder
│   ├── directory-browser.js        ← File browser
│   ├── directory-browser.css       ← Browser styling
│   ├── auto-save.js                ← Auto-save manager
│   ├── settings-modern.css         ← Modern styling
│   └── settings.html               ← Integrated HTML
├── core/
│   └── path_utils.py               ← Path utilities
├── app/
│   └── api.py                      ← API endpoints
├── tests/
│   └── test_modern_ui.py           ← Test suite
├── MODERN_UI_GUIDE.md              ← Feature docs
├── IMPLEMENTATION_SUMMARY.md       ← Tech details
└── DELIVERY_CHECKLIST.md           ← Delivery info
```

---

## 🔗 Related Documentation

- **Full Guide**: See `MODERN_UI_GUIDE.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Testing**: See `tests/test_modern_ui.py`
- **Deployment**: See `DELIVERY_CHECKLIST.md`

---

## 💡 Tips & Tricks

### Forcing Auto-Save Immediately
```javascript
await autoSaveManager.saveConfig('analysis');
```

### Getting Current Pattern
```javascript
const currentPattern = autoSaveManager.getPendingChanges('pattern');
```

### Refreshing Directory Browser
```javascript
browser.browse(browser.currentPath);
```

### Batch Updates
```javascript
// Mark multiple fields dirty
markDirty('config', 'field1', value1);
markDirty('config', 'field2', value2);
// Both save together after debounce delay
```

### Testing Path Resolution Locally
```javascript
fetch('/api/resolve-path', {
    method: 'POST',
    body: JSON.stringify({path: process.env.HOME || '~'})
}).then(r => r.json()).then(d => console.log(d.absolute_path));
```

---

## ✅ Verification Checklist

After deployment, verify:
- [ ] Pattern builder drag-drop works
- [ ] Directory browser navigates correctly
- [ ] Auto-save triggers silently
- [ ] CSS styling applies correctly
- [ ] Path resolution works for relative paths
- [ ] No console errors in browser
- [ ] All API endpoints respond
- [ ] File operations succeed

---

**Version**: OppNDA 2.0+  
**Last Updated**: 2024  
**Status**: Production Ready ✅
