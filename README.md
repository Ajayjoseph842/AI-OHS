AI-Powered Workplace Incident Analyzer

A real-time, end-to-end system that automates the intake, analysis, and visualization of workplace incident reports using AI and Power BI.

📌 Overview

This project is a personal prototype that leverages large language models (LLMs) to analyze occupational health and safety (OHS) incident reports in real time. It turns raw safety submissions into summarized narratives and hazard categories — visualized through interactive dashboards.

Built to explore AI's potential in proactive safety compliance.

🛠️ Tools & Tech Stack

Component

Tool/Service

Form Collection

Microsoft Forms

Data Sync

Google Sheets

AI Summarization

OpenRouter + Python (Colab)

Visualization

Power BI Desktop

Storage

CSV / OneDrive (optional)

🔄 Workflow Pipeline



✨ Features

Real-time form intake of workplace incidents

LLM-based summarization of report narratives

Automatic hazard tagging using AI prompts

Power BI dashboard with slicers, filters, and visual breakdowns

📥 How to Run

1. Fill the Microsoft Form

Submit incidents through your form.

2. Open the Google Colab notebook

Run the script to fetch form responses

AI summarizes the incidents and tags hazards

Output is saved as enhanced_incidents.csv

3. Import CSV into Power BI

Open Power BI Desktop

Load enhanced_incidents.csv

Build visuals using fields like AI Summary, Hazard Tags, and Date

📊 Dashboard Highlights

Bar chart of hazard frequency

Time-series of incidents over weeks/months

AI summaries in an interactive table

Filters by date, location, and hazard type

🔍 Sample Use Case

A worker reports an incident involving chemical fumes.

🧠 AI summarizes it as a "chemical exposure due to lack of PPE"

🏷️ Tags it under "Chemical Hazard", "PPE"

📊 Appears in Power BI under relevant hazard filters

📚 Learning Goals

Explore LLM applications in real-world workflows

Combine automation, AI, and visualization in one pipeline

Build a practical portfolio project in the OHS domain

🚀 Future Improvements

Deploy as a web dashboard (Streamlit or Gradio)

Add severity scoring

Schedule automated runs (via Colab Pro or GCP)

Trigger Slack/Email alerts for high-risk incidents

🙋‍♂️ Author

Ajay JosephInternational student, OHS + Forensic Science backgroundCurious about using AI to solve meaningful problems

📬 Contact

DM on LinkedIn if you're curious, hiring, or want to collaborate!
