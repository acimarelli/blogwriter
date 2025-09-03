run:
	poetry run python run_cli.py --title "Titolo demo" --structure Introduzione Contenuto Conclusione

test:
	poetry run pytest tests/

dashboard:
	poetry run streamlit run dashboards/streamlit_editor.py

audit:
	poetry run streamlit run dashboards/streamlit_audit.py
