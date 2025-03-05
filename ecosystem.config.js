module.exports = {
  apps: [{
    name: "servidor",
    script: "app.py",
    interpreter: "venv/bin/python3",
    env: {
      NODE_ENV: "production"
    },
    watch: false,
    instances: 1,
    exec_mode: "fork",
    max_memory_restart: "1G",
    env_production: {
      NODE_ENV: "production"
    }
  }]
} 