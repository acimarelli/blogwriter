# crew.py
import os
from crews.writing.flow import WritingArticleFlow
from utils.config_loader import build_agents_from_yaml, build_tasks_from_yaml
from pathlib import Path

# Load agent and task registry from YAML
config_dir = Path(__file__).parent


class WritingCrew:
    def __init__(self, 
                 agent_yaml_path: str = os.path.join(config_dir, "agents.yaml"), 
                 task_yaml_path: str = os.path.join(config_dir, "tasks.yaml")
                 ):
        """Classe di orchestrazione per il flusso di validazione degli input iniziali."""
        self.agents = build_agents_from_yaml(agent_yaml_path)
        self.tasks = build_tasks_from_yaml(task_yaml_path, self.agents)
        self.flow = None
    
    async def kickoff(self, title: str, abstract: str, structure: list[str]):
        self.flow = WritingArticleFlow(
            agents=self.agents,
            tasks=self.tasks,
            title=title,
            abstract=abstract,
            structure=structure
        )
        return await self.flow.run_async()