import ast
from typing import Optional
import json
import ast
import re
from typing import List

from crewai.flow import Flow, start, router, listen, or_
from schema.state import ArticleState
from utils.logger import get_logger, summarize_log_metrics
from utils.config_loader import build_agents_from_yaml, build_tasks_from_yaml, build_crew

logger = get_logger("InputValidatorFlow")


class InputValidatorFlow(Flow[ArticleState]):
    def __init__(
        self,
        agents: dict,
        tasks: dict,
        title: Optional[str] = None,
        abstract: Optional[str] = None,
        structure: Optional[list[str]] = None,
        ):
        super().__init__(title=title, abstract=abstract, structure=structure)
        self.agents = agents
        self.tasks = tasks
    
    @start()
    def verify_title(self):
        logger.info("🔁 Inizio del flow di validazione input")
        if not self.state.title.strip():
            self.state.title = input("📝 Inserisci il titolo dell'articolo: ")
        return self.state.title

    @router(verify_title)
    def decide_abstract_presence(self, abstract):
        if abstract and abstract.strip():
            logger.info("✅ Abstract già fornito. Procedo a migliorarlo.")
            return "abstract_presente"
        logger.info("🧠 Abstract mancante. Sarà generato automaticamente.")
        return "generate_abstract"

    @listen("generate_abstract")
    def abstract_creator(self):
        logger.info("🚀 Attivo la crew per generare l’abstract...")
        crew = build_crew(
            agents=self.agents,
            tasks=self.tasks,
            agent_keys=["abstract_writer"],
            task_keys=["generate_abstract_task"]
            )
        output = crew.kickoff(
            inputs={"title": self.state.title}
            )

        self.state.abstract = output
        logger.info(f"[OUTPUT abstract] {self.state.abstract}")
        return self.state.abstract
    
    @listen("abstract_presente")
    def abstract_modifier(self):
        logger.info("🚀 Attivo la crew per migliorare l’abstract esistente...")
        crew = build_crew(
            agents=self.agents,
            tasks=self.tasks,
            agent_keys=["abstract_writer"],
            task_keys=["modify_abstract_task"]
            )
        output = crew.kickoff(
            inputs={"title": self.state.title, 
                    "abstract": self.state.abstract}
            )
        self.state.abstract = output.__dict__['raw']
        logger.info(f"[OUTPUT abstract] {self.state.abstract}")
        return self.state.abstract

    @listen(or_(abstract_creator, abstract_modifier))
    def migliora_struttura(self):
        logger.info("🎯 Attivazione Crew per miglioramento struttura")
        crew = build_crew(
            agents=self.agents,
            tasks=self.tasks,
            agent_keys=["project_manager"],
            task_keys=["structure_analysis_task"]
        )
        result = crew.kickoff(inputs={
            "title": self.state.title,
            "abstract": self.state.abstract,
            "structure": self.state.structure
        })
        logger.info(f"✅ Crew completata, output : {result.__dict__['raw']}")
        self.state.structure = InputValidatorFlow.safe_literal_list_parse(result.__dict__['raw'])
        return self.state.structure

    @listen(migliora_struttura)
    def conclude(self):
        logger.info("🏁 Flow terminato con successo.")
        logger.info(f"Titolo: {self.state.title}")
        logger.info(f"Abstract: {self.state.abstract}")
        logger.info(f"Struttura finale: {self.state.structure}")

        # Analisi log
        try:
            summary = summarize_log_metrics(f"logs/{logger.name}.log")
            self.state.log_summary = summary
            logger.info(f"📊 Riepilogo log: {summary}")
        except Exception as e:
            logger.warning(f"⚠️ Impossibile generare metriche log: {e}")

        return self.state
    
    @staticmethod
    def safe_literal_list_parse(output: str) -> List[str]:
        """
        Estrae e parse in sicurezza una lista Python da un blocco di testo.
        Ritorna una lista di stringhe, o una lista vuota in caso di errore.
        """
        try:
            parsed = ast.literal_eval(output)
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                return parsed
            else:
                return []
        except (SyntaxError, ValueError):
            return []

    async def run_async(self, export_log_summary: bool = True) -> ArticleState:
        logger.info("🚀 Avvio asincrono del flow InputValidatorFlow")
        final_state = await self.kickoff_async()
        self.final_state = final_state
        return final_state
