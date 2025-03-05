module.exports = {
  apps: [{
    name: "servidor",
    script: "./app.py",
    interpreter: "./venv/bin/python3",
    cwd: ".",
    env: {
      NODE_ENV: "production",
      PYTHONUNBUFFERED: "1"
    },
    watch: false,
    instances: 1,
    exec_mode: "fork",
    max_memory_restart: "1G",
    env_production: {
      NODE_ENV: "production",
      PYTHONUNBUFFERED: "1"
    },
    error_file: "logs/err.log",
    out_file: "logs/out.log",
    log_date_format: "YYYY-MM-DD HH:mm:ss",
    merge_logs: true
  }]
} 