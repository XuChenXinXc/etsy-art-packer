# EtsyArtPacker ⚡

[![Live Demo](https://img.shields.io/badge/demo-online-emerald.svg?style=flat-square)](https://etsyartpacker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Client--Side-indigo.svg?style=flat-square)](https://etsyartpacker.com/)
[![Zero Upload](https://img.shields.io/badge/Privacy-100%25%20In--Browser-green.svg?style=flat-square)](https://etsyartpacker.com/)

> **EtsyArtPacker** is an open-source, client-side image processing utility engineered for Etsy digital art sellers and Print-on-Demand (POD) creators. It automatically transforms a single high-resolution artwork into the **5 standard gallery frame ratios**, injects true **300 DPI** metadata into the binary headers, and bundles everything into an **Etsy-compliant ZIP package** in seconds.

[**Explore Live Demo »**](https://etsyartpacker.com/)

---

## 🌟 Key Highlights

- **🔒 100% Client-Side & Private**: All image cropping, re-sampling, and ZIP packaging occur locally in the user's browser using HTML5 Canvas and Web Workers. Zero bytes of creative assets are ever uploaded to remote servers.
- **🎯 5 Essential Ratio Families**: Pre-configured with the exact dimensional ratios required by global wall art marketplaces (2:3, 3:4, 4:5, ISO A-Series, and 11:14).
- **🖨️ True Binary 300 DPI Injection**: Modifies the JFIF `APP0` marker directly in the JPEG byte stream to guarantee genuine 300 DPI resolution recognition across Photoshop, Windows Explorer, Printify, Gelato, and professional print labs.
- **📦 Instant ZIP Delivery**: Uses in-memory compression via `JSZip` to generate a structured, customer-ready digital download pack complete with a built-in `Printing_Size_Guide.txt`.
- **🚀 Zero Cost & Zero Setup**: Pure static frontend architecture with zero backend dependencies. Deployable instantly on Vercel, Cloudflare Pages, or GitHub Pages.

---

## 📐 Ratio & Size Matrix

EtsyArtPacker calculates and exports each ratio based on maximum standard wall frame specifications:

| Ratio Family | Target Max Resolution (@300 DPI) | Compatible Frame & Print Sizes | Common Display Use Case |
| :--- | :--- | :--- | :--- |
| **2:3 Ratio** | **7200 × 4800 px** (or 4800 × 7200) | `4x6"`, `8x12"`, `12x18"`, `16x24"`, `20x30"`, `24x36"` | Large exhibition posters, gallery hallways |
| **3:4 Ratio** | **7200 × 5400 px** (or 5400 × 7200) | `6x8"`, `9x12"`, `12x16"`, `15x20"`, `18x24"` | Standard photography & gallery frames |
| **4:5 Ratio** | **6000 × 4800 px** (or 4800 × 6000) | `4x5"`, `8x10"`, `12x15"`, `16x20"` | Home decor, classic photo frames, IKEA frames |
| **ISO A-Series**| **7016 × 4960 px** (or 4960 × 7016) | `A1`, `A2`, `A3`, `A4`, `A5` | International standard (UK, Europe, Australia) |
| **11:14 Ratio** | **4200 �� 3300 px** (or 3300 × 4200) | `11x14"` | Popular North American standalone portrait frame |

*Note: The exporter automatically detects whether the input artwork is portrait or landscape and applies corresponding dimension boundaries.*

---

## 🏗️ Technical Architecture & Pipeline

```
[Master Artwork (JPG/PNG/WEBP)]
              │
              ▼
   [HTML5 Canvas Viewport]
              │
      ┌───────┴──────────────────────────────┐
      │  • Aspect Ratio Calculation          │
      │  • Smart Center Cropping             │
      │  • High-Quality Bilinear Smoothing   │
      └───────┬──────────────────────────────┘
              │
              ▼
      [Raw JPEG Byte Stream]
              │
              ▼
   [Binary JFIF Header Modifier] ──► (Sets APP0 Marker: Xdensity=300, Ydensity=300, Units=DPI)
              │
              ▼
    [In-Memory JSZip Packaging]  ──► (5 High-Res JPGs + 1 Customer Printing Guide)
              │
              ▼
[Instant Local Browser Download (.ZIP)]
```

---

## 🚀 Quick Start & Local Development

This project has zero build-step requirements. You can run it locally with any lightweight static file server:

### Prerequisites
- Any modern web browser (Chrome, Edge, Firefox, Safari)
- Optional: Python 3 or Node.js for local static serving

### Running Locally

```bash
# 1. Clone repository
git clone https://github.com/XuChenXinXc/etsy-art-packer.git
cd etsy-art-packer

# 2. Start a local server (Option A: Python)
python -m http.server 3000

# Or (Option B: Node.js)
npx serve .

# 3. Open your browser
# Navigate to: http://localhost:3000
```

---

## 🌐 Production Deployment

Deploy to modern serverless edge platforms with a single click or Git push:

### Vercel
1. Import this repository into [Vercel](https://vercel.com).
2. Framework Preset: **Other**.
3. Build & Output Settings: Leave default.
4. Click **Deploy**.

### Cloudflare Pages
1. Connect repository in Cloudflare Dashboard under **Workers & Pages**.
2. Build command: None (Static HTML).
3. Output directory: `/`.
4. Click **Deploy Site**.

---

## 📄 License & Ownership

Distributed under the **MIT License**. Copyright (c) 2026 **[XuChenXinXc](https://github.com/XuChenXinXc)**. See [`LICENSE`](LICENSE) for details.

---

## 🤝 Contributing

Contributions, feature suggestions, and pull requests are warmly welcomed!  
If you find this tool helpful for your digital product store, please consider giving this repository a ⭐️!

Contributions, feature suggestions, and pull requests are warmly welcomed!  
If you find this tool helpful for your digital product store, please consider giving this repository a ⭐️!
