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

**A high-fidelity Reinforcement Learning environment tackling a $44.5B enterprise problem: Cloud "Zombie Resources" and Distributed State Failures.**

---

## 📖 The Origin Story & The Real-World Problem

During my years managing heavy enterprise ERP infrastructure like SAP Basis, I repeatedly ran into the same operational nightmare: asynchronous cloud provisioning failures. 

When enterprises deploy architecture (VPCs, IPs, Disks, VMs), they rely on strict Directed Acyclic Graphs (DAGs). If a deployment fails halfway through—say, a sudden GPU quota error or a gateway timeout—standard deterministic scripts simply crash. They leave the successfully provisioned resources spinning endlessly in the void. These are known as **"Zombie Resources."**

This isn't a theoretical issue. According to recent industry research (like the *FinOps in Focus* report), an estimated **$44.5 Billion** in enterprise cloud spend is wasted annually, with orphaned and idle resources being a primary culprit. 

Resolving these partial failures requires the **Saga Pattern**—a complex distributed systems concept where an agent must catch the failure and traverse the dependency graph *backward* to safely tear down the infrastructure. Standard LLMs fail at this. They lack temporal reasoning, panic during timeouts, or execute teardowns out of order (causing 409 dependency lock-ups).

I built the **Cloud Saga Orchestrator** to train RL Agents to act as Resilient DevOps Orchestrators. The agent must provision a strict DAG, gracefully handle injected API failures, and mathematically execute "Clean Aborts" to bring the financial burn rate back to $0.00.

---

## 🛡️ Anti-Reward Hacking Design

As highlighted in RL safety research, agents often "game" the verifier. **This environment structurally prevents reward hacking:**
* The environment's dependency matrix (`DEPENDS_ON` and `REQUIRED_FOR`) is immutable on the server side. 
* The agent cannot spoof a successful teardown or fake a `200 OK` status; it must execute the topologically correct sequence of API calls.
* The dense reward signal is tied directly to the `hourly_burn_rate`. The only way to stop bleeding points is to successfully complete the architecture or execute a flawless rollback.

---

## 👨‍💻 Manual Testing Guide (For the Judges)

Want to see the engine in action? Head over to the **App** tab -> `/docs` and try to beat the environment yourself.

**1. The Dependency Trap:**
* Go to `POST /step`. Try to create the `gpu_vm` first. 
* *Result:* The engine mathematically blocks you with a `400 Bad Request: Missing dependencies ['ip', 'disk']`.

**2. The FinOps Burn Rate:**
* Go to `POST /step` and create the `vpc`.
* *Result:* `201 Created`. Notice your `hourly_burn_rate` goes up to `0.1`. You are now bleeding virtual money every step until you finish or clean up.

**3. The Medium Task (Simulated Outage & Pivot):**
* Create the `ip`, then the `disk`. Now try to create the `gpu_vm`.
* *Result:* **BAM.** You hit a `403 Insufficient Quota: Out of GPUs`. 
* *The Test:* You must now delete the `disk`, `ip`, and `vpc` in exact reverse order to achieve a `WIN: Clean Abort detected` and save the company's budget.

---

## 🧠 Action & Observation Spaces

### Action Space (Agent -> Environment)
The agent interacts with a strict JSON Pydantic schema representing internal API commands.
* `command` (str): `create`, `delete`, or `check_status`.
* `resource_type` (str): `vpc`, `ip`, `disk`, `gpu_vm`, `dns`.

### Observation Space (Environment -> Agent)
The environment returns a comprehensive state tensor mocking a real cloud console.
* `message` (str): API response context (e.g., "403 Insufficient Quota").
* `last_status_code` (int): HTTP status of the immediate prior action.
* `active_resources` (dict): The live, tracked state of the infrastructure graph.
* `hourly_burn_rate` (float): The financial cost of active resources (used for dense negative reward shaping).

---

## 🚀 Setup & Automated Evaluation

### Run Baseline Inference
The `inference.py` script is fully configured to evaluate frontier models against all three task difficulties using the mandatory `[START]/[STEP]/[END]` logging format. It utilizes the Hugging Face router.

```bash
export HF_TOKEN="your_hf_token_here"
python inference.py

Connect via Python Client (OpenEnv)
Install and run it directly in your RL training loops:

Bash
pip install git+[https://huggingface.co/spaces/AamirK/cloud-saga-orchestrator](https://huggingface.co/spaces/AamirK/cloud-saga-orchestrator)
Python
from cloud_saga_orchestrator import SagaEnvironment, ProvisionAction

# Connect to the live Space
env = SagaEnvironment(base_url="[https://aamirk-cloud-saga-orchestrator.hf.space](https://aamirk-cloud-saga-orchestrator.hf.space)")
obs = env.reset(task_level="medium")

# Execute a command
action = ProvisionAction(command="create", resource_type="vpc")
result = env.step(action)
print(result.hourly_burn_rate)