<div align="center">

# ⬢ Kepler‑404

### AI‑Driven Super‑Resolution & Colorization of Landsat 9 TIR Imagery

*Upscaling 200m thermal data to 100m with generative AI — translating monochrome heat into physically‑consistent RGB.*

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-00ff88)](#)
[![Status](https://img.shields.io/badge/Status-Prototype-00ff88)](#)

**ISRO · Space Applications Centre (SAC) · BAH 2026 Hackathon**

</div>

---

## 📖 Overview

**Kepler‑404** is a full‑stack prototype that enhances **Thermal Infrared (TIR)** satellite imagery captured by the **Landsat 9 TIRS** sensor. Thermal bands (Band 10) are captured at a coarse **100m** native resolution — limiting fine‑grained analysis of urban heat islands, volcanic activity, ocean fronts, and wildfire dynamics.

Kepler‑404 uses a **generative AI pipeline** to:

1. **Super‑resolve** the low‑resolution TIR input from **200m → 100m** spatial resolution.
2. **Colorize** the monochrome thermal data into a **realistic RGB composite** using learned thermal‑to‑visible mappings.
3. **Preserve geospatial integrity** — output GeoTIFFs retain their original CRS and affine transform, ready for QGIS/ArcGIS.

> ⚠️ **Prototype note:** This build uses a **mock inference layer** (OpenCV resize + Inferno colormap) that mirrors the real model's I/O contract exactly. Swapping in PyTorch **ESRGAN/SwinIR** and **Pix2Pix/Diffusion** checkpoints is a drop‑in replacement — see [🔌 Integrating Real Models](#-integrating-real-models).

---

## ✨ Key Features

| Area | Capability |
|------|-----------|
| 🎨 **Frontend** | Glassmorphism "Mission Control" UI, custom cursor, particle network hero, dark/light themes |
| 🚀 **Pipeline** | End‑to‑end flow: upload → ingest → super‑resolve → colorize → export |
| 🗺️ **Geospatial** | Full CRS + affine transform preservation on GeoTIFF export |
| 🖼️ **Comparison** | Interactive 3‑way before/after slider (Original · Super‑Resolved · Colorized) |
| 📊 **Telemetry** | Live job metadata — input/output dims, CRS, elapsed time, job ID |
| ⬇️ **Export** | One‑click download of processed **PNG** and georeferenced **GeoTIFF** |
| 📱 **Responsive** | Fully fluid across desktop, tablet, and mobile |
| ♿ **Accessible** | Keyboard‑navigable, ARIA labels, `prefers-reduced-motion` support |

---

## 🧠 The AI Pipeline

```
┌──────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  01 INGEST   │ ─► │  02 SUPER‑RES    │ ─► │  03 COLORIZE    │ ─► │  04 GEO‑EXPORT   │
│  GeoTIFF +   │    │  ESRGAN / SwinIR │    │  Pix2Pix /      │    │  Colorized 100m  │
│  metadata    │    │  200m → 100m     │    │  Diffusion      │    │  GeoTIFF (CRS    │
│              │    │                  │    │  thermal→RGB    │    │  preserved)      │
└──────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
```

| Stage | Description |
|-------|-------------|
| **01 · Data Ingest** | Reads single‑channel Landsat 9 Band 10 (TIR) GeoTIFFs while preserving CRS, transform, and metadata. |
| **02 · Super‑Resolution** | Generative AI (ESRGAN / SwinIR) upscales structural detail to 100m, retaining thermal integrity and edge fidelity. |
| **03 · Colorization** | Maps thermal signatures to RGB via Pix2Pix/Diffusion models trained on paired TIR+RGB datasets. |
| **04 · Geospatial Export** | Writes colorized 100m GeoTIFFs with preserved CRS and affine transform for QGIS/ArcGIS overlay. |

### 🧪 Physics‑Informed Bonus

The framework is designed to integrate **blackbody radiation laws** into the neural loss function — ensuring generated RGB values are *physically consistent* with measured thermal radiation, not just visually plausible.

---

## 🏗️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python · Flask · Flask‑CORS |
| **Geospatial** | Rasterio · GDAL · Affine transforms |
| **Image Processing** | OpenCV · NumPy · Pillow |
| **ML (target)** | PyTorch · ESRGAN · SwinIR · Pix2Pix · Diffusion |
| **Frontend** | HTML5 · CSS3 (custom properties) · Vanilla JS (ES6) |
| **UI Library** | Font Awesome · Google Fonts (Inter, JetBrains Mono) |

---

## 📁 Project Structure

```
Kepler‑404/
├── app.py                    # Flask server + inference pipeline
├── requirements.txt          # Python dependencies
├── README.md
│
├── templates/
│   └── index.html            # Main UI (header, hero, demo, FAQ, footer)
│
├── static/
│   ├── css/
│   │   └── style.css         # Full design system (themes, responsive, animations)
│   │
│   └── js/
│       └── script.js         # Cursor, particles, nav, FAQ, upload, 3‑way compare
│
├── uploads/                  # ⬆️ Incoming GeoTIFFs (auto‑purged after 24h)
│   └── .gitkeep
│
└── static/results/           # 🖼️ Processed outputs (PNG + GeoTIFF, auto‑purged 24h)
    └── .gitkeep
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **pip** (comes with Python)

### 1 · Clone & enter

```bash
git clone https://github.com/<your‑org>/Kepler‑404.git
cd Kepler‑404
```

### 2 · Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3 · Install dependencies

```bash
pip install -r requirements.txt
```

### 4 · Run the server

```bash
python app.py
```

### 5 · Open the app

```
http://127.0.0.1:5000
```

> 💡 **Debug mode is ON** (`debug=True`) for the hackathon — Flask will **auto‑reload** on any code/HTML/CSS/JS edit. No restart needed.

---

## 🔌 API Reference

### `POST /api/infer`

Process an uploaded TIR image through the full pipeline.

**Request** — `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | `File` | `.tif`, `.tiff`, `.png`, `.jpg`, or `.jpeg` (max 50 MB) |

**Response `200`** — `application/json`

```json
{
  "success": true,
  "images": {
    "input":     "/static/results/<job_id>_input.png",
    "sr":        "/static/results/<job_id>_sr.png",
    "colorized": "/static/results/<job_id>_colorized.png"
  },
  "download":     "/api/download/<job_id>_colorized.png",
  "download_tif": "/api/download/<job_id>_colorized.tif",
  "meta": {
    "job_id":     "a1b2c3d4e5f6...",
    "input_size": "256×256",
    "output_size":"512×512",
    "crs":        "EPSG:32643",
    "elapsed":    "2.6",
    "file_type":  "GeoTIFF"
  }
}
```

> ℹ️ For plain images (`.png`/`.jpg`), `download_tif` is `null` (no georeferencing data exists) and `file_type` is `"Image"`.

**Error responses** — `400 / 415 / 500`

```json
{ "success": false, "error": "Invalid file format. Please upload a .tif, .tiff, .png, .jpg, or .jpeg file." }
```

---

### `GET /api/download/<filename>`

Download a processed result file.

| Parameter | Values |
|-----------|--------|
| `filename` | `<job_id>_input.png` · `<job_id>_sr.png` · `<job_id>_colorized.png` · `<job_id>_colorized.tif` |

Returns the file as an attachment (`Content-Disposition: attachment`).

---

## 🎛️ Frontend Features

- **Custom cursor** — dot + lerp‑smoothed outline that grows on hoverable elements (auto‑disabled on touch).
- **Particle network hero** — interactive canvas with mouse repulsion and connection lines.
- **Theme toggle** — dark/light, persisted in `localStorage`.
- **Mobile nav** — slide‑in drawer with overlay + ESC‑to‑close.
- **Scroll choreography** — progress bar, header shadow, back‑to‑top, active‑section highlight.
- **FAQ accordion** — single‑open pattern with smooth expand.
- **Upload demo** — drag‑drop + click + sample chips, with dynamic progress driven by the **actual server response**.
- **3‑way comparison slider** — pointer + keyboard accessible, click‑to‑move handle.
- **Toast notifications** — auto‑dismissing success/error feedback.
- **Offline fallback** — if the backend is unreachable, the UI shows a clearly‑labeled preview mode instead of breaking.

---

## 🔌 Integrating Real Models

The mock layer in `app.py` is structured to be a **drop‑in swap** for real ML models. Replace the three functions in [`app.py`](./app.py):

```python
# ── CURRENT (mock) ──────────────────────────────────────────
def super_resolve(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape[:2]
    return cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)

def colorize(gray: np.ndarray) -> np.ndarray:
    return cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)


# ── TARGET (real models) ────────────────────────────────────
import torch
from models import ESRGANModel, Pix2PixModel  # your checkpoints

_device = "cuda" if torch.cuda.is_available() else "cpu"
_sr_model = ESRGANModel("weights/esrgan_b10.pt").to(_device).eval()
_color_model = Pix2PixModel("weights/pix2pix_b10.pt").to(_device).eval()

def super_resolve(gray: np.ndarray) -> np.ndarray:
    t = torch.from_numpy(gray).float().div(255).unsqueeze(0).unsqueeze(0).to(_device)
    with torch.no_grad():
        out = _sr_model(t)
    return (out.squeeze().cpu().numpy() * 255).clip(0, 255).astype(np.uint8)

def colorize(gray: np.ndarray) -> np.ndarray:
    t = torch.from_numpy(gray).float().div(255).unsqueeze(0).unsqueeze(0).to(_device)
    with torch.no_grad():
        rgb = _color_model(t)                 # 1×3×H×W
    rgb = rgb.squeeze().permute(1, 2, 0).cpu().numpy()
    return cv2.cvtColor((rgb * 255).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
```

Uncomment `torch` in [`requirements.txt`](./requirements.txt), add your weights under `weights/`, and the rest of the pipeline (API, frontend, exports) works unchanged.

---

## 📐 Assumptions & Constraints

| Constraint | Value | Why |
|-----------|-------|-----|
| Max file size | **50 MB** | Prevents OOM during inference |
| Accepted formats | `.tif` · `.tiff` · `.png` · `.jpg` · `.jpeg` | GeoTIFF for real scenes, images for quick testing |
| Upscale factor | **2×** (200m → 100m) | Matches Landsat 9 TIRS spec |
| File retention | **24 hours** | Auto‑purged uploads/results at server start |
| Colorization model | **Inferno colormap (mock)** | Placeholder for Pix2Pix/Diffusion |
| Port | **5000** | Configurable in `app.py` |
| Mock delay | **2.5s** | Simulates inference latency; remove for production |

---

## 🛠️ Development Notes

- **File retention**: Uploads and results are intentionally **not deleted immediately** so they can be inspected live during a demo. `purge_stale()` runs at server start and removes anything older than 24h.
- **CRS handling**: GeoTIFF inputs preserve their CRS and transform through the entire pipeline. Plain images report `"Unknown"` CRS and skip the GeoTIFF export.
- **CORS**: Enabled globally via `flask-cors` for development convenience.
- **Frontend paths**: The HTML uses `static/css/style.css` and `static/js/script.js` (plain paths). For strict Flask usage, swap to `{{ url_for('static', filename='...') }}`.

---

## 🧭 Roadmap

- [x] End‑to‑end backend ↔ frontend data flow
- [x] GeoTIFF georeferenced export with preserved CRS
- [x] Interactive 3‑way comparison slider
- [x] PNG + GeoTIFF download
- [ ] Integrate real ESRGAN/SwinIR super‑resolution checkpoint
- [ ] Integrate Pix2Pix/Diffusion colorization checkpoint
- [ ] Physics‑informed (blackbody) loss function
- [ ] SSIM/PSNR metrics panel for generated outputs
- [ ] Batch processing & history gallery
- [ ] Streaming progress (SSE/WebSocket) for true % reporting

---

## 📜 License

Released under the **MIT License**.

---

<div align="center">

**Built for the ISRO · SAC BAH 2026 Hackathon**

⬢ **Kepler‑404** · *Where thermal silence becomes visual signal.*

</div>
