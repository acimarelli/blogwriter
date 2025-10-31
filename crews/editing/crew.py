import os
from pathlib import Path
from crews.editing.flow import EditingFlow
from utils.config_loader import build_agents_from_yaml, build_tasks_from_yaml

config_dir = Path(__file__).parent


class EditingCrew:
    def __init__(self,
                 agent_yaml_path: str = os.path.join(config_dir, "agents.yaml"),
                 task_yaml_path: str = os.path.join(config_dir, "tasks.yaml")):
        self.agents = build_agents_from_yaml(agent_yaml_path)
        self.tasks = build_tasks_from_yaml(task_yaml_path, self.agents)
        self.flow = None

    async def kickoff(self, title: str, abstract: str, structure: list[str],
                      paragraphs: dict[str, str],
                      code_snippets: dict[str, str]):
        self.flow = EditingFlow(
            agents=self.agents,
            tasks=self.tasks,
            title=title,
            abstract=abstract,
            structure=structure,
            paragraphs=paragraphs,
            code_snippets=code_snippets
        )
        return await self.flow.run_async()