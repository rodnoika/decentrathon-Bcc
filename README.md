# 📄 Document OCR & Extraction System

An end-to-end system for **OCR (Optical Character Recognition)**, **post-processing**, and **structured data extraction**.  
It provides a clean **web-based interface** for uploading documents, runs **PaddleOCR** for recognition, and optionally applies **Google Gemini AI** for post-processing and structured data extraction.

---

## 🚀 Features

- **Web UI (Gradio)** – simple interface for uploading PDFs/images, selecting options, and downloading results.  
- **OCR with PaddleOCR** – supports unwarping, orientation classification, and custom recognition models.  
- **AI-Powered Post-Processing** – optional integration with Google Gemini AI for text cleaning, formatting, and data extraction.  
- **Structured Output** – exports merged text, DOCX, Markdown, and JSON with extracted metadata.  
- **Flexible Runtime** – works with CPU or GPU, customizable via environment variables.  

---

## 🏗️ System Architecture

### 1. **User Interface (Gradio / `app.py`)**
- Web-based UI for uploading files (PDFs/images).
- Lets users configure processing options:
  - Output folder  
  - Language  
  - Document unwarping  
  - Orientation correction  
  - GPU/CPU toggle  
- Displays logs, OCR results, and output download links.

### 2. **OCR Processing (`ocr.py`)**
- Core function: `run_ocr` orchestrates OCR workflow.  
- Runs **PaddleOCR CLI** with chosen options.  
- Combines results into:
  - Single merged `.txt` file  
  - `.docx` file with structured text  
- Optionally forwards results to post-processing.

### 3. **Post-Processing & Extraction (`gemini_post.py`)**
- Uses **Google Gemini AI** to:  
  - Clean OCR text  
  - Restore formatting  
  - Extract structured fields (document type, number, dates, parties, currency, etc.)  
- Validates extracted data for consistency.  
- Returns **cleaned Markdown** + **structured JSON**.

### 4. **Model Assets (`eslav_PP-OCRv5_mobile_rec`)**
- Contains PaddleOCR model weights and configs.  
- Easily replaceable for custom recognition models.  

### 5. **Configuration & Environment**
- Controlled via **environment variables**:
  - Model paths  
  - Gemini API keys  
  - Feature toggles  
- Dependencies listed in `requirements.txt`.

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/your-repo.git
cd your-repo

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # (Linux/macOS)
venv\Scripts\activate      # (Windows)

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Set environment variables in `.env`:

```ini
# PaddleOCR model path
MODEL_DIR=./eslav_PP-OCRv5_mobile_rec

# Enable Gemini post-processing (optional)
USE_GEMINI=true
GEMINI_API_KEY=your_api_key_here

# GPU support (optional)
USE_GPU=false
```

---

## ▶️ Usage

### Start the Web App
```bash
python app.py
```
The Gradio UI will open in your browser.  

### Workflow
1. Upload PDF or image files.  
2. Select processing options.  
3. Run OCR → view logs.  
4. Download results:
   - `.txt` – merged OCR text  
   - `.docx` – structured text file  
   - `.md` – cleaned Markdown (if Gemini enabled)  
   - `.json` – structured data (if Gemini enabled)  

---

## 📂 Output Examples

- **Raw OCR Text (`output.txt`)**  
- **Formatted DOCX (`output.docx`)**  
- **Cleaned Markdown (`output.md`)**  
- **Structured JSON (`output.json`)**  

---

## 🔧 Extensibility

- Swap PaddleOCR models by replacing files in `eslav_PP-OCRv5_mobile_rec`.  
- Enable/disable AI-powered post-processing with `USE_GEMINI`.  
- Runs on **CPU or GPU**, controlled via environment settings.  

---

## 🤝 Contributing

Pull requests and feature requests are welcome!  
Please open an issue for discussion before submitting major changes.  

---

## 📜 License

[MIT](LICENSE) © 2025 Your Name  
