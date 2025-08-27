# 🧠 Project Manager - CrewAI

Project planning application based on **CrewAI** with intelligent agents that help organize multichannel content marketing campaigns.  
The **frontend is built with Streamlit**, providing an easy-to-use web interface for project interaction and execution.

---

## 📌 Executive Summary
This application uses a **crew of 3 AI agents** that validate inputs with **Pydantic** and generate an **actionable plan**:
- Team organization  
- Assignment of responsibilities  
- Task sequencing  
- Estimation of time and costs  

Although the use case is oriented towards **content marketing (blog, email, social media)**, the approach is **generalizable** to any type of project.

---

## 🚀 Problem It Solves
A Project Manager usually spends hours on:
- Organizing people and resources  
- Sequencing tasks  
- Monitoring objectives  

This app **systematizes the process**, reducing preparation time and improving the quality of the initial plan.

---

## ⚙️ Project Structure

```
content_marketing_project_manager/
│── config/     # Crew and task configuration
│── tools/      # Custom tools
│── main.py     # Main script
│── crew.py     # Crew definition
│── types.py    # Pydantic type definitions
│── README.md   # Project documentation
```

---

## 🔧 Requirements
- Python 3.10+  
- [CrewAI](https://pypi.org/project/crewai/)  
- Pydantic  
- Streamlit  
- OpenAI API key (or another LLM provider)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## ▶️ Execution

Create and configure a `.env` file in the root with your API key:

```
OPENAI_API_KEY=your_api_key_here
```

Run the app:

```bash
python main.py
```

Enter objectives, team, and deliverables. The system outputs a plan in a Notebook with assignment of responsibilities, timing, and token/cost estimation.

---

## 🎨 Frontend

This project uses **Streamlit** as the frontend framework to provide an interactive and user-friendly interface where users can:
- Upload inputs and objectives  
- Run the CrewAI workflow  
- Visualize the generated project plan and task distribution  

---

## 📊 Example Usage

**Input:**
```json
{
  "objective": "Launch a digital marketing campaign",
  "team": ["PM", "Copywriter", "Designer", "SEO Analyst"],
  "deliverables": ["Blog posts", "Emailing", "Social Ads"]
}
```

**Output:**
- Work plan in Notebook  
- Token and cost estimation  
- Task distribution by responsible  

---

## 👨‍💻 Author
Francisco Moyano Escalera  
Specialist in Data, AI and Automation  
📧 frannmmm419@gmail.com  
🌐 GitHub  

