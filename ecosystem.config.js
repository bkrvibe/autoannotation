module.exports = {
  apps: [
    {
      name: 'autolabel-backend',
      cwd: '/home/administrator/autoannotation/backend',
      script: '/home/administrator/autoannotation/.venv/bin/uvicorn',
      args: 'app.main:app --host 127.0.0.1 --port 8000',
      interpreter: 'none',
      env: {
        PATH: '/home/administrator/autoannotation/.venv/bin:' + process.env.PATH
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
