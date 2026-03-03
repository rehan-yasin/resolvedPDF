# 📄 Resolved → PDF Converter Plugin

Convert `.resolved` Markdown files into beautifully styled PDFs with a single click.

---

## 🚀 Quick Start

### 1. Install Python (if not installed)
Download Python 3.10+ from [python.org](https://python.org). Make sure to check **"Add Python to PATH"** during install.

### 2. Install Dependencies
```bash
pip install reportlab
```

### 3. Launch the Plugin
```bash
python plugin_gui.py
```

---

## 🎯 How to Use

1. Click **Browse** and select your `.resolved` file
2. Optionally choose an output folder (default: same folder as the input file)
3. Click **⚡ Convert to PDF**
4. The PDF opens automatically when done

---

## 💰 Free vs Premium

| Feature | Free | Premium |
|---|---|---|
| Conversions per day | 3 | Unlimited |
| PDF export | ✅ | ✅ |
| Priority support | ❌ | ✅ |

**Free plan:** 3 conversions per day, tracked locally.  
**Premium:** Enter your license key in the **Upgrade** dialog.

---

## 🛠️ Command Line (Advanced)

You can also run conversions without the GUI:

```bash
# Convert to PDF in the same directory
python convert_resolved.py myfile.resolved

# Convert with custom output path
python convert_resolved.py myfile.resolved C:\Users\You\Documents\output.pdf
```

---

## 📁 Files

| File | Purpose |
|---|---|
| `plugin_gui.py` | Main GUI application — run this |
| `convert_resolved.py` | Core converter engine |
| `usage_tracker.py` | Free/premium usage tracking |
| `requirements.txt` | Python dependencies |

---

## 🔑 Premium Activation

1. Click **⭐ Upgrade to Premium** in the top right of the app
2. Enter your license key
3. Click **Activate License**

---

*Built with Python · ReportLab · Tkinter*
