from crewai import Agent, Task, Crew, Process
from llm.local_llm_tool import LocalLLMTool


def summarize_section(section: str, content: str, model_name: str = 'ollama/phi4') -> str:
    llm = LocalLLMTool(model=model_name)

    summarizer = Agent(
        role="Article Summarizer",
        goal="Sintetizzare efficacemente i contenuti di ogni sezione dell’articolo",
        backstory="Esperto in scrittura tecnico-scientifica sintetica. Genera riassunti compatti e informativi per sezioni articolate di un contenuto.",
        llm=llm,
        allow_delegation=False,
        verbose=False
    )

    task = Task(
        description="Genera un riassunto (max 5 frasi) per la sezione '{section}' dell'articolo:\n\n{content}",
        agent=summarizer,
        expected_output="Riassunto coerente e informativo della sezione '{section}'"
    )

    crew = Crew(
        agents=[summarizer],
        tasks=[task],
        process=Process.sequential
    )

    result = crew.kickoff(inputs={"section":section, "content":content})

    return result.__dict__['raw']

# def summarize_context(previous_summaries: dict, model_name: str = "local_chatollama") -> str:
#     if not previous_summaries:
#         return ""

#     full_text = "\n".join(previous_summaries.values())
#     llm = OllamaLLMTool(model=model_name)

#     context_summarizer = Agent(
#         role="Global Context Synthesizer",
#         goal="Sintetizzare il contesto cumulato delle sezioni precedenti in modo coeso",
#         backstory="Editor esperto nella continuità narrativa tra sezioni di contenuto tecnico-divulgativo.",
#         llm=llm,
#         allow_delegation=False,
#         verbose=False
#     )

#     task = Task(
#         description=f"Fornisci una sintesi narrativa coerente delle seguenti sezioni già scritte:\n\n{full_text}",
#         agent=context_summarizer,
#         expected_output="Sintesi fluida e coerente delle sezioni precedenti."
#     )

#     crew = Crew(
#         agents=[context_summarizer],
#         tasks=[task],
#         process=Process.Sequential
#     )

#     return crew.kickoff()