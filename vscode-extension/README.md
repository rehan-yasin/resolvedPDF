<div align="center">
  <img src="https://raw.githubusercontent.com/rehan-yasin/resolvedPDF/main/vscode-extension/icon.png" width="128" />
  <h1>ResolvedPDF</h1>
  <p><b>Convert .resolved Markdown files to beautifully styled PDFs with a right-click.</b></p>
</div>

## ✨ Features

- **Instant PDF Generation:** Converts custom `.resolved` files into beautifully formatted PDF documents instantly.
- **Offline & Secure:** All conversions happen locally on your machine. No data is sent to the cloud.
- **Zero Configuration:** Automatically styles tables, code blocks, bold/italic text, and headings with a professional, light-themed aesthetic.
- **Seamless Integration:** Right-click any `.resolved` file in your editor or file explorer to generate the PDF alongside the original file.

## 🚀 Installation & Usage

### 1. Prerequisites
You must have [Node.js](https://nodejs.org/) installed on your machine for the extension to execute the built-in python converter smoothly.

### 2. How to use
1. Create or open any file ending with `.resolved` (e.g., `document.md.resolved`).
2. **Right-click** anywhere inside the editor or right-click the file in the sidebar.
3. Select **"Convert to PDF"**.
4. The generated PDF will instantly appear in the same directory!

### ⚠️ Known Limitations
- **External Files Context Menu:** If you open a `.resolved` file that is *outside* your currently open folder/workspace, VS Code occasionally restricts the right-click menu from appearing immediately. 
  - **Workaround:** Simply click to another open tab and click back to the `.resolved` file (or close and re-open the file). This refreshes the VS Code context menu and the "Convert to PDF" button will appear.

## 🤝 Support & Web App

You can also use the drag-and-drop web version for quick conversions on the go:
👉 [resolved2pdf.com](https://resolved2pdf.com)

**Created by Vibecoder**
