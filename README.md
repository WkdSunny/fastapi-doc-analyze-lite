```
fastapi-iac-py
├─ .gitignore
├─ app
│  ├─ config.py
│  ├─ dependencies.py
│  ├─ main.py
│  ├─ models
│  │  ├─ pdf_model.py
│  │  ├─ response_model.py
│  │  └─ __init__.py
│  ├─ routers
│  │  ├─ convert.py
│  │  ├─ extract
│  │  │  ├─ claude.py
│  │  │  ├─ openai.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ llm_clients
│  │  │  ├─ claude.py
│  │  │  └─ openai.py
│  │  ├─ processors
│  │  │  ├─ excel.py
│  │  │  ├─ pdf
│  │  │  │  ├─ muPDF.py
│  │  │  │  ├─ pdf_miner.py
│  │  │  │  ├─ pdf_tasks.py
│  │  │  │  ├─ pyPDF2.py
│  │  │  │  ├─ tesseract.py
│  │  │  │  ├─ textract.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ word.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ tasks
│  │  ├─ aws_services.py
│  │  ├─ celery_config.py
│  │  ├─ pdf_tasks.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ ecosystem.config.js
├─ README.md
└─ requirements.txt

```