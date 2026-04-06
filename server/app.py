import os
import sys
import uvicorn
from fastapi import FastAPI

# Ensure Python can find models in the root folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.saga_environment import SagaEnvironment
from models import ProvisionAction

env = SagaEnvironment()
app = FastAPI(title="Cloud Saga Orchestrator API", version="1.0")

@app.get("/")
def read_root():
    """Health check endpoint for Hugging Face Spaces"""
    return {"status": "healthy", "message": "Cloud Saga Orchestrator API is running. Visit /docs for the UI."}

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
        return {"score": 1.0, "status": "Win - Fully Provisioned"}
    elif len(env.state.provisioned_graph) == 0 and env.state.step_count > 0:
        return {"score": 1.0, "status": "Win - Clean Abort"}
    elif env.state.step_count >= env.state.max_steps:
        return {"score": 0.0, "status": "Loss - Zombie Resources Running"}
    else:
        progress = len(env.state.provisioned_graph) / len(env.state.target_architecture)
        return {"score": round(min(progress, 0.9), 2), "status": "In Progress"}

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()