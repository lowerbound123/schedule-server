from fastapi import FastAPI
from models import Statue, StandardResponse
from models.exceptions import (
    ErrorStructure,
    FaultDestination,
    FaultOrigin,
    NonExistentMachine,
    NonExistentCarrier,
    FaultCarrier,
    FullDestination
)
from utils.greedy import RandomGreddy
from schedulers.LLMscheduler import QwenLoraPredictor

metrics: dict[str, float] = {
    "success_request": 0.0,
    "failed_request": 0.0,
    "bad_structure": 0.0,
    "nonexistent_carrier": 0.0,
    "nonexistent_machine_or_shelf": 0.0,
    "full_destination": 0.0,
    "fault_origin": 0.0,
    "fault_destination": 0.0,
    "fault_carrier": 0.0,
    "predict_cost": 0.0,
}

app = FastAPI()
random_greddy = RandomGreddy(tags={})
scheduler = QwenLoraPredictor(
    base_model_path="./base_models/Qwen3-0.6B",
    adapter_path="./adapters/Qwen3-0.6B-lora-First",
)
    

@app.post("/init")
async def init(tags: dict[str, list[str]]):
    global random_greddy
    random_greddy = RandomGreddy(tags=tags)
    print(tags)
    return {"statue": "ok"}

@app.get("/update")
async def update():
    return {"Hello": "World"}

@app.post("/schedule")
async def schedule(statue: Statue) -> StandardResponse:
    output = None
    try:
        output, metric = scheduler(statue.machines, statue.shelves, statue.carriers)
        for k, v in metric.items():
            metrics[k] += v
        return output
    except ErrorStructure:
        metrics["bad_structure"] += 1
    except FaultDestination:
        metrics["fault_destination"] += 1
    except FaultOrigin:
        metrics["fault_origin"] += 1
    except NonExistentMachine:
        metrics["nonexistent_target"] += 1
    except NonExistentCarrier:
        metrics["nonexistent_carrier"] += 1
    except FaultCarrier:
        metrics["fault_carrier"] += 1
    except FullDestination:
        metrics["full_destination"] += 1
    except Exception as e:
        print(e)
    finally:
        if output is None:
            metrics["failed_request"] += 1
            output = random_greddy(statue.machines, statue.shelves, statue.carriers)
        else:
            metrics["success_request"] += 1
        return output

@app.get("/metrics")
async def get_metrics():
    return metrics