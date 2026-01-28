module.exports = {
  apps: [
    {
      name: 'autolabel-backend',
      cwd: '/home/administrator/autoannotation/backend',
      script: '/home/administrator/autoannotation/.venv/bin/uvicorn',
      args: 'app.main:app --host 127.0.0.1 --port 8000',
      interpreter: 'none',
      env: {
        PATH: '/home/administrator/autoannotation/.venv/bin:' + process.env.PATH,
        GOOGLE_APPLICATION_CREDENTIALS: '/home/administrator/autoannotation/KEY_FILE',
        GCP_PROJECT_ID: 'regal-hybrid-445815-n1',
        AIRFLOW_TOKEN_SECRET_ID: 'airflow-default-token'
      }
    },
    {
      name: 'autolabel-frontend',
      cwd: '/home/administrator/autoannotation/frontend',
      script: 'npm',
      args: 'start',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      }
    }
  ]
};
