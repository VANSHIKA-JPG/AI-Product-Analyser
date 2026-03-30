# 🔍 AI Product Analyser

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-green?logo=flask)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red?logo=streamlit)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-orange?logo=scikit-learn)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-2.0-purple?logo=google)

> AI-powered product analysis tool that scrapes Amazon reviews, detects fake reviews, runs sentiment analysis, and generates AI-powered summaries to help shoppers make informed decisions.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ **Smart Scraping** | Scrapes Amazon India product details & reviews with anti-detection |
| 💬 **Dual Sentiment Analysis** | VADER + TextBlob engines with aspect-based breakdown |
| 🕵️ **Fake Review Detection** | ML classifier (Random Forest + TF-IDF) identifies suspicious reviews |
| 🤖 **AI Summarization** | Google Gemini generates pros/cons, summary & buying recommendation |
| 💰 **Value Analysis** | Price-to-sentiment scoring for value-for-money insights |
| 📊 **Interactive Dashboard** | Streamlit UI with Plotly gauges, radar charts & comparison view |
| 🔐 **JWT Authentication** | Secure API with register/login and token-based auth |
| 🐳 **Docker Ready** | One-command deployment with Docker Compose |

---

## 🏗️ Architecture

```
AI-Product-Analyser/
├── app.py                     # Flask API entry point
├── config.py                  # Central configuration
├── requirements.txt           # Dependencies
├── src/
│   ├── scraper/               # Web scraping engine
│   │   ├── base_scraper.py    #   Abstract base with retry logic
│   │   └── amazon_scraper.py  #   Amazon India scraper
│   ├── analysis/              # AI/ML pipeline
│   │   ├── sentiment.py       #   VADER + TextBlob sentiment
│   │   ├── fake_review.py     #   ML fake review detector
│   │   ├── summarizer.py      #   Gemini AI summarization
│   │   └── pricing.py         #   Price/value analysis
│   ├── models/product.py      # SQLAlchemy database models
│   ├── api/
│   │   ├── routes.py          # REST API endpoints
│   │   └── auth.py            # JWT authentication
│   └── utils/helpers.py       # Shared utilities
├── frontend/
│   └── dashboard.py           # Streamlit dashboard
├── models/                    # Trained ML models (.pkl)
├── tests/                     # Test suite
├── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Google Gemini API key](https://makersuite.google.com/app/apikey) (free)

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/AI-Product-Analyser.git
cd AI-Product-Analyser

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Train the Fake Review Model (Optional)
```bash
# Download fake reviews dataset from Kaggle and place in data/
# Then train via API or notebook
python -c "from src.analysis.fake_review import FakeReviewDetector; d = FakeReviewDetector(); d.train('data/fake_reviews_dataset.csv')"
```

### 4. Run the Application
```bash
# Terminal 1: Start Flask API
python app.py

# Terminal 2: Start Streamlit Dashboard
streamlit run frontend/dashboard.py
```

### 5. Open Dashboard
Visit **http://localhost:8501** and paste any Amazon India product URL!

---

## 🐳 Docker Deployment
```bash
docker-compose up --build
```
- API: http://localhost:5000
- Dashboard: http://localhost:8501

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Analyze a product (body: `{"url": "..."}`) |
| `GET` | `/api/analysis/<id>` | Get saved analysis result |
| `GET` | `/api/history` | List all past analyses |
| `POST` | `/api/compare` | Compare products (body: `{"urls": [...]}`) |
| `POST` | `/api/auth/register` | Register user |
| `POST` | `/api/auth/login` | Login & get JWT token |
| `POST` | `/api/train-model` | Train fake review model |
| `GET` | `/api/health` | Health check |

---

## 🧠 Tech Stack

- **Backend**: Flask, SQLAlchemy, JWT
- **ML/NLP**: scikit-learn, VADER, TextBlob, TF-IDF
- **AI**: Google Gemini API (2.0 Flash)
- **Scraping**: BeautifulSoup, requests, fake-useragent
- **Frontend**: Streamlit, Plotly
- **DevOps**: Docker, pytest

---

## 👥 Team

| Member | Role | Responsibilities |
|--------|------|-------------------|
| Member 1 | Backend Lead | Flask API, DB, auth, integration |
| Member 2 | ML/NLP Engineer | Sentiment analysis, fake review model |
| Member 3 | Scraping & AI | Web scraper, Gemini summarizer |
| Member 4 | Frontend & Docs | Streamlit dashboard, documentation |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.