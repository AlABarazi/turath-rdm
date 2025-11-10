# Mirador Integration - Deep Research Findings

**Date**: November 7, 2025  
**Researcher**: Cascade AI  
**Objective**: Understand how to properly integrate Mirador viewer into InvenioRDM v13

---

## 🔍 Key Discoveries

### 1. **Zenodo RDM's Working Implementation**

Zenodo RDM (which runs on InvenioRDM v21.2.x ~ v13) has a **fully functional** Mirador integration using a **custom previewer** (NOT a separate package).

**Location**: `/site/zenodo_rdm/previewer/image_previewer.py`

**Registration Method** (`pyproject.toml` line 78-79):
```toml
[project.entry-points."invenio_previewer.previewers"]
image_previewer = "zenodo_rdm.previewer.image_previewer"
```

**Key Code Patterns from Zenodo**:

```python
def preview(file):
    """Render template."""
    record = file.record._record
    tpl_ctx = {}
    
    # Line 117: Uses InvenioRDM's BUILT-IN manifest link!
    tpl_ctx["iiif_manifest_url"] = file.record["links"]["self_iiif_manifest"]
    tpl_ctx["iiif_canvas_url"] = file.data["links"]["iiif_canvas"]
    tpl_ctx["mirador_cfg"] = deepcopy(current_app.config["MIRADOR_PREVIEW_CONFIG"])
    
    # Line 121-139: Handles annotations (.wadm files)
    annotations = {}
    for file_list, base_url in [(record.files, "files"), (record.media_files, "media_files")]:
        for filename in file_list:
            if filename.endswith(".wadm"):
                main_filename = filename[:-5]
                if main_filename in record.files or main_filename in record.media_files:
                    annotations[main_filename] = f"{file.record['links'][base_url]}/{filename}/content"
    
    # Line 169-174: Renders with standard InvenioRDM previewer template
    return render_template(
        "invenio_app_rdm/records/previewers/mirador_preview.html",
        css_bundles=["image-previewer.css"],
        file=file,
        **tpl_ctx,
    )
```

**Configuration** (`invenio.cfg` line 1090-1142):
```python
PREVIEWER_PREFERENCE = [
    "csv_papaparsejs",
    "pdfjs",
    "image_previewer",  # Custom Mirador previewer
    # ... other previewers
]

MIRADOR_PREVIEW_EXTENSIONS = ["pdf", "png", "jp2", "jpeg", "jpg", "tif", "tiff"]

MIRADOR_PREVIEW_CONFIG = {
    "window": {
        "allowClose": False,
        "allowFullscreen": True,
        "defaultView": "single",
        "panels": {
            "info": True,
            "annotations": False,
            "search": False,
        },
    },
    "workspace": {
        "draggingEnabled": True,
        "showZoomControls": True,
        "height": 4000,
    },
}
```

**Template** (`mirador_preview.html`):
```html
{% extends config.PREVIEWER_ABSTRACT_TEMPLATE %}

{% block panel %}
{% if show_mirador %}
  <div id="m3-dist"
    data-canvas='{{ iiif_canvas_url }}'
    data-config='{{ mirador_cfg | tojson }}'
    data-manifest='{{ iiif_manifest_url }}'
    data-annotations='{{ annotations | tojson }}'
  >
    <p>{{ _("Loading...") }}</p>
  </div>
{% endif %}
{% endblock %}

{% block javascript %}
{% if show_mirador %}
  <script src="{{ url_for('static', filename='js/mirador3-dist/main.js') }}"></script>
{% endif %}
{% endblock javascript %}
```

---

### 2. **V12 Package vs Zenodo Approach**

#### V12 Package Structure:
- **Entry Points** (setup.py line 27-30):
  ```python
  "invenio_base.apps": [
      "invenio_previewer_mirador = invenio_previewer_mirador:InvenioPreviewerMirador",
  ],
  "invenio_previewer.previewers": [
      "mirador = invenio_previewer_mirador.previewer:mirador_previewer"
  ],
  ```

- **Problem**: The package was designed for uploaded `manifest.json` files, NOT dynamic manifests
- **Code Pattern**:
  ```python
  # Line 117-119: Fetches uploaded manifest content
  content_url = file.data.get("links", {}).get("content")
  manifestId: "{{ file.data.links.content }}"  # Template line 23
  ```

#### Zenodo Approach:
- **NO separate extension app** - just a previewer entry point
- **Uses InvenioRDM's built-in IIIF system**:
  ```python
  file.record["links"]["self_iiif_manifest"]  # Dynamic manifest!
  ```

---

### 3. **InvenioRDM v13 IIIF Support**

InvenioRDM v13 **has built-in IIIF manifest generation**!

**Verified in**:
- `/turath-rdm/.venv/lib/python3.12/site-packages/invenio_rdm_records/services/config.py` (line 697):
  ```python
  "self_iiif_manifest": EndpointLink(
      "iiif.manifest", params=["uuid"], vars=vars_self_iiif
  ),
  ```

**This means**:
- Every record with files automatically gets: `record["links"]["self_iiif_manifest"]`
- Endpoint pattern: `/api/iiif/record:<PID>/manifest`
- Example: `https://127.0.0.1:5000/api/iiif/record:1ank1-xn122/manifest`

---

## 🎯 The Solution: Zenodo-Style Implementation

### **Why This is the Correct Approach**:

1. ✅ **No v12→v13 migration needed** - start fresh with v13 patterns
2. ✅ **Uses InvenioRDM's built-in features** - no fighting the system
3. ✅ **Proven to work** - Zenodo RDM is production-ready
4. ✅ **Simpler** - no separate extension app, just a previewer
5. ✅ **Maintainable** - follows InvenioRDM conventions

---

## 📋 Implementation Plan

