# Customer Profiler

A modern app for generating comprehensive customer profiles from uploaded documents, featuring a visually appealing, card-based UI for Relationship Managers.

## Features
- Modern, card-based customer profile page with summary badges
- Upload and analyze key documents (Sale Deed, Credit Report, Bank Statement, ID)
- AI-driven profile generation and query functionality
- Responsive, clean design

## Installation

```bash
pip install streamlit pymupdf matplotlib docx2txt
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
pip install paddleocr==2.10.0
```

## Running the App

Activate your environment (if using a virtualenv):
```bash
. profiler_env/Scripts/activate
```

Then start the app:
```bash
streamlit run app.py
```

## Screenshots

![Modern Customer Profile Page](screenshot.png)

## About
This app provides a modern, interactive interface for Relationship Managers to view, analyze, and query customer profiles generated from uploaded documents.