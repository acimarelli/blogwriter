import asyncio
import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from crews.input_validator.crew import InputValidatorCrew
from crews.writing.crew import WritingCrew
from crews.editing.crew import EditingCrew
from llm.ollama_llm_tool import OllamaLLMTool


# ---------- Config & Helpers ----------

@dataclass(frozen=True)
class OrchestratorConfig:
    title: str
    abstract: str = ""
    structure: List[str] = None
    agent_registry: Optional[Dict] = None
    num_reviews: int = 10
    write_output: bool = False
    markdown_outpath: Optional[Path] = None
    plot_flows: bool = True
    flow_dir: Path = Path(__file__).resolve().parent / "flow_chart"


def _slugify(text: str, max_len: int = 80) -> str:
    slug = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-").lower()
    return slug[:max_len] if max_len else slug


def build_default_agent_registry() -> Dict[str, OllamaLLMTool]:
    """
    Registry minimale con modelli locali Ollama. Personalizza a piacere.
    """
    return {
        "local_chatollama": OllamaLLMTool(
            model="ollama/gpt-oss:20b",
            temperature=0.7,
            top_p=0.9,
            top_k=60,
            repeat_penalty=1.1,
            num_ctx=4096,
        ),
        "code_llm": OllamaLLMTool(
            model="ollama/deepseek-coder:33b",
            temperature=0.2,
            top_p=0.8,
            top_k=50,
            repeat_penalty=1.1,
            num_ctx=4096,
        ),
        "code_comment_llm": OllamaLLMTool(
            model="ollama/gemma3:27b",
            temperature=0.4,
            top_p=0.9,
            top_k=50,
            repeat_penalty=1.1,
            num_ctx=4096,
        ),
    }


# ---------- Core Orchestrator ----------

async def blogwriter_orchestrator(
    title: str,
    abstract: str = "",
    structure: Optional[List[str]] = None,
    agent_registry: Optional[Dict] = None,
    num_reviews: int = 10,
    write_output: bool = False,
    markdown_outpath: Optional[str] = None,
    plot_flows: bool = True,
) -> dict:
    """
    Esegue: Validazione -> Scrittura -> Editing/Review.
    Ritorna lo stato finale (editing_state).
    """
    if not title or not title.strip():
        raise ValueError("`title` non può essere vuoto.")
    if num_reviews < 1:
        raise ValueError("`num_reviews` deve essere >= 1.")

    structure = structure or []
    agent_registry = agent_registry or build_default_agent_registry()

    # Cartella per i diagrammi
    flow_dir = Path(__file__).resolve().parent / "flow_chart"
    flow_dir.mkdir(parents=True, exist_ok=True)

    # Path markdown (fallback dal titolo)
    md_path: Optional[Path] = None
    if write_output:
        if markdown_outpath:
            md_path = Path(markdown_outpath)
            md_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            default_name = f"{_slugify(title)}.md"
            md_path = (Path.cwd() / "outputs" / default_name).resolve()
            md_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Avvio InputValidatorCrew...")
    validator = InputValidatorCrew(agent_registry=agent_registry)
    validated_state = await validator.kickoff(
        title=title.strip(),
        abstract=abstract.strip(),
        structure=structure,
    )
    if plot_flows:
        validator.flow.plot(filename=str(flow_dir / "InputValidatorFlow"))

    logging.info("Avvio WritingCrew...")
    writer = WritingCrew(state=validated_state, agent_registry=agent_registry)
    written_state = await writer.kickoff()
    if plot_flows:
        writer.flow.plot(filename=str(flow_dir / "WritingFlow"))

    logging.info("Avvio EditingCrew...")
    editor = EditingCrew(state=written_state, agent_registry=agent_registry)
    editing_state = await editor.kickoff(
        num_reviews=num_reviews,
        write_output=write_output,
        markdown_outpath=str(md_path) if md_path else None,
    )
    if plot_flows:
        editor.flow.plot(filename=str(flow_dir / "EditingFlow"))

    logging.info("Flusso completato.")
    return editing_state


# ---------- CLI ----------

def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestratore BlogWriter")
    parser.add_argument("--title", required=True, help="Titolo dell'articolo")
    parser.add_argument("--abstract", default="", help="Abstract iniziale (facoltativo)")
    parser.add_argument(
        "--structure",
        nargs="*",
        default=[],
        help="Sezioni (es. --structure Introduzione 'Metodologia & Dati' Conclusioni)",
    )
    parser.add_argument(
        "--num_reviews",
        type=int,
        default=10,
        help="Numero di review critiche (>=1). Default: 10",
    )
    parser.add_argument(
        "--write_output",
        action="store_true",
        help="Se presente, scrive il Markdown su file.",
    )
    parser.add_argument(
        "--markdown_outpath",
        default=None,
        help="Path file Markdown di output. Se omesso, usa ./outputs/<slug(title)>.md",
    )
    parser.add_argument(
        "--no_plot_flows",
        action="store_true",
        help="Disabilita la generazione dei diagrammi di flow.",
    )
    parser.add_argument(
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Livello di logging. Default: INFO",
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    # Esecuzione
    asyncio.run(
        blogwriter_orchestrator(
            title=args.title,
            abstract=args.abstract,
            structure=args.structure,
            agent_registry=None,  # override qui se vuoi leggere da YAML/JSON
            num_reviews=args.num_reviews,
            write_output=args.write_output,
            markdown_outpath=args.markdown_outpath,
            plot_flows=not args.no_plot_flows,
        )
    )


if __name__ == "__main__":
    main()
