 Pl#  AI-Data-Reporter

**AI-Data-Reporter** is a Streamlit web app that allows users to upload structured data files (CSV or Excel) and automatically generates insightful visual and textual reports using Python-based analysis and AI techniques.

---

##  Features

- 📂 Upload `.csv` or `.xlsx` files
- 📊 Automatic exploratory data analysis (EDA)
- 📈 Interactive visualizations (histograms, boxplots, correlations)
- 🧠 AI-generated summaries (via LLMs)
- 🧼 Clean and responsive Streamlit interface

---

## 📁 Project Structure

    AI-Data-Reporter/
    ├──Data2docs/
    |   └──app/
    │      ├── main.py # FastAPI backend (optional for APIs)
    │      ├── services/ # EDA, ML, forecasting logic
    │      ├── llm/ # LLM integration
    │      └── utils/ # Helpers
    ├── streamlit_app/
    │ └── app.py # Streamlit UI
    ├── models/ # Trained model files
    ├── data/ # Sample CSV files
    ├── notebooks/ # Experiments & testing
    ├── requirements.txt
    ├── .venv
    └── README.md    


---

## 🚀 Tech Stack

### **1** ML, EDA & Forecasting
- **Python 3.10+**
- `Pandas`, `NumPy`, `Scikit-learn`, `XGBoost`, `LightGBM`, `CatBoost`
- `PyCaret` – AutoML
- `Prophet`, `ARIMA`, `Statsmodels`
- `Sweetviz`, `Pandas-Profiling`, `Plotly`, `Matplotlib`

### **2** LLM CSV Chat
- `LangChain`, `PandasAI`, `LlamaIndex`
-  `Groq + LLaMA3`

### **3** Frontend
- ✅ `Streamlit` – interactive Python web UI
- `Plotly`, `Seaborn` – for charts in Streamlit

### **4** Backend
- `FastAPI` – high-performance async backend (if needed)
- `Uvicorn` – ASGI server
- Optional: `SQLite/PostgreSQL`, `Celery + Redis`


##  Setup Instructions

### 🔹 Clone the Repository

```bash
git clone https://github.com/vijendrayadav07/AI-Data-Reporter.git
cd AI-Data-Reporter
