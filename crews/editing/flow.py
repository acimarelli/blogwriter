from __future__ import annotations

from logging.handlers import RotatingFileHandler
from typing import Any

from crewai.flow import Flow, listen, start

from schema.state import ArticleState
from utils.config_loader import build_crew
from utils.logger import get_logger, summarize_log_metrics

logger = get_logger("EditingFlow")


class EditingFlow(Flow[ArticleState]):
    """Gestisce la collaborazione tra agenti per l'editing dell'articolo."""

    def __init__(
        self,
        agents: dict[str, Any],
        tasks: dict[str, Any],
        title: str,
        abstract: str,
        paragraphs: dict[str, str],
        code_snippets: dict[str, str],
        structure: list[str],
    ) -> None:
        """Inizializza il flow con lo stato dell'articolo da revisionare."""
        super().__init__(
            title=title,
            abstract=abstract,
            paragraphs=paragraphs,
            code_snippets=code_snippets,
            structure=structure,
        )
        self.agents = agents
        self.tasks = tasks

    @start()
    def edit_article(self) -> ArticleState:
        """Attiva la crew responsabile dell'editing del contenuto generato."""
        logger.info("🛠️ Avvio della crew di editing dell'articolo...")
        editing_crew = build_crew(
            agents=self.agents,
            tasks=self.tasks,
            agent_keys=["editor"],
            task_keys=["edit_article_task"],
        )

        result = editing_crew.kickoff(
            inputs={
                "title": self.state.title,
                "abstract": self.state.abstract,
                "paragraphs": self.state.paragraphs,
                "code_snippets": self.state.code_snippets,
                "structure": self.state.structure,
            }
        )

        raw_output = self._extract_raw_output(result)
        if isinstance(raw_output, dict):
            self.state.edited_article = raw_output.get("edited_article", "")
            self.state.supervision_report = raw_output.get("supervision_report", "")
        else:
            self.state.edited_article = raw_output
        return self.state

    @listen(edit_article)
    def conclude(self) -> ArticleState:
        """Registra un riepilogo dei log alla fine del processo di editing."""
        logger.info("🏁 Flow di editing completato con successo.")
        try:
            log_file = next(
                handler.baseFilename
                for handler in logger.handlers
                if isinstance(handler, RotatingFileHandler)
            )
            summary = summarize_log_metrics(log_file)
            self.state.log_summary = summary
            logger.info(f"📊 Riepilogo log: {summary}")
        except StopIteration:
            logger.debug(
                "Nessun RotatingFileHandler configurato per il logger di editing."
            )
        except Exception as exc:  # pragma: no cover - logging fallback
            logger.warning(f"⚠️ Impossibile generare metriche log: {exc}")
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