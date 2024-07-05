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
2. Install Popplar
  2.1. For Windows:
    2.1.1. Goto GitHub - https://github.com/oschwartz10612/poppler-windows
    2.1.2. Download ZIP
    2.1.3. Extract to a location of your choice, preferrably
      2.1.3.1. C:\Progam Files\
    2.1.4. Add C:\Program Files\poppler-<0.68.0_x86>\bin (Text inside <> refers to version number it may differ upon the ZIP file you extracted) to your system PATH by doing the following: Click on the Windows start button, search for Edit the system environment variables, click on Environment Variables..., under System variables, look for and double-click on PATH, click on New, then add C:\Users\Program Files\poppler-0.68.0_x86\bin, click OK.
    2.1.5. If you are using a terminal to execute poppler (e.g. running pdf2image in command line), you may need to reopen your terminal for poppler to work.
  2.2. For MAC: brew install poppler
  2.3. For Linux: sudo apt-get install poppler-utils

3. pip install -r requirements.txt

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
      6. Stop redis - redis-cli shutdown
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
3. Start Celery Worker - celery -A app.tasks.celery_config worker --loglevel=info --logfile="app/logs/celery.log"
4. Start watchdog - python python watchdog_celery.py
  4.1. watchdog, watches change in app and restarts celery
  4.2. Not needed in prod, celery is supposed to be long running task handler
  4.3. Use in dev so that you dont need to manually restart celery on every change
  4.4. Not included in requirement.txt
  4.5. Manual installation - pip install watchdog
5. Start FastAPI server
  5.1. To start Uvicorn - uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
  5.2. To start Gunicorn - gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8008 --reload --log-level info

