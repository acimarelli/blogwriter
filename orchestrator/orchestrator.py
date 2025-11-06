import asyncio
import argparse
from pathlib import Path

from crews.input_validator.crew import InputValidatorCrew
from crews.writing.crew import WritingCrew
from crews.editing.crew import EditingCrew


async def blogwriter_orchestrator(title: str, 
                                  abstract: str = "", 
                                  structure: list[str] | None = None, 
                                  num_reviews: int = 10,
                                  write_output: bool = False,
                                  markdown_outpath: str | None = None):
    """Lancia il flusso di validazione e quello di scrittura."""
    structure = structure or []

    # Cartella in cui salvare i diagrammi dei flow
    flow_dir = Path(__file__).resolve().parent / "flow_chart"
    flow_dir.mkdir(parents=True, exist_ok=True)

    # 1) Validazione dell’input
    validator = InputValidatorCrew()
    validated_state = await validator.kickoff(
        title=title,
        abstract=abstract,
        structure=structure,
    )
    validator.flow.plot(filename=str(flow_dir / "InputValidatorFlow"))

    # 2) Scrittura dell’articolo 
    writer = WritingCrew(state=validated_state)
    written_state = await writer.kickoff()
    writer.flow.plot(filename=str(flow_dir / "WritingFlow"))

    # 3) Review+Editing dell’articolo
    editor = EditingCrew(state=written_state)
    editing_state = await editor.kickoff(
        num_reviews=num_reviews,
        write_output=write_output,
        markdown_outpath=markdown_outpath
    )
    editor.flow.plot(filename=str(flow_dir / "EditingFlow"))

    return editing_state


def main():
    parser = argparse.ArgumentParser(description="Orchestratore BlogWriter")
    parser.add_argument("--title", required=True, help="Titolo dell'articolo")
    parser.add_argument("--abstract", default="", help="Abstract iniziale (facoltativo)")
    parser.add_argument(
        "--structure",
        nargs="*",
        default=[],
        help="Elenco delle sezioni (es. --structure Introduzione Corpo Conclusione)",
    )
    args = parser.parse_args()

    asyncio.run(blogwriter_orchestrator(args.title, args.abstract, args.structure))


if __name__ == "__main__":
    main()
