.PHONY: help
help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY: setup
setup:  ## Install dependencies
	pip install -r requirements.txt

.PHONY: venv
venv:  ## Create virtual environment
	python3 -m venv venv
	@echo "Activate with: source venv/bin/activate"

.PHONY: pipeline
pipeline: ## Run the analysis pipeline
	python load_data.py
	python data_overview.py
	python statistical_analysis.py
	python subset_analysis.py