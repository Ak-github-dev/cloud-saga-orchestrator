import os
import json
from openai import OpenAI
from server.saga_environment import SagaEnvironment
from models import ProvisionAction

# MANDATORY HACKATHON VARIABLES
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
TASK_NAME = "cloud-saga"
BENCHMARK = "openenv_saga"

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: str) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def run_inference():
    if not API_KEY:
        print("ERROR: HF_TOKEN or OPENAI_API_KEY environment variable is not set.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = SagaEnvironment()
    
    system_prompt = """You are a Cloud DevOps Agent. 
    Provision architecture strictly in this order: vpc -> ip -> disk -> gpu_vm -> dns.
    Output ONLY valid JSON: {"command": "create|delete|check_status", "resource_type": "vpc|ip|disk|gpu_vm|dns"}
    If you encounter a 403 or 504 error, you MUST stop creating and safely 'delete' active resources in REVERSE order to cleanly abort."""

    for level in ["easy", "medium", "hard"]:
        log_start(task=f"{TASK_NAME}-{level}", env=BENCHMARK, model=MODEL_NAME)
        
        obs = env.reset(task_level=level)
        done = False
        step_count = 0
        rewards = []
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Observation: {obs.model_dump_json()}"}]
        
        while not done and step_count < 15:
            step_count += 1
            error_msg = None
            
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                agent_reply = response.choices[0].message.content
                action_dict = json.loads(agent_reply)
                action = ProvisionAction(**action_dict)
                action_str = f"{action.command}({action.resource_type})"
            except Exception as e:
                error_msg = "JSON Parse Error"
                action_str = "invalid_action"
                action = ProvisionAction(command="check_status", resource_type="vpc")
            
            obs = env.step(action)
            reward = float(obs.reward)
            done = obs.done
            rewards.append(reward)
            
            log_step(step=step_count, action=action_str, reward=reward, done=done, error=error_msg)
            messages.append({"role": "assistant", "content": agent_reply if not error_msg else "{}"})
            messages.append({"role": "user", "content": f"Observation: {obs.model_dump_json()}"})
            
        success = (obs.reward > 0.0) 
        log_end(success=success, steps=step_count, score=obs.reward, rewards=rewards)

if __name__ == "__main__":
    run_inference()