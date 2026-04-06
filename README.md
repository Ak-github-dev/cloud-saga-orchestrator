---
title: Cloud Saga Orchestrator
emoji: 🌩️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - devops
  - finops
---

# 🌩️ Cloud Saga Orchestrator (OpenEnv)

**A high-fidelity Reinforcement Learning environment tackling a $17B enterprise problem: Cloud "Zombie Resources" and Distributed State Failures.**

---

## 📖 Motivation & Real-World Utility (The "Why")

When massive enterprises provision cloud infrastructure (VPCs, IPs, Disks, VMs), they rely on Directed Acyclic Graphs (DAGs). If a provisioning sequence fails halfway through (e.g., a sudden GPU quota error or network timeout), standard deterministic scripts often crash, leaving partial infrastructure running indefinitely. These are known as **"Zombie Resources,"** costing companies billions annually in wasted cloud spend (FinOps). 

Furthermore, resolving these partial failures requires implementing the **Saga Pattern**—a complex distributed systems concept where an agent must traverse a dependency graph backward to safely tear down resources. Standard LLMs fail at this because they lack temporal reasoning, panic during timeouts, or execute teardowns out of order (causing dependency lock-ups).

This environment trains an RL Agent to act as a **Resilient DevOps Orchestrator**. The agent must provision a strict DAG, gracefully handle asynchronous API failures, and mathematically execute clean aborts to minimize the financial burn rate.

---

## 🛡️ Anti-Reward Hacking Design

As highlighted in RL safety research, agents often "game" the verifier (e.g., deleting a test timer to maximize a score). **The Cloud Saga Orchestrator structurally prevents reward hacking.** * The environment's dependency matrix (`DEPENDS_ON` and `REQUIRED_FOR`) is immutable on the server side. 
* The agent cannot spoof a successful teardown or fake a `200 OK` status; it must execute the topologically correct sequence of API calls.
* The dense reward signal is tied directly to the `hourly_burn_rate`. The only way to stop bleeding points is to successfully complete the architecture or execute a flawless "Clean Abort" to bring the burn rate back to $0.00.

---

## 🧠 Action & Observation Spaces

### Action Space (Agent -> Environment)
The agent interacts with a strict JSON Pydantic schema representing internal API commands.
* `command` (str): `create`, `delete`, or `check_status`.
* `resource_type` (str): `vpc`, `ip`, `disk`, `gpu_vm`, `dns`.
* `resource_id` (str, optional): The target ID for deletion or status checks.

### Observation Space (Environment -> Agent)
The environment returns a comprehensive state tensor mocking a real cloud console.
* `message` (str): API response context (e.g., "403 Insufficient Quota", "201 Created").
* `last_status_code` (int): HTTP status of the immediate prior action.
* `active_resources` (dict): The live, tracked state of the infrastructure graph.
* `hourly_burn_rate` (float): The current financial cost of active resources. Used for dense negative reward shaping.

---

## 🎯 Task Difficulties & Grading

The environment evaluates the agent's ability to maintain a clean state under increasing system duress. The deterministic Grader outputs `0.0` to `1.0` based on terminal ledger states.

1. **Easy Task (The Happy Path):** * **Scenario:** 100% API uptime. 
   * **Goal:** Agent provisions `vpc -> ip -> disk -> gpu_vm -> dns` in perfect topological order.
2. **Medium Task (The Hard Failure & Pivot):**
   * **Scenario:** Infrastructure builds successfully until the `gpu_vm` throws a `403 Quota Error`. 
   * **Goal:** Agent must catch the failure, halt provisioning, and execute a reverse topological teardown (`disk -> ip -> vpc`) to achieve a "Clean Abort" state with a $0 burn rate.
3. **Hard Task (The Asynchronous Timeout):**
   * **Scenario:** The `disk` API throws a `504 Gateway Timeout`. The true state is unknown. 
   * **Goal:** Agent must not blindly create (duplicate error) or delete (404 error). It must issue `check_status`, discover the true state, and execute the exact required rollback sequence.

---

## 🚀 Setup & Usage Instructions

### Connect via Python Client (OpenEnv)
Because this Space is built on the OpenEnv spec, you can install and run it directly in your RL training loops:

```bash
pip install git+https://huggingface.co/spaces/AamirK/cloud-saga-orchestrator

from cloud_saga_orchestrator import SagaEnvironment, ProvisionAction

# Connect to the live Space
env = SagaEnvironment(base_url="[https://aamirk-cloud-saga-orchestrator.hf.space](https://aamirk-cloud-saga-orchestrator.hf.space)")
obs = env.reset(task_level="medium")

# Execute a command
action = ProvisionAction(command="create", resource_type="vpc")
result = env.step(action)
print(result.hourly_burn_rate)
Run Baseline Inference
A standard inference.py script is included in the repository root to evaluate frontier models against the environment using the mandatory [START]/[STEP]/[END] logging format. It uses the Hugging Face router, so no OpenAI billing is required.

Bash
export HF_TOKEN="hf_your_token_here"
python inference.py