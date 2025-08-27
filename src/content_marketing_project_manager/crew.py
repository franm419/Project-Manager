from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from content_marketing_project_manager.types import ProjectPlan

@CrewBase
class ContentMarketingProjectManager():
    """ContentMarketingProjectManager: Content Campaign Planning Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def project_planning_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['project_planning_agent'],
            verbose=True
        )

    @agent
    def estimation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['estimation_agent'],
            verbose=True
        )

    @agent
    def resource_allocation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['resource_allocation_agent'],
            verbose=True
        )

    @task
    def task_breakdown(self) -> Task:
        return Task(
            config=self.tasks_config['task_breakdown'],
            agent=self.project_planning_agent()
        )

    @task
    def time_resource_estimation(self) -> Task:
        return Task(
            config=self.tasks_config['time_resource_estimation'],
            agent=self.estimation_agent()
        )

    @task
    def resource_allocation(self) -> Task:
        return Task(
            config=self.tasks_config['resource_allocation'],
            agent=self.resource_allocation_agent(),
            output_pydantic=ProjectPlan  # Ensure the final task produces a fully structured plan
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ContentMarketingProjectManager for content project planning"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Sequential execution: breakdown → estimate → allocate
            verbose=True
        )
