import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


#!/usr/bin/env python
from dotenv import load_dotenv
load_dotenv()

import sys
import warnings
from datetime import datetime
from pprint import pprint

import pandas as pd
import nbformat
from nbformat.v4 import new_notebook, new_code_cell

from content_marketing_project_manager.crew import ContentMarketingProjectManager

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Content Marketing Project Inputs
project_type = "Multi-Channel Content Marketing Campaign"
industry = "B2B SaaS"
project_objectives = "Drive brand awareness and lead generation through strategic content across blog, email, social media, and webinars."

team_members = """
- Sarah Lee (Content Strategist)
- Mark Johnson (SEO Writer)
- Priya Desai (Graphic Designer)
- Carlos Rivera (Email Marketing Specialist)
- Emma Chen (Social Media Manager)
- Liam Brown (Video Producer)
"""

project_requirements = """
- Create a blog series focused on solving key pain points for B2B SaaS decision-makers
- Develop lead magnet content (eBook and checklist) to support gated campaigns
- Write a 4-part email nurture sequence tied to the blog and lead magnet topics
- Design promotional assets for social media (LinkedIn, Twitter, Instagram)
- Produce a 2-minute explainer video introducing our new feature set
- Schedule and coordinate a live webinar with two guest speakers
- Ensure all content follows our brand guidelines and tone of voice
- Optimize blog posts and landing pages for SEO performance
- Align all content with the quarterly theme: "Scaling with Smart Systems"
- Track deadlines across all channels using a shared editorial calendar
"""

# Input dictionary for the crew
inputs = {
    'project_type': project_type,
    'industry': industry,
    'project_objectives': project_objectives,
    'project_requirements': project_requirements,
    'team_members': team_members
}


def run():
    """
    Run the content planning crew, display results, and export a notebook.
    """
    try:
        crew_instance = ContentMarketingProjectManager().crew()
        result = crew_instance.kickoff(inputs=inputs)

        # Token usage reporting
        crew_instance.calculate_usage_metrics()
        usage = crew_instance.usage_metrics

        if usage:
            cost_per_token = 0.150 / 1_000_000  # Adjust for your model
            total_tokens = usage.prompt_tokens + usage.completion_tokens
            total_cost = total_tokens * cost_per_token

            print("\n--- 📊 Usage Summary ---")
            print(f"Prompt tokens: {usage.prompt_tokens}")
            print(f"Completion tokens: {usage.completion_tokens}")
            print(f"Total tokens: {total_tokens}")
            print(f"Estimated total cost: ${total_cost:.4f}")
        else:
            print("Usage metrics not available.")

        # Extract structured output
        project_plan = result.pydantic.dict()
        tasks = project_plan.get("tasks", [])
        assignments = project_plan.get("assignments", [])
        milestones = project_plan.get("milestones", [])
        calendar = project_plan.get("content_calendar", "N/A")

        # Terminal display
        print("\n--- 📝 Content Tasks ---")
        pprint(tasks)

        print("\n--- 👥 Assignments ---")
        pprint(assignments)

        print("\n--- 🎯 Milestones ---")
        pprint(milestones)

        print("\n--- 📅 Content Calendar ---")
        print(calendar if calendar else "No calendar summary provided.")

        # Create Jupyter Notebook
        nb = new_notebook()
        nb.cells.append(new_code_cell("import pandas as pd"))

        nb.cells.append(new_code_cell(
            f"tasks = {tasks}\n"
            "df_tasks = pd.DataFrame(tasks)\n"
            "df_tasks.style.set_table_attributes('border=\"1\"').set_caption(\"Task Details\").set_table_styles(\n"
            "    [{'selector': 'th, td', 'props': [('font-size', '120%')]}]\n"
            ")"
        ))

        nb.cells.append(new_code_cell(
            f"assignments = {assignments}\n"
            "df_assignments = pd.DataFrame(assignments)\n"
            "df_assignments.style.set_table_attributes('border=\"1\"').set_caption(\"Resource Assignments\").set_table_styles(\n"
            "    [{'selector': 'th, td', 'props': [('font-size', '120%')]}]\n"
            ")"
        ))

        nb.cells.append(new_code_cell(
            f"milestones = {milestones}\n"
            "df_milestones = pd.DataFrame(milestones)\n"
            "df_milestones.style.set_table_attributes('border=\"1\"').set_caption(\"Milestones\").set_table_styles(\n"
            "    [{'selector': 'th, td', 'props': [('font-size', '120%')]}]\n"
            ")"
        ))

        nb.cells.append(new_code_cell(
            f'print("📅 Content Calendar Summary:")\nprint("""{calendar}""")'
        ))

        with open("crew_output.ipynb", "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        print("\n✅ Jupyter Notebook 'crew_output.ipynb' created successfully.")

    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs"
    }
    try:
        ContentMarketingProjectManager().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ContentMarketingProjectManager().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution with mock inputs.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    try:
        ContentMarketingProjectManager().crew().test(
            n_iterations=int(sys.argv[1]),
            openai_model_name=sys.argv[2],
            inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    run()
