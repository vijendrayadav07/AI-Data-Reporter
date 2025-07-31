#  AI-Data-Reporter

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
    ├── data2docs/
    │   ├── app/
    │   │   ├── main.py
    │   │   ├── eda.py
    │   │   └── file_handler.py
    │   ├── static/
    │   └── templates/
    ├── environment.yml
    ├── .gitignore
    └── README.md


---

## 🧱 Tech Stack

| Layer          | Tools Used                        |
|----------------|-----------------------------------|
| Frontend       | Streamlit, Matplotlib, Seaborn    |
| Backend        | Python, Pandas, Jinja2            |
| AI Engine      | OpenAI GPT-3.5 / GPT-4             |
| PDF Reports    | WeasyPrint, Jinja2                |
| File Support   | CSV, Excel (`.xlsx`), JSON        |
| Secrets        | Streamlit's `.streamlit/secrets.toml |

##  Setup Instructions

### 🔹 Clone the Repository

```bash
git clone https://github.com/vijendrayadav07/AI-Data-Reporter.git
cd AI-Data-Reporter
