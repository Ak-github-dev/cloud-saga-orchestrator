from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from openenv.core.env_server import Action, Observation, State

class ProvisionAction(Action):
    command: str = Field(..., description="Must be 'create', 'delete', or 'check_status'")
    resource_type: str = Field(..., description="e.g., 'vpc', 'ip', 'disk', 'gpu_vm', 'dns'")
    resource_id: Optional[str] = Field(None, description="Required for delete and check_status commands")

class ProvisionObservation(Observation):
    message: str = Field(..., description="API Response")
    last_status_code: int = Field(..., description="HTTP status code")
    active_resources: Dict[str, str] = Field(..., description="Dictionary of running resources")
    hourly_burn_rate: float = Field(..., description="Current cost per hour")
    
class ProvisionState(State):
    step_count: int = 0
    max_steps: int = 20
    target_architecture: List[str] = ["vpc", "ip", "disk", "gpu_vm", "dns"]
    provisioned_graph: Dict[str, str] = {} 
    total_wasted_money: float = 0.0
    task_difficulty: str = "easy"