### **Step 1: Create Custom Previewer in Site Package**

**Location**: `site/turath_inveniordm/previewer/mirador_previewer.py`

**Code Structure** (adapted from Zenodo):
```python
from flask import current_app, render_template

def can_preview(file):
    """Check if file can be previewed with Mirador."""
    # Support TIFF, PDF, and other IIIF-compatible formats
    supported_extensions = current_app.config.get(
        "MIRADOR_PREVIEW_EXTENSIONS", 
        [".pdf", ".tif", ".tiff", ".jp2", ".jpeg", ".jpg", ".png"]
    )
    return file.has_extensions(*supported_extensions)

def preview(file):
    """Render Mirador preview."""
    record = file.record._record
    
    # Use InvenioRDM's built-in dynamic manifest
    manifest_url = file.record["links"]["self_iiif_manifest"]
    mirador_config = current_app.config.get("MIRADOR_PREVIEW_CONFIG", {})
    
    return render_template(
        "invenio_app_rdm/records/previewers/mirador_preview.html",
        css_bundles=["mirador-previewer.css"],
        file=file,
        iiif_manifest_url=manifest_url,
        mirador_cfg=mirador_config,
        show_mirador=True,
    )
```

---

### **Step 2: Register Previewer**

**Location**: `site/pyproject.toml`

**Add Entry Point**:
```toml
[project.entry-points."invenio_previewer.previewers"]
mirador_previewer = "turath_inveniordm.previewer.mirador_previewer"
```

---

### **Step 3: Create Template**

**Location**: `site/turath_inveniordm/templates/semantic-ui/invenio_app_rdm/records/previewers/mirador_preview.html`

**Content** (from Zenodo):
```html
{%- extends config.PREVIEWER_ABSTRACT_TEMPLATE %}

{% block panel %}
{% if show_mirador %}
  <div id="m3-dist"
    data-config='{{ mirador_cfg | tojson }}'
    data-manifest='{{ iiif_manifest_url }}'
  >
    <p>{{ _("Loading Mirador viewer...") }}</p>
  </div>
{% endif %}
{% endblock %}

{% block javascript %}
{% if show_mirador %}
  <script src="{{ url_for('static', filename='js/mirador3/mirador.min.js') }}"></script>
  <script>
    // Mirador initialization will happen here
    // Read config from data attributes
  </script>
{% endif %}
{% endblock javascript %}
```

---

### **Step 4: Add Configuration**

**Location**: `site/turath_inveniordm/config.py`

**Add Settings**:
```python
# Mirador Previewer Configuration
PREVIEWER_PREFERENCE = [
    "csv_papaparsejs",
    "pdfjs",
    "mirador_previewer",  # Our custom Mirador previewer
    "json_prismjs",
    "simple_image",
    "txt",
    "mistune",
    "zip",
]

MIRADOR_PREVIEW_EXTENSIONS = [".pdf", ".tif", ".tiff", ".jp2", ".jpeg", ".jpg", ".png"]

MIRADOR_PREVIEW_CONFIG = {
    "window": {
        "allowClose": False,
        "allowFullscreen": True,
        "allowMaximize": False,
        "defaultView": "single",
        "panels": {
            "info": True,
            "annotations": False,
            "search": False,
        },
    },
    "workspace": {
        "showZoomControls": True,
    },
}
```

---

### **Step 5: Add Mirador Assets**

**Option A: CDN** (easiest for testing):
```html
<script src="https://cdn.jsdelivr.net/npm/mirador@latest/dist/mirador.min.js"></script>
```

**Option B: Local Assets** (production):
1. Download Mirador from: https://github.com/ProjectMirador/mirador/releases
2. Place in: `site/turath_inveniordm/assets/js/mirador3/`
3. Build with Webpack

---

## ✅ Why This Will Work

1. **InvenioRDM already generates manifests** - we just use them
2. **Entry point system is standard** - Zenodo proves it works in v13
3. **Template system is proven** - extends `PREVIEWER_ABSTRACT_TEMPLATE`
4. **No dependency conflicts** - no external packages needed
5. **Follows InvenioRDM patterns** - maintainable and upgradable

---

## 🚫 What NOT to Do

1. ❌ **Don't try to update v12 package** - too much has changed
2. ❌ **Don't create template overrides in wrong location** - infinite loops
3. ❌ **Don't hardcode manifest URLs** - use `file.record["links"]["self_iiif_manifest"]`
4. ❌ **Don't add unnecessary extensions** - just the previewer entry point is enough

---

## 📚 References

- **Zenodo RDM Source**: `/Users/alaaalbarazi/Projects/Turath/zenodo-rdm-21.2.1/site/zenodo_rdm/previewer/image_previewer.py`
- **InvenioRDM IIIF Config**: `.venv/lib/python3.12/site-packages/invenio_rdm_records/services/config.py:697`
- **InvenioRDM Previewer Docs**: https://invenio-previewer.readthedocs.io/
- **Mirador Documentation**: https://projectmirador.org/

---

## 🎯 Next Steps

1. Create `site/turath_inveniordm/previewer/` directory
2. Implement `mirador_previewer.py` (copy Zenodo pattern)
3. Add entry point in `site/pyproject.toml`
4. Create template in correct location
5. Add config to `site/turath_inveniordm/config.py`
6. Test with record: `1ank1-xn122`
7. Install site package: `pipenv install -e site`
8. Restart InvenioRDM
9. Verify Mirador loads for PDF/TIFF files

---

**Estimated Time**: 2-3 hours (clean implementation following Zenodo pattern)

**Success Criteria**:
- ✅ Mirador viewer appears when viewing PDF files
- ✅ Uses dynamic manifest endpoint
- ✅ No package conflicts
- ✅ No template recursion errors
- ✅ System remains stable and maintainable
