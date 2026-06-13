# TeikoTechnical

Create a SQLite database for cell count data and run an analysis pipeline. 

## Make commands

To prepare the environment

```make setup```

To reproduce the analysis

```make pipeline```

To launch the analysis dashboard

```make dashboard```

To perform unit tests

```make test```

## Dashboard

The locally hosted dashboard is located at:
```http://localhost:8501/```

When using GitHub Codespaces, the dashboard is hosted at:
```<codespace-url>-8501.app.github.dev/```

## Database schema

```
PROJECT
  project_id              INTEGER  PK (autoincrement)
  project_id_text         INTEGER  PK (autoincrement)
  principal_investigator  TEXT
  company                 TEXT
  description             TEXT

SUBJECT
  subject_id       INTEGER  PK (autoincrement)
  subject_id_name  TEXT  PK
  condition        TEXT
  age              INTEGER
  sex              TEXT
  treatment        TEXT
  response         TEXT
  project_id       INTEGER FK → PROJECT
  project_id_text  TEXT

SAMPLE
  sample_id                 INTEGER  PK (autoincrement)
  sample_id_text            TEXT
  sample_type               TEXT
  time_from_treatment_start INTEGER
  subject_id                INTEGER  FK → SUBJECT
  subject_id_text           TEXT
  project_id                INTEGER FK → PROJECT
  project_id_text           TEXT
  
POPULATION
  population_id          INTEGER  PK (autoincrement)
  population_name        TEXT
  count                  INTEGER
  sample_id              INTEGER       FK → SAMPLE
  sample_id_text         TEXT
  subject_id             INTEGER  FK → SUBJECT
  subject_id_text        TEXT
  project_id             INTEGER FK → PROJECT
  project_id_text        TEXT
```

The schema normalizes the data into five tables: PROJECT, SUBJECT, SAMPLE, and POPULATION. A project table isn't needed at this scale with three projects but as the number of projects increases into the hundreds, having an index of the projects with associated principal investigators and company will become valuable. Storing the cell population type in long format in the POPULATION table allows new cell types to be added easily in future projects and allows for easy aggregation of the counts. A new integer primary key was created for each table in order to avoid potential problems with subject IDs being reused between projects. This has the added benefit of increasing the efficiency of joins.

## Code structure

```TeikoTechnical/
├── load_data.py                # Generate and populate the SQLite database
├── cell-count.db               # SQLite Database
├── analysis.py                 # Run the analysis pipeline and generate outputs without dashboard
├── makefile                    
├── requirements.txt
├── data/                       
    └── cell-count.csv          # unprocessed data
├── output/                     # Output data and plots
├── pages/                      # Dashboard pages
    ├── data_overview.py        # Page for the cell population summary
    ├── statistical_analysis.py # Page for the miraclib response analysis
    └── subset_analysis.py      # Page for the selected subset of the data
├── utils/                      
    └── display.py              # Helper functions for streamlit rendering
```

The analysis is separate from the dashboard in order to simplify running the pipeline and improve debugging, as well as allow the dashboard pages to simply call functions. The dashboard has been separated into pages for clarity and to allow the complexity of the pages to grow without becoming unwieldy. 
