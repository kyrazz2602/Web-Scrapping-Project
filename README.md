# 🚀 Amazon Intelligence Dashboard


![Amazon](https://img.shields.io/badge/Amazon-FF9900?style=for-the-badge&logo=amazon&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5-AI_Powered-4285F4?style=flat-square&logo=google&logoColor=white)
![Oxylabs](https://img.shields.io/badge/Oxylabs-Data_Source-00C853?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-orange?style=flat-square)

**Unlock the secrets of Amazon's marketplace with AI-powered competitor intelligence**

[🔖 Get Started](#-get-started) • [🎯 Features](#-features) • [🛠️ Installation](#️-installation) • [📖 Usage](#-usage) • [🤝 Contributing](#-contributing)

---

## 📖 The Story

In the vast ocean of Amazon's marketplace, millions of products compete for attention. Every seller faces the same challenge: *How do I stand out?* How do I know if my pricing is competitive? What makes my rivals successful?

**Enter the Amazon Intelligence Dashboard** - your secret weapon in the e-commerce battlefield. 

Imagine having a team of expert analysts working 24/7, dissecting every competitor, analyzing market trends, and delivering actionable insights - all in seconds. That's exactly what this project delivers.

Built with cutting-edge AI technology and powered by real-time data scraping, this dashboard transforms raw product data into strategic intelligence. Whether you're a seasoned seller looking to optimize your strategy or a newcomer trying to understand the competitive landscape, this tool gives you the unfair advantage you need.

---

## 🌟 What Makes It Special

### 🎯 **Precision Intelligence**
- **Real-time scraping** from Amazon's global marketplaces
- **AI-powered analysis** using Google's Gemini models
- **Competitive insights** that drive strategic decisions

### 💎 **Beautiful Interface**
- **Modern dark theme** designed for focus
- **Responsive layout** that works everywhere
- **Intuitive navigation** with zero learning curve

### ⚡ **Lightning Fast**
- **Parallel processing** for maximum efficiency
- **Smart caching** to minimize API calls
- **Progressive loading** for instant feedback

---

## 🚀 Features

### 🔍 **Product Discovery**
- **ASIN-based lookup** - Enter any Amazon ASIN
- **Multi-marketplace support** - US, UK, DE, FR, IT, CA, AE
- **Geo-targeted results** - Localized pricing and availability

### 🤖 **AI Analysis**
- **Competitor intelligence** - Automatic competitor identification
- **Price positioning** - Understand where you stand in the market
- **Strategic recommendations** - Actionable insights from AI
- **Market positioning** - Discover your unique selling proposition

### 📊 **Data Management**
- **Local storage** - All data stored securely on your machine
- **Smart deduplication** - Clean, organized database
- **Export capabilities** - Use your data anywhere

### 🎨 **User Experience**
- **Real-time progress** - Watch the magic happen
- **Error handling** - Graceful failure recovery
- **Responsive design** - Works on desktop, tablet, and mobile

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit) | Web interface |
| **Backend** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python) | Core logic |
| **AI Engine** | ![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=flat-square&logo=google) | Analysis |
| **Scraping** | ![Oxylabs](https://img.shields.io/badge/Oxylabs-00A4E4?style=flat-square) | Data source |
| **Database** | ![TinyDB](https://img.shields.io/badge/TinyDB-FF6B6B?style=flat-square) | Storage |
| **Styling** | ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3) | UI/UX |
| **Validation** | Pydantic v2 | Typed models, guaranteed schema from LLM |
| **Package Mgmt** | uv | 10–100× faster than pip |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- An [Oxylabs](https://oxylabs.io) account
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/amazon.git
cd amazon
```

**2. Install dependencies with uv**
```bash
uv add streamlit langchain-core langchain-google-genai langchain-openai requests python-dotenv pydantic tinydb
```

**3. Set up your environment**
```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:
```env
# Oxylabs — https://oxylabs.io
OXYLABS_USERNAME=your_username
OXYLABS_PASSWORD=your_password

# Google Gemini — https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=AIza...your_key_here
```

**4. Run the app**
```bash
uv run streamlit run main.py
```

Open your browser at `http://localhost:8501` — you're live. 🎉

---


## 🎮 How to Use

### Step 1 — Scrape Your Product
Enter the ASIN of the product you want to analyze, add your zip/postal code for geo-accurate pricing, pick the marketplace, and hit **Scrape**.

```
ASIN:           B0CX23VSAS
Postal Code:    10001
Marketplace:    amazon.com
```

### Step 2 — Find Competitors
Once your product is scraped, click **🔎 Analyze Competitors** on the product card. The app will automatically search across multiple categories and sort strategies to find up to 20 real competitors.

### Step 3 — Run the AI
Click **🤖 Analyze with AI**. Gemini reads your product and every competitor, then generates:

- **Summary** — what's happening in this market right now
- **Positioning** — where your product sits relative to the field
- **Top Competitors Table** — price, rating, and key differentiators side by side
- **Recommendations** — specific, actionable moves to improve your position

---

### Architecture

```
  ┌──────────┐   structured   ┌──────────────┐   typed result   ┌──────────────┐
  │  app.py  │◀─────────────▶│  services.py │◀───────────────▶│oxylabs_client│
  │  UI only │   dataclasses  │  logic only  │  ProgressReporter│  HTTP only   │
  └──────────┘                └──────────────┘                  └──────────────┘
                                      │
                                      ▼
                               ┌──────────────┐
                               │    llm.py    │
                               │  AI only     │
                               └──────────────┘
```

> **The rule is simple:** `app.py` is the only file allowed to call `st.*`. Every other layer returns typed data. This makes the codebase testable, swappable, and sane.

---

### 📁 Project Structure

```
AmazonScrapping/
├── 📄 main.py              # Streamlit web application
├── 📄 pyproject.toml       # Project dependencies
├── 📄 .env                 # Environment variables
├── 📁 src/                 # Core application logic
│   ├── 🤖 llm.py          # AI analysis engine
│   ├── 🌐 oxylabs_client.py # Amazon scraping client
│   ├── 🔧 services.py     # Business logic layer
│   └── 💾 tinydb.py       # Database operations
├── 📄 data.json            # Local database storage
└── 📄 README.md           # This file
```

---

## 🎨 Design Philosophy

### 🌙 Dark Theme Excellence
- **Reduced eye strain** for extended analysis sessions
- **High contrast** for optimal readability
- **Professional appearance** for business presentations

### 🎯 User-Centric Design
- **Progressive disclosure** - Show only what's needed
- **Visual feedback** - Every action has a response
- **Error resilience** - Graceful handling of edge cases

### ⚡ Performance First
- **Lazy loading** - Load data only when needed
- **Smart caching** - Avoid redundant API calls
- **Parallel processing** - Maximize throughput

---

## 🔧 Configuration

### 🌍 Marketplace Support

| Marketplace | Domain | Supported |
|-------------|--------|-----------|
| 🇺🇸 United States | amazon.com | ✅ |
| 🇨🇦 Canada | amazon.ca | ✅ |
| 🇬🇧 United Kingdom | amazon.co.uk | ✅ |
| 🇩🇪 Germany | amazon.de | ✅ |
| 🇫🇷 France | amazon.fr | ✅ |
| 🇮🇹 Italy | amazon.it | ✅ |
| 🇦🇪 UAE | amazon.ae | ✅ |

## 🤖 AI Model Strategy

The app uses a **cascading fallback** across Gemini 2.5 models to maximize uptime on the free tier:

```python
MODELS = [
    "gemini-2.5-flash-lite-preview-06-17",  # Fastest · highest daily quota
    "gemini-2.5-flash",                      # Balanced · good quality
    "gemini-2.5-pro",                        # Most capable · lower quota
]
```

If a model hits a rate limit (429), the app waits with exponential backoff (`15s → 30s`) before trying the next model automatically. No babysitting required.

---

## ⚙️ Configuration Reference

| Variable | Required | Description |
|---|---|---|
| `OXYLABS_USERNAME` | ✅ | Your Oxylabs account username |
| `OXYLABS_PASSWORD` | ✅ | Your Oxylabs account password |
| `GOOGLE_API_KEY` | ✅ | Google AI Studio API key (free at [aistudio.google.com](https://aistudio.google.com/app/apikey)) |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### ⚖️ Important Notes

- **Respect Amazon's Terms of Service** when using scraped data
- **API rate limits** apply - use responsibly
- **Data privacy** - All data is stored locally
- **Commercial use** - Check API provider terms for commercial applications

---

## 🙏 Acknowledgments

- **Amazon** - For providing the marketplace data
- **Oxylabs** - For reliable scraping infrastructure
- **Google** - For the powerful Gemini AI models
- **Streamlit** - For the amazing web framework
- **Open Source Community** - For the incredible tools and libraries

---

## 📞 Support

Got questions? We're here to help!

- 📧 **Email**: arizalansyori42@gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/AmazonScrapping/issues)
- 📖 **Documentation**: [Wiki](https://github.com/yourusername/AmazonScrapping/wiki)

---


**⭐ If this project helped you, give it a star!**

Made with ❤️ by [Arizal Anshori](https://github.com/kyrazz2602)

[🔝 Back to Top](#-amazon-intelligence-dashboard)