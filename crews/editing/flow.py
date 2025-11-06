from __future__ import annotations

import json
from logging.handlers import RotatingFileHandler
from typing import Any
from pathlib import Path

from crewai.flow import Flow, listen, start

from schema.state import ArticleState
from utils.config_loader import build_crew
from utils.logger import get_logger, summarize_log_metrics
from utils.markdown_utils import MarkdownUtils

logger = get_logger("EditingFlow")


class EditingFlow(Flow[ArticleState]):
    """Gestisce la collaborazione tra agenti per l'editing dell'articolo."""

    def __init__(
        self,
        agents: dict[str, Any],
        tasks: dict[str, Any],
        state: ArticleState, 
        num_reviews: int = 10,
        write_output: bool = False,
        markdown_outpath: str | None = None
    ) -> ArticleState:
        """Inizializza il flow con lo stato dell'articolo da revisionare."""
        super().__init__(**state.model_dump())
        self.agents = dict(agents)
        self.tasks = dict(tasks)
        self.num_reviews = num_reviews
        self.write_output = write_output
        self.md_outpath = markdown_outpath

    @start()
    def review_article(self):
        self.state.original_article = MarkdownUtils.generate_markdown(title=self.state.title, abstract=self.state.abstract, 
                                                           structure=self.state.structure, paragraphs=self.state.paragraphs, 
                                                           code_snippets=self.state.code_snippets, write_output=False)
        
        logger.info("🕵️ Avvio della supervisione editoriale.")
        for i in range(self.num_reviews):
            supervision_crew = build_crew(
                agents=self.agents,
                tasks=self.tasks,
                agent_keys=["supervisor"],
                task_keys=["supervision_task"],
            )

            result = supervision_crew.kickoff(inputs={"original_article": self.state.original_article})
            self.state.supervision_report[f"Reviews_{i+1}"] = self._extract_raw_output(result)
            logger.info(f"Review {i+1}/{self.num_reviews} terminata.")

        return self.state
    
    @listen(review_article)
    def review_consolidator(self):
        logger.info("🕵️ Avvio consolidamento della supervisione editoriale in unica review.")
        review_consolidator_crew = build_crew(
                agents=self.agents,
                tasks=self.tasks,
                agent_keys=["review_consolidator"],
                task_keys=["consolidate_reviews_task"],
            )
        
        result = review_consolidator_crew.kickoff(inputs={
            "reviews": self.state.supervision_report
            })
        self.state.final_revision_report = self._extract_raw_output(result)
        
        return self.state
    
    @listen(review_consolidator)
    def final_article_generator(self):
        logger.info("🚀 Attivo la crew per la generazione della versione finale dell'articolo.")

        section_modifier_crew = build_crew(
                agents=self.agents,
                tasks=self.tasks,
                agent_keys=["editor_profile"],
                task_keys=["edit_article_task"],
            )
        final_review_dict = json.loads(self.state.final_revision_report)

        if final_review_dict.get("Abstract", "") != "":
            new_abstract_result = section_modifier_crew.kickoff(
                inputs={
                    "section_name": "Abstract",
                    "section_text": self.state.abstract,
                    "review_text": final_review_dict.get("Abstract", "")
                    }
                )
            self.state.abstract = self._extract_raw_output(new_abstract_result)
        for section in self.state.structure:
            if final_review_dict.get(section, "") != "":
                new_section_result = section_modifier_crew.kickoff(
                    inputs={
                        "section_name": section,
                        "section_text": self.state.paragraphs[section],
                        "review_text": final_review_dict.get(section, "")
                        }
                    )
                self.state.paragraphs[section] = self._extract_raw_output(new_section_result)
        
        return self.state
    
    @listen(final_article_generator)
    def edit_article(self) -> ArticleState:
        """Attiva l'editing del contenuto generato."""
        logger.info("🛠️ Avvio dell'editing dell'articolo…")

        self.state.edited_article = MarkdownUtils.generate_markdown(title=self.state.title, abstract=self.state.abstract, 
                                                                    structure=self.state.structure, paragraphs=self.state.paragraphs, 
                                                                    code_snippets=self.state.code_snippets, write_output=self.write_output, output_path=self.md_outpath)
        if self.write_output:
            logger.info(f"✅ File Markdown generato: {self.state.title.lower().replace(' ', '_').replace('/', '-')}.md")

        return self.state

    @listen(edit_article)
    def conclude(self) -> ArticleState:
        """Registra un riepilogo dei log alla fine del processo di editing."""
        logger.info("🏁 Flow di editing completato con successo.")
        # Analisi log
        try:
            log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
            log_file = next(
                h.baseFilename for h in logger.handlers if isinstance(h, RotatingFileHandler)
            )
            summary = summarize_log_metrics(log_file)
            self.state.log_summary = summary
            logger.info(f"📊 Riepilogo log: {summary}")
        except Exception as e:
            logger.warning(f"⚠️ Impossibile generare metriche log: {e}")
        return self.state

    async def run_async(self, export_log_summary: bool = True) -> ArticleState:
        """Avvia il flow in modalità asincrona, restituendo lo stato finale."""
        logger.info("🚀 Avvio asincrono del flow EditingFlow")
        final_state = await self.kickoff_async()
        self.final_state = final_state
        return final_state

    @staticmethod
    def _extract_raw_output(result: Any) -> Any:
        """Estrae la rappresentazione grezza dal risultato della crew."""
        if hasattr(result, "raw"):
            return result.raw
        if hasattr(result, "__dict__") and "raw" in result.__dict__:
            return result.__dict__["raw"]
        return result

