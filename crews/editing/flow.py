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
            paragraphs=dict(paragraphs),
            code_snippets=dict(code_snippets),
            structure=list(structure),
        )
        self.agents = dict(agents)
        self.tasks = dict(tasks)
        self._export_log_summary = True

    @start()
    def edit_article(self) -> ArticleState:
        """Attiva la crew responsabile dell'editing del contenuto generato."""
        logger.info("🛠️ Avvio della crew di editing dell'articolo…")
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

        edited_article, supervision_report = self._parse_result(result)
        self.state.edited_article = edited_article
        self.state.supervision_report = supervision_report

        if not supervision_report and edited_article:
            generated_report = self._run_supervision(edited_article)
            if generated_report:
                self.state.supervision_report = generated_report

        return self.state

    @listen(edit_article)
    def conclude(self) -> ArticleState:
        """Registra un riepilogo dei log alla fine del processo di editing."""
        logger.info("🏁 Flow di editing completato con successo.")

        if not self._export_log_summary:
            logger.debug("Generazione del riepilogo log disattivata per questo run.")
            return self.state

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
        self._export_log_summary = export_log_summary
        final_state = await self.kickoff_async()
        self.final_state = final_state
        return final_state

    def _run_supervision(self, edited_article: str) -> str:
        """Esegue il task di supervisione se configurato e restituisce il report."""
        if "supervision_task" not in self.tasks:
            logger.debug("Task di supervisione non configurato: salto della supervisione.")
            return ""

        logger.info("🕵️ Avvio della supervisione editoriale.")
        try:
            supervision_crew = build_crew(
                agents=self.agents,
                tasks=self.tasks,
                agent_keys=["supervisor"],
                task_keys=["supervision_task"],
            )

            supervision_result = supervision_crew.kickoff(
                inputs={"edited_article": edited_article}
            )
        except Exception as exc:  # pragma: no cover - fallback in caso di errori crew
            logger.warning(f"⚠️ Impossibile completare la supervisione: {exc}")
            return ""

        raw_report = self._extract_raw_output(supervision_result)
        return str(raw_report).strip()

    @staticmethod
    def _extract_raw_output(result: Any) -> Any:
        """Estrae la rappresentazione grezza dal risultato della crew."""
        if hasattr(result, "raw"):
            return result.raw
        if hasattr(result, "__dict__") and "raw" in result.__dict__:
            return result.__dict__["raw"]
        return result

    @staticmethod
    def _parse_result(result: Any) -> tuple[str, str]:
        """Interpreta il risultato della crew restituendo testo e supervisione."""
        raw_output = EditingFlow._extract_raw_output(result)

        if isinstance(raw_output, dict):
            edited_article = str(raw_output.get("edited_article", "")).strip()
            supervision_report = str(raw_output.get("supervision_report", "")).strip()
        else:
            edited_article = str(raw_output).strip()
            supervision_report = ""

        return edited_article, supervision_report

