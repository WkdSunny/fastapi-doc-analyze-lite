# Project Structure
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
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  ├─ routers
│  │  ├─ convert.py
│  │  ├─ extract
│  │  │  ├─ claude.py
│  │  │  ├─ openai.py
│  │  │  ├─ __init__.py
│  │  │  └─ __pycache__
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  ├─ services
│  │  ├─ llm_clients
│  │  │  ├─ claude.py
│  │  │  ├─ openai.py
│  │  │  └─ __pycache__
│  │  ├─ processors
│  │  │  ├─ excel.py
│  │  │  ├─ pdf
│  │  │  │  ├─ muPDF.py
│  │  │  │  ├─ pdf_miner.py
│  │  │  │  ├─ pdf_tasks.py
│  │  │  │  ├─ pyPDF2.py
│  │  │  │  ├─ tesseract.py
│  │  │  │  ├─ textract.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ word.py
│  │  │  ├─ __init__.py
│  │  │  └─ __pycache__
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  ├─ tasks
│  │  ├─ aws_services.py
│  │  ├─ celery_config.py
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  ├─ __init__.py
│  └─ __pycache__
├─ ecosystem.config.js
├─ README.md
└─ requirements.txt

```

# Deployment Instruction
1. Git clone
2. pip install -r requirements.txt

# Starting the Server
1. Install Redis
  For Windows:
    URL: https://github.com/microsoftarchive/redis/releases
    Steps:
      1. Goto the URL download the latest release (*.msi)
      2. Install, remember to the add the location to the environment PATH variable of system variables
      3. Set the port to - 6379
        3.1. If you change the port same has to be changed in the env variables
          3.1.1. In ".env" for local
          3.1.2. In ecosystem.config.js for prod
      4. Start redis server -
        4.1. Local: "redis-server"
      5. You can check using "redis-cli ping"
    Note: Windows may need to be restarted before starting redis server and system variables take effect after windows restart.

  For MAC:
    Steps: 
      1. brew install redis
      2. Start redis server -
        2.1. Local: brew services start redis
        2.2. Prod: Use ecosystem.config.js
      3. You can check using "redis-cli ping"

  For Linux:
    Steps: 
      1. sudo apt update
      2. sudo apt install redis-server
      3. Start redis server -
        3.1. sudo systemctl start redis
        3.2. sudo systemctl enable redis
      4. You can check using "redis-cli ping"

2. Start Redis Server
3. Start Celery Worker - celery -A app.tasks.celery_config worker --loglevel=info
4. Start Uvicorn - uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
