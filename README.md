# BlogWriter

BlogWriter è un framework modulare basato su [CrewAI](https://github.com/joaomdmoura/crewai) pensato per produrre articoli tecnici partendo da titolo, abstract e scaletta, orchestrando fasi di validazione, scrittura, generazione di codice ed editing finale.

## Caratteristiche principali
- **Validazione dell'input**: un flow asincrono verifica e arricchisce titolo, abstract e struttura tramite agenti dedicati, con parsing sicuro della scaletta e metriche di logging automatiche.
- **Scrittura sezione per sezione**: la crew di writing produce paragrafi coerenti, riassunti, eventuali istruzioni per il codice e richiede snippet Python solo quando necessari.
- **Generazione e revisione del codice**: per ogni sezione che lo richiede, un agente sviluppatore crea il codice mentre un revisore lo migliora prima dell'inclusione nell'articolo.
- **Editing e supervisione finale**: il flow di editing assemblea l'articolo in Markdown, sostituisce i placeholder del codice e, se configurato, avvia una revisione editoriale automatica.
- **Configurazione da YAML**: agenti, task e LLM sono definiti tramite file YAML e un registry centralizzato che semplifica l'estensione del sistema.
- **Metriche e logging avanzati**: un logger personalizzato evita duplicati, persiste i log su file e calcola statistiche riepilogative utili per il monitoraggio dei flow.

## Architettura della repository
```
blogwriter/
├── crews/                # Definizioni di crew e flow (validazione, scrittura, editing)
├── dashboards/           # Bozze di dashboard Streamlit per audit e revisione
├── llm/                  # Wrapper verso modelli Ollama utilizzati dagli agenti
├── notebooks/            # Notebook Jupyter di test end-to-end dei flow
├── orchestrator/         # Orchestratore CLI per concatenare i flow principali
├── schema/               # Pydantic model dello stato condiviso fra i flow
├── utils/                # Loader di configurazioni, logger e utility LLM
├── tests/                # Segnaposto per test automatici (da completare)
└── pyproject.toml        # Gestione dipendenze tramite Poetry
```

## Requisiti
- Python 3.10 – 3.12
- [Poetry](https://python-poetry.org/) per la gestione delle dipendenze
- Un server [Ollama](https://ollama.com/) raggiungibile (default `http://localhost:11434`) con i modelli indicati nel registry (`ollama/gpt-oss:20b`, `ollama/deepseek-coder:33b`, `ollama/gemma3:27b`, `ollama/phi4`).

```bash
poetry install
```

Per esecuzioni headless è consigliato disabilitare la telemetria di CrewAI e di eventuali proxy, come fatto nel notebook dimostrativo.

## Flussi disponibili
### 1. InputValidatorFlow
- Richiede titolo, abstract facoltativo e struttura (lista di sezioni).
- Se l'abstract manca viene generato, altrimenti migliorato.
- La struttura proposta dagli utenti viene analizzata, ampliata o ricostruita usando un agente project manager.
- Al termine salva un riepilogo dei log nel campo `log_summary` dello stato finale.

### 2. WritingArticleFlow
- Elabora lo stato validato, ciclando sulle sezioni finché tutte sono complete.
- Per ogni sezione salva paragrafo, riassunto sintetico e istruzioni per il codice.
- Attiva automaticamente le crew di code generation e code review se è stato segnalato il marker `[CODICE_RICHIESTO]`.
- Raccoglie log e metriche al termine dell'ultima sezione.

### 3. EditingFlow
- Riceve titolo, abstract, paragrafi, snippet di codice e struttura.
- Costruisce l'articolo finale in Markdown sostituendo i placeholder del codice.
- Se configurato, lancia una supervisione editoriale e registra un report dedicato.
- Persiste le metriche del logger su file se disponibile un `RotatingFileHandler`.

## Orchestrazione end-to-end
L'orchestratore CLI concatena validazione e scrittura, generando anche i diagrammi dei flow in `orchestrator/flow_chart/`.

```bash
poetry run python -m orchestrator.orchestrator --title "Titolo" \
    --abstract "Abstract opzionale" \
    --structure Introduzione Corpo Conclusioni
```

Per includere la fase di editing è possibile importare direttamente le crew nei propri script Python, come mostrato nel notebook `notebooks/check_components.ipynb` che testa in sequenza i tre flow.

## Notebook di validazione
Il notebook `notebooks/check_components.ipynb` disattiva la telemetria, istanzia le tre crew (validazione, scrittura, editing) e ne verifica il comportamento asincrono producendo come output lo stato finale dell'articolo completo.

Esempio di uso programmatico (estratto dal notebook):

```python
state = await InputValidatorCrew().kickoff(title="Titolo", abstract="", structure=[...])
state2 = await WritingCrew().kickoff(title=state.title, abstract=state.abstract, structure=state.structure)
state3 = await EditingCrew().kickoff(
    title=state2.title,
    abstract=state2.abstract,
    structure=state2.structure,
    paragraphs=state2.paragraphs,
    code_snippets=state2.code_snippets,
)
```

## Personalizzazione degli agenti
- Gli agenti e i task sono definiti rispettivamente in `crews/*/agents.yaml` e `crews/*/tasks.yaml`.
- `utils/config_loader.build_agents_from_yaml` carica dinamicamente i tool, associa gli LLM dal registry e permette di sostituire facilmente i modelli fornendo un `agent_registry` personalizzato.
- I task di writing codificano le convenzioni sul marker `[CODICE_RICHIESTO]`, mentre quelli di editing gestiscono l'assemblaggio Markdown e la supervisione.

## Logging e metriche
- Il logger `NonRepetitiveLogger` evita duplicati e può scrivere su file rotanti in `logs/`.
- `summarize_log_metrics` analizza i log generando statistiche (conteggio livelli, durata, top messaggi) che vengono salvate nello stato dei flow al termine dell'esecuzione.

## Dashboard sperimentali
Sono presenti due app Streamlit (`dashboards/streamlit_audit.py` e `dashboards/streamlit_editor.py`) che fungeranno da interfaccia per esplorare log e revisioni. Richiedono ulteriori utility (`blogwriter.utils.flow_plotter`, `FlowLogger`) non ancora incluse nella repo corrente e vanno considerate work-in-progress.

## Test
La cartella `tests/` contiene placeholder da popolare; si consiglia di aggiungere unit test per i parser dei flow e per il logger, sfruttando l'infrastruttura Poetry (`poetry run pytest`).

## Contributi
1. Fork del progetto e creazione di un branch dedicato.
2. Installazione delle dipendenze con Poetry.
3. Aggiunta o modifica di agenti/task aggiornando i rispettivi file YAML.
4. Apertura di una Pull Request descrivendo le modifiche e l'impatto sui flow.