module.exports = {
  apps: [
    {
      name: 'fastapi-app',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8008 --workers 4',
      interpreter: 'python3',
      env: {
        "AWS_ACCESS_KEY_ID": "your_aws_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "your_aws_secret_access_key",
        "OPENAI_API_KEY": "your_openai_api_key",
        "CLAUDE_API_KEY": "your_claude_api_key",
        "BEARER_TOKEN": "your_bearer_token"
      }
    },
    {
      name: 'celery-worker',
      script: 'python',  // Point to the Python executable
      args: '-m celery -A app.tasks.celery_app worker --loglevel=info',  // Correct module path
      interpreter: 'python3',
      // cwd: '/path/to/your/project/root',  // Ensure you provide the correct path to your project root
      env: {
        "AWS_ACCESS_KEY_ID": "your_aws_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "your_aws_secret_access_key",
        "OPENAI_API_KEY": "your_openai_api_key",
        "CLAUDE_API_KEY": "your_claude_api_key",
        "BEARER_TOKEN": "your_bearer_token"
      }
    }    
  ]
};
