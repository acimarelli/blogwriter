import ast
import os
from typing import Optional
import json
import re
from pathlib import Path

from crewai.flow import Flow, start, router, listen, or_
from schema.state import ArticleState
from utils.logger import get_logger, summarize_log_metrics
from utils.config_loader import build_crew
from utils.context_summarizer_crew import summarize_section
from utils.markdown_utils import MarkdownUtils
from logging.handlers import RotatingFileHandler

logger = get_logger("WritingArticleFlow")


class WritingArticleFlow(Flow[ArticleState]):
    def __init__(self, 
                 agents: dict, 
                 tasks: dict, 
                 state: ArticleState
                 ):
        super().__init__(**state.model_dump())
        self.agents = agents
        self.tasks = tasks

    @start()
    def start_article(self):
        print("📝 Inizio generazione sezioni articolo...")
        self.state.current_section_index = 0

    @router(or_(start_article, "loop_till_last_section"))
    def check_written_sections(self):
        if self.state.current_section_index==len(self.state.structure):
            return "end_article_writing"
        else:
            return "article_writing"

    @listen("article_writing")
    def write_section(self): 
        if self.state.current_section_index==0:
            logger.info("🚀 Attivo la crew per la generazione sezioni articolo...")

        writing_crew = build_crew(
            agents=self.agents,
            tasks=self.tasks,
            agent_keys=["writer"],
            task_keys=["write_task"]
        )
        
        logger.info(f"📝 Scrittura sezione {self.state.structure[self.state.current_section_index]}")
        result = writing_crew.kickoff(inputs={
                "section": self.state.structure[self.state.current_section_index],
                "title": self.state.title,
                "abstract": self.state.abstract,
                "previous_sections_summary": self.state.section_summaries if self.state.current_section_index>0 else {}
            })
        
        self.state.paragraphs[self.state.structure[self.state.current_section_index]] = result.__dict__['raw']
        self.state.section_summaries[self.state.structure[self.state.current_section_index]] = summarize_section(section=self.state.structure[self.state.current_section_index], 
                                                                                                                 content=result.__dict__['raw'])
        self.state.code_instructions[self.state.structure[self.state.current_section_index]] = WritingArticleFlow.extract_code_request(result.__dict__['raw'])

        return self.state
    
    @router(write_section)
    def code_generation_node(self):
        if self.state.code_instructions[self.state.structure[self.state.current_section_index]] != "":
            return "code_generation"
        else:
            self.state.code_snippets[self.state.structure[self.state.current_section_index]] = ""
            return "no_coding_section"

    @listen("code_generation")
    def write_code(self):
        logger.info(f"🚀 Attivo la crew per la generazione del codice interno alla sezione {self.state.structure[self.state.current_section_index]}")
        coding_crew = build_crew(
            agents=self.agents,
            tasks=self.tasks,
            agent_keys=["code_writer"],
            task_keys=["generate_code_task"]
        )

        logger.info("📝 Generazione codice...")
        result = coding_crew.kickoff(inputs={
            "instruction": self.state.code_instructions[self.state.structure[self.state.current_section_index]]
        })
        
        # self.state.code_instructions[self.state.structure[self.state.current_section_index]] = self.state.code_instructions[self.state.structure[self.state.current_section_index]]
        self.state.code_snippets[self.state.structure[self.state.current_section_index]] = result.__dict__['raw'] if result != "" else result

        return self.state 
    
    @listen(write_code)
    def update_code(self):
        logger.info(f"🚀 Attivo la crew per la modifica del codice generato per la sezione {self.state.structure[self.state.current_section_index]}")
        coding_review_crew = build_crew(
            agents=self.agents,
            tasks=self.tasks,
            agent_keys=["code_reviewer"],
            task_keys=["review_code_task"]
        )

        logger.info(f"📝 Modifiche al codice...")
        result = coding_review_crew.kickoff(inputs={
            "code": self.state.code_snippets[self.state.structure[self.state.current_section_index]]
            })
        self.state.code_snippets[self.state.structure[self.state.current_section_index]] = result.__dict__['raw'] 

        return self.state

    @listen(or_("no_coding_section", update_code))
    def loop_till_last_section(self):
        self.state.current_section_index = self.state.current_section_index + 1
        return "loop_till_last_section"

    @listen("end_article_writing")
    def conclude(self):
        logger.info("🏁 Flow terminato con successo.")
        
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

    @staticmethod
    def extract_code_request(paragraph: str) -> str:
        match = re.search(r"\[CODICE_RICHIESTO\]\[START\]\s*(.*?)\s*\[END\]", paragraph, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    async def run_async(self, export_log_summary: bool = True) -> ArticleState:
        logger.info("🚀 Avvio asincrono del flow WritingArticleFlow")
        final_state = await self.kickoff_async()
        self.final_state = final_state
        return final_state
