import asyncio
import argparse
from pathlib import Path

from crews.input_validator.crew import InputValidatorCrew
from crews.writing.crew import WritingCrew


async def blogwriter_orchestrator(title: str, abstract: str = "", structure: list[str] | None = None):
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
    writer = WritingCrew()
    final_state = await writer.kickoff(
        title=validated_state.title,
        abstract=validated_state.abstract,
        structure=validated_state.structure,
    )
    writer.flow.plot(filename=str(flow_dir / "WritingValidatorFlow"))

    return final_state


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
