SHELL := /bin/bash
VENV_DIR := .venv-rota-em-dia
PYTHON := $(if $(wildcard $(VENV_DIR)/bin/python),$(VENV_DIR)/bin/python,python3)
PIP := $(if $(wildcard $(VENV_DIR)/bin/pip),$(VENV_DIR)/bin/pip,pip3)

.PHONY: menu setup analise notebook slides relatorio apresentacao-pdf tudo validar

menu:
	@echo "Rota em Dia - escolha uma opção:"
	@echo "1) Preparar ambiente Python"
	@echo "2) Gerar análise e gráficos"
	@echo "3) Gerar e executar notebook"
	@echo "4) Gerar slides"
	@echo "5) Gerar relatório"
	@echo "6) Gerar todos os entregáveis"
	@echo "7) Validar entregáveis"
	@read -r -p "Opção: " option; \
	case "$$option" in \
		1) $(MAKE) setup ;; \
		2) $(MAKE) analise ;; \
		3) $(MAKE) notebook ;; \
		4) $(MAKE) slides ;; \
		5) $(MAKE) relatorio ;; \
		6) $(MAKE) tudo ;; \
		7) $(MAKE) validar ;; \
		*) echo "Opção inválida."; exit 1 ;; \
	esac

setup:
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt
	@echo "Ambiente preparado em $(VENV_DIR)."

analise:
	$(PYTHON) fontes/analise.py

notebook: analise
	$(PYTHON) fontes/gerar_notebook.py
	$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace transporte_fretado_rota_em_dia.ipynb --ExecutePreprocessor.timeout=600

slides: analise
	$(PYTHON) fontes/gerar_slides.py

relatorio: analise
	$(PYTHON) fontes/gerar_relatorio.py

apresentacao-pdf: slides
	libreoffice --headless --convert-to pdf --outdir docs/apresentacao docs/apresentacao/apresentacao_rota_em_dia.pptx

tudo: analise notebook slides relatorio apresentacao-pdf
	@echo "Entregáveis gerados com sucesso."

validar:
	$(PYTHON) -m py_compile fontes/*.py
	unzip -t docs/apresentacao/apresentacao_rota_em_dia.pptx
	pdfinfo docs/relatorio/relatorio_tecnico_rota_em_dia.pdf | grep -E 'Pages|Page size'
	pdfinfo docs/apresentacao/apresentacao_rota_em_dia.pdf | grep -E 'Pages|Page size'
	@echo "Validação estrutural concluída."
