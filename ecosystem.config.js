module.exports = {
  apps: [
    {
      name: 'redis-server',
      script: 'redis-server',
      args: '', // No arguments needed for the default configuration
      interpreter: 'none',
      env: {
        // Add any environment variables for Redis if needed
      }
    },
    {
      name: 'celery-worker',
      script: 'celery',
      args: '-A app.tasks.celery_config worker --loglevel=info',
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
      name: 'fastapi-app',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8008 --reload',
      interpreter: 'python3',
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
