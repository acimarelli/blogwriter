import os
import sys
import yaml
import importlib
import inspect
from typing import Dict
from crewai import Agent, Task, Crew, Process
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from llm.ollama_llm_tool import OllamaLLMTool

DEFAULT_AGENT_REGISTRY = {
    "local_chatollama": OllamaLLMTool(model='ollama/gpt-oss:20b',
                                      temperature=0.7,
                                      top_p=0.9,
                                      top_k=60,
                                      repeat_penalty=1.1,
                                      num_ctx=4096),
    "code_llm": OllamaLLMTool(model='ollama/deepseek-coder:33b',
                              temperature=0.2,
                              top_p=0.8,
                              top_k=50,
                              repeat_penalty=1.1,
                              num_ctx=4096),
    "code_comment_llm": OllamaLLMTool(model='ollama/gemma3:27b',
                                      temperature=0.4,
                                      top_p=0.9,
                                      top_k=50,
                                      repeat_penalty=1.1,
                                      num_ctx=4096)
}

def load_yaml(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def camel_to_snake(name):
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def load_tools(agents_yaml_path: str):
    agents = load_yaml(agents_yaml_path)
    tool_names = {tool for ag in agents.values() for tool in ag.get("tools", [])}
    tools_registry = {}

    for tool in tool_names:
        try:
            module_path = f"blogwriter.tools.{camel_to_snake(tool)}"
            module = importlib.import_module(module_path)
            cls = getattr(module, tool)
            if inspect.isclass(cls):
                tools_registry[tool] = cls()
        except Exception as e:
            print(f"Errore caricando il tool {tool}: {e}")
    return tools_registry

def build_agents_from_yaml(agents_path: str, tools_registry: dict = None, agent_registry: dict = None) -> Dict[str, Agent]:
    """Build agents from a YAML configuration.

    Parameters
    ----------
    agents_path: str
        Path to the YAML file defining the agents.
    tools_registry: dict, optional
        Mapping of tool names to tool instances available to the agents.
    agent_registry: dict, optional
        Mapping of LLM identifiers to LLM tool instances. If ``None`` the
        :data:`DEFAULT_AGENT_REGISTRY` is used.

    Returns
    -------
    Dict[str, Agent]
        Dictionary of instantiated agents keyed by their identifiers.
    """
    raw_agents = load_yaml(agents_path)
    agents = {}
    tools_registry = tools_registry or {}
    agent_registry = agent_registry or DEFAULT_AGENT_REGISTRY

    for key, data in raw_agents.items():
        tools = [tools_registry[t] for t in data.get("tools", []) if t in tools_registry]
        llm = agent_registry.get(data.get("llm", "local_chatollama"))
        llm_obj = getattr(llm, "llm", llm)

        agents[key] = Agent(
            role=data["role"],
            goal=data["goal"],
            backstory=data["backstory"],
            tools=tools,
            cache=data.get("cache", True),
            verbose=data.get("verbose", False),
            multimodal=data.get("multimodal", False),
            reasoning=data.get("reasoning", False),
            knowledge_sources=data.get("knowledge_sources", []),
            allow_delegation=data.get("allow_delegation", False),
            allow_code_execution=data.get("allow_code_execution", False),
            llm=llm_obj
        )
    return agents

def build_tasks_from_yaml(tasks_path: str, agents: Dict[str, Agent]) -> Dict[str, Task]:
    raw_tasks = load_yaml(tasks_path)
    tasks = {}
    for key, data in raw_tasks.items():
        agent = agents[data["agent"]]
        tasks[key] = Task(
            description=data["description"],
            expected_output=data["expected_output"],
            agent=agent,
            output_file=data.get("output_file", None),
            human_input=data.get("human_input", False),
            markdown=data.get("markdown", False)
        )
    return tasks

def build_crew(agents: dict, tasks: dict, agent_keys: list[str], task_keys: list[str], *, verbose=False, process="sequential") -> Crew:
    """
    Costruisce una Crew dinamicamente estraendo da dizionari preesistenti gli agenti e i task
    associati alle chiavi specificate.

    :param agents: Dizionario completo di agenti (tipicamente prodotto da build_agents_from_yaml)
    :param tasks: Dizionario completo di task (tipicamente prodotto da build_tasks_from_yaml)
    :param agent_keys: Lista di chiavi da estrarre da agents
    :param task_keys: Lista di chiavi da estrarre da tasks
    :param verbose: Flag per attivare i log della Crew
    :param process: Modalità di orchestrazione ('sequential', 'hierarchical', ...)
    :return: Oggetto Crew pronto all’uso
    """
    selected_agents = [agents[key] for key in agent_keys if key in agents]
    selected_tasks = [tasks[key] for key in task_keys if key in tasks]

    if not selected_agents:
        raise ValueError("Nessun agente trovato con le chiavi specificate.")
    if not selected_tasks:
        raise ValueError("Nessun task trovato con le chiavi specificate.")

    return Crew(
        agents=selected_agents,
        tasks=selected_tasks,
        verbose=verbose,
        process=process,
        
    )

def load_agent_and_task_from_yaml(agent_id: str, task_id: str, agents_path: str, tasks_path: str, agent_registry: dict = None):
    """Load a single agent and task from YAML files.

    Parameters
    ----------
    agent_id: str
        Identifier of the agent to load.
    task_id: str
        Identifier of the task to load.
    agents_path: str
        Path to the YAML file defining agents.
    tasks_path: str
        Path to the YAML file defining tasks.
    agent_registry: dict, optional
        Custom mapping of LLM identifiers to LLM tool instances. If ``None`` the
        :data:`DEFAULT_AGENT_REGISTRY` is used.

    Returns
    -------
    tuple[Agent, Task]
        The instantiated agent and task corresponding to the provided identifiers.
    """
    tools = load_tools(agents_path)
    agents = build_agents_from_yaml(agents_path, tools, agent_registry)
    tasks = build_tasks_from_yaml(tasks_path, agents)
    return agents[agent_id], tasks[task_id]
