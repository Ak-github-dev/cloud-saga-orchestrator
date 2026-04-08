import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Ensure Python can find models in the root folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.saga_environment import SagaEnvironment
from models import ProvisionAction

env = SagaEnvironment()
app = FastAPI(title="Cloud Saga Orchestrator API", version="1.0")

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Sleek HTML Landing Page for Hugging Face Spaces"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌩️ Cloud Saga Orchestrator</title>
        <style>
            body {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }
            h1 { font-size: 3rem; margin-bottom: 0.5rem; background: -webkit-linear-gradient(#818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            p { font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin-bottom: 2rem; line-height: 1.6; }
            .button-container { display: flex; gap: 20px; }
            .btn {
                text-decoration: none;
                padding: 15px 30px;
                font-size: 1.2rem;
                font-weight: bold;
                border-radius: 8px;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .btn-api { background-color: #3b82f6; color: white; box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.39); }
            .btn-ui { background-color: #8b5cf6; color: white; box-shadow: 0 4px 14px 0 rgba(139, 92, 246, 0.39); }
            .btn:hover { transform: translateY(-2px); }
            .status { margin-top: 40px; font-size: 0.9rem; color: #10b981; display: flex; align-items: center; gap: 8px; }
            .dot { height: 10px; width: 10px; background-color: #10b981; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px #10b981; }
        </style>
    </head>
    <body>
        <h1>Cloud Saga Orchestrator</h1>
        <p>A high-fidelity Reinforcement Learning environment tackling the $44.5B enterprise problem of Cloud "Zombie Resources" and Distributed State Failures.</p>
        
        <div class="button-container">
            <a href="/docs" class="btn btn-api">⚙️ Open API Docs</a>
            <a href="https://huggingface.co/spaces/AamirK/cloud-saga-interactive-demo" target="_blank" class="btn btn-ui">🎮 Try Interactive UI</a>
        </div>

        <div class="status"><span class="dot"></span> Backend Engine is Live and Healthy</div>
    </body>
    </html>
    """
    return html_content

@app.post("/reset")
def reset_env(task_level: str = "easy"):
    return env.reset(task_level=task_level)

@app.post("/step")
def step_env(action_data: dict):
    action = ProvisionAction(**action_data)
    return env.step(action)

@app.get("/state")
def get_state():
    return env.state

@app.get("/tasks")
def get_tasks():
    return {
        "tasks": ["easy", "medium", "hard"],
        "action_schema": {
            "command": "string (MUST BE: 'create', 'delete', or 'check_status')",
            "resource_type": "string (MUST BE: 'vpc', 'ip', 'disk', 'gpu_vm', 'dns')",
            "resource_id": "string (Optional)"
        }
    }

@app.get("/grader")
def get_grader():
    if len(env.state.provisioned_graph) == len(env.state.target_architecture):
        return {"score": 0.99, "status": "Win - Fully Provisioned"}
    elif len(env.state.provisioned_graph) == 0 and env.state.step_count > 0:
        return {"score": 0.99, "status": "Win - Clean Abort"}
    elif env.state.step_count >= env.state.max_steps:
        return {"score": 0.01, "status": "Loss - Zombie Resources Running"}
    else:
        progress = len(env.state.provisioned_graph) / len(env.state.target_architecture)
        safe_score = round(max(0.01, min(progress, 0.98)), 2)
        return {"score": safe_score, "status": "In Progress"}

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()