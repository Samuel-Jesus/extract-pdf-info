module.exports = {
    apps: [{
        name: "pdf-extractor-api",
        script: "run.py",
        interpreter: process.platform === "win32" ? "./venv/Scripts/python" : "./venv/bin/python",
        instances: 1,
        autorestart: true,
        watch: false,
        max_memory_restart: "1G",
        env: {
            NODE_ENV: "production"
        }
    }]
}