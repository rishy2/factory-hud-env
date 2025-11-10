"""Factory Environment API for LLM agents to interact with the factory simulation."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from factory_setup import factory  # your initialized instance

import logging
import sys

# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
)
log = logging.getLogger("factory_env")

# -------------------------------------------------------------------
# FastAPI app initialization
# -------------------------------------------------------------------
app = FastAPI(
    title="Factory Environment API",
    description="Environment API exposing a manufacturing DAG and actions usable by LLM agents.",
    version="1.1",
)


# -------------------------------------------------------------------
# Request schemas
# -------------------------------------------------------------------
class BuyRequest(BaseModel):
    material_name: str
    quantity: int


class CraftRequest(BaseModel):
    product_name: str
    quantity: int


class SellRequest(BaseModel):
    product_name: str
    quantity: int


# -------------------------------------------------------------------
# Basic meta routes
# -------------------------------------------------------------------
@app.get("/health")
def health():
    """Check if the environment is alive."""
    return {"status": "ok"}


# -------------------------------------------------------------------
# State / graph / context
# -------------------------------------------------------------------
@app.get("/state")
def get_state():
    """Return current balance, revenue, and inventory."""
    return factory.get_state()


@app.get("/graph")
def get_graph():
    """Return the raw DAG structure (nodes + links)."""
    return factory.get_graph()


@app.get("/describe")
def describe_factory():
    """Return a human-readable explanation of the factory dependency graph."""
    return {"description": factory.llm_describe_graph()}


@app.get("/context")
def get_llm_context():
    """Return a full LLM reasoning context (graph + state + actions)."""
    return {"context": factory.llm_get_context()}


# -------------------------------------------------------------------
# Actions
# -------------------------------------------------------------------
@app.post("/buy")
def buy(req: BuyRequest):
    """Buy a raw material if enough balance is available."""
    try:
        factory.buy(req.material_name, req.quantity)
        log.info(f"Bought {req.quantity} × {req.material_name}")
        return {
            "message": f"Bought {req.quantity} × {req.material_name}.",
            "state": factory.get_state(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/craft")
def craft(req: CraftRequest):
    """Craft a product using existing ingredients."""
    try:
        factory.craft(req.product_name, req.quantity)
        log.info(f"Crafted {req.quantity} × {req.product_name}")
        return {
            "message": f"Crafted {req.quantity} × {req.product_name}.",
            "state": factory.get_state(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/sell")
def sell(req: SellRequest):
    """Sell a crafted product to earn revenue."""
    try:
        factory.sell(req.product_name, req.quantity)
        log.info(f"Sold {req.quantity} × {req.product_name}")
        return {
            "message": f"Sold {req.quantity} × {req.product_name}.",
            "state": factory.get_state(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------------
# Reset and act
# -------------------------------------------------------------------
@app.post("/reset")
def reset():
    """Reset factory to its initial starting state."""
    global factory
    factory = factory.__class__()  # create a fresh instance
    log.info("Factory reset.")
    return {"message": "Factory reset.", "state": factory.get_state()}


@app.post("/act")
def act(action: str = "noop"):
    """
    Perform a generic environment step.
    Mostly used for HUD/MCP eval loops that expect this endpoint.
    """
    log.info(f"Received act: {action}")
    return {
        "action": action,
        "state": factory.get_state(),
        "context": factory.llm_get_context(),
    }
