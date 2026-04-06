import uuid
from typing import Dict, List
from openenv.core.env_server import Environment
from models import ProvisionAction, ProvisionObservation, ProvisionState

COSTS = {"vpc": 0.10, "ip": 0.05, "disk": 0.50, "gpu_vm": 5.00, "dns": 0.10}

DEPENDS_ON = {
    "vpc": [], "ip": ["vpc"], "disk": ["vpc"], 
    "gpu_vm": ["ip", "disk"], "dns": ["gpu_vm"]
}

REQUIRED_FOR = {
    "vpc": ["ip", "disk"], "ip": ["gpu_vm"], "disk": ["gpu_vm"], 
    "gpu_vm": ["dns"], "dns": []
}

class SagaEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = ProvisionState()
        self._hard_mode_timeout_flag = False

    def reset(self, seed=None, episode_id=None, task_level="easy", **kwargs) -> ProvisionObservation:
        self._state = ProvisionState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            task_difficulty=task_level,
            provisioned_graph={},
            total_wasted_money=0.0
        )
        self._hard_mode_timeout_flag = (task_level == "hard")
        return self._build_observation("Environment initialized. Awaiting provision commands.", 200)

    def step(self, action: ProvisionAction, **kwargs) -> ProvisionObservation:
        self._state.step_count += 1
        cmd = action.command
        rtype = action.resource_type
        
        current_burn = sum(COSTS[r] for r in self._state.provisioned_graph.keys())
        self._state.total_wasted_money += current_burn
        step_reward = -0.05 
        
        msg, status = "", 500

        if cmd == "create":
            if rtype in self._state.provisioned_graph:
                msg, status, step_reward = f"409 Conflict: {rtype} already exists.", 409, -0.1
            else:
                missing_deps = [dep for dep in DEPENDS_ON[rtype] if dep not in self._state.provisioned_graph]
                if missing_deps:
                    msg, status, step_reward = f"400 Bad Request: Missing dependencies {missing_deps}", 400, -0.2
                elif self._state.task_difficulty == "medium" and rtype == "gpu_vm":
                    msg, status, step_reward = "403 Insufficient Quota: Out of GPUs.", 403, 0.0 
                elif self._state.task_difficulty == "hard" and rtype == "disk" and self._hard_mode_timeout_flag:
                    self._state.provisioned_graph[rtype] = f"res_{rtype}_{uuid.uuid4().hex[:6]}"
                    self._hard_mode_timeout_flag = False 
                    msg, status, step_reward = "504 Gateway Timeout: Storage backend unresponsive.", 504, 0.0
                else:
                    self._state.provisioned_graph[rtype] = f"res_{rtype}_{uuid.uuid4().hex[:6]}"
                    msg, status, step_reward = f"201 Created: {rtype} provisioned.", 201, 0.1

        elif cmd == "delete":
            if rtype not in self._state.provisioned_graph:
                msg, status, step_reward = f"404 Not Found: {rtype} does not exist.", 404, -0.1
            else:
                blocking_resources = [res for res in REQUIRED_FOR[rtype] if res in self._state.provisioned_graph]
                if blocking_resources:
                    msg, status, step_reward = f"409 Conflict: Cannot delete {rtype} while {blocking_resources} are attached.", 409, -0.2
                else:
                    del self._state.provisioned_graph[rtype]
                    msg, status, step_reward = f"200 OK: {rtype} deleted.", 200, 0.2 

        elif cmd == "check_status":
            if rtype in self._state.provisioned_graph:
                msg, status, step_reward = f"200 OK: {rtype} is running.", 200, 0.05
            else:
                msg, status, step_reward = f"404 Not Found: {rtype} is not provisioned.", 404, 0.05
        else:
            msg, status, step_reward = f"400 Bad Request: Unknown command.", 400, -0.5

        done = False
        terminal_reward = 0.0

        if len(self._state.provisioned_graph) == len(self._state.target_architecture):
            done, terminal_reward, msg = True, 1.0, "WIN: Architecture fully provisioned!"
        elif status in [403, 504] and len(self._state.provisioned_graph) == 0:
            done, terminal_reward, msg = True, 1.0, "WIN: Clean Abort detected. Zero zombie resources."
        elif self._state.step_count >= self._state.max_steps:
            done = True
            if len(self._state.provisioned_graph) > 0:
                terminal_reward, msg = -1.0, f"GAME OVER: Zombie resources running: {list(self._state.provisioned_graph.keys())}"
            else:
                terminal_reward = 0.5 

        total_reward = step_reward + terminal_reward
        return self._build_observation(msg, status, reward=total_reward, done=done)

    def _build_observation(self, message: str, status: int, reward: float = 0.0, done: bool = False) -> ProvisionObservation:
        current_burn = sum(COSTS[r] for r in self._state.provisioned_graph.keys())
        return ProvisionObservation(
            message=message, last_status_code=status,
            active_resources=self._state.provisioned_graph.copy(),
            hourly_burn_rate=current_burn, reward=reward, done=done
        )

    @property
    def state(self) -> ProvisionState:
        return self._state