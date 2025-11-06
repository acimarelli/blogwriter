import os
from pathlib import Path
from crews.editing.flow import EditingFlow
from schema.state import ArticleState
from utils.config_loader import build_agents_from_yaml, build_tasks_from_yaml

config_dir = Path(__file__).parent


class EditingCrew:
    def __init__(self, 
                 state: ArticleState,
                 agent_yaml_path: str = os.path.join(config_dir, "agents.yaml"),
                 task_yaml_path: str = os.path.join(config_dir, "tasks.yaml")
                 ) -> ArticleState:
        self.agents = build_agents_from_yaml(agent_yaml_path)
        self.tasks = build_tasks_from_yaml(task_yaml_path, self.agents)
        self.state = state
        self.flow = None

    async def kickoff(self, 
                      num_reviews: int = 10,
                      write_output: bool = False,
                      markdown_outpath: str | None = None
                      ):
        self.flow = EditingFlow(
            agents=self.agents,
            tasks=self.tasks,
            state=self.state,
            num_reviews=num_reviews,
            write_output=write_output,
            markdown_outpath=markdown_outpath
        )
        return await self.flow.run_async()