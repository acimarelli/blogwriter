# crew.py
import os
from crews.input_validator.flow import InputValidatorFlow
from schema.state import ArticleState
from utils.config_loader import build_agents_from_yaml, build_tasks_from_yaml
from pathlib import Path

# Load agent and task registry from YAML
config_dir = Path(__file__).parent


class InputValidatorCrew:
    def __init__(self, 
                 agent_yaml_path: str = os.path.join(config_dir, "agents.yaml"), 
                 task_yaml_path: str = os.path.join(config_dir, "tasks.yaml"),
                 agent_registry: dict | None = None
                 ) -> ArticleState:
        """Classe di orchestrazione per il flusso di validazione degli input iniziali.

        Parameters
        ----------
        agent_yaml_path:
            Percorso del file YAML contenente la definizione degli agenti.
        task_yaml_path:
            Percorso del file YAML contenente la definizione dei task.
        agent_registry:
            Registro opzionale per risolvere gli identificativi degli LLM. Se
            non fornito viene utilizzato il registro di default.
        """
        self.agents = build_agents_from_yaml(agent_yaml_path, agent_registry=agent_registry)
        self.tasks = build_tasks_from_yaml(task_yaml_path, self.agents)
        self.flow = None
    
    async def kickoff(self, title: str = "", abstract: str = "", structure: list[str] = []):
        self.flow = InputValidatorFlow(
            agents=self.agents,
            tasks=self.tasks,
            title=title,
            abstract=abstract,
            structure=structure
        )
        return await self.flow.run_async()

