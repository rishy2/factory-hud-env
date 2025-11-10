"""Tools router for Factory Environment (LLM + HUD compatible)."""

from hud.server import MCPRouter
from hud.tools.types import EvaluationResult
from server.shared import http_client

router = MCPRouter()


# -------------------------------------------------------------------
# 1️⃣ General environment introspection
# -------------------------------------------------------------------
@router.tool
async def context() -> str:
    """Get a full textual summary of the current factory graph, state, and actions."""
    resp = await http_client.get("/context")
    data = resp.json()
    return data.get("context", "No context available.")


@router.tool
async def state() -> dict:
    """Get the current structured state of the factory (balance, revenue, inventory)."""
    resp = await http_client.get("/state")
    return resp.json()


@router.tool
async def graph() -> dict:
    """Get the raw dependency graph for the factory (nodes + links)."""
    resp = await http_client.get("/graph")
    return resp.json()


# -------------------------------------------------------------------
# 2️⃣ Core environment actions
# -------------------------------------------------------------------
@router.tool
async def buy(material_name: str, quantity: int) -> str:
    """Buy raw materials using the factory balance."""
    resp = await http_client.post(
        "/buy", json={"material_name": material_name, "quantity": quantity}
    )
    if resp.status_code != 200:
        return f"❌ Failed to buy {material_name}: {resp.text}"
    data = resp.json()
    return f"✅ {data['message']}\n\nNew state:\n{data['state']}"


@router.tool
async def craft(product_name: str, quantity: int) -> str:
    """Craft a product from available inventory materials."""
    resp = await http_client.post(
        "/craft", json={"product_name": product_name, "quantity": quantity}
    )
    if resp.status_code != 200:
        return f"❌ Failed to craft {product_name}: {resp.text}"
    data = resp.json()
    return f"🧩 {data['message']}\n\nNew state:\n{data['state']}"


@router.tool
async def sell(product_name: str, quantity: int) -> str:
    """Sell a crafted product to earn revenue."""
    resp = await http_client.post(
        "/sell", json={"product_name": product_name, "quantity": quantity}
    )
    if resp.status_code != 200:
        return f"❌ Failed to sell {product_name}: {resp.text}"
    data = resp.json()
    return f"💰 {data['message']}\n\nNew state:\n{data['state']}"


@router.tool
async def reset() -> str:
    """Reset the factory environment to its initial state."""
    resp = await http_client.post("/reset")
    if resp.status_code != 200:
        return f"❌ Failed to reset factory: {resp.text}"
    data = resp.json()
    return f"🔄 {data['message']}\n\nNew state:\n{data['state']}"


# -------------------------------------------------------------------
# 3️⃣ Evaluation for agents
# -------------------------------------------------------------------
@router.tool
async def evaluate(target_revenue: float = 500.0) -> EvaluationResult:
    """Evaluate how close the factory is to the target revenue."""
    resp = await http_client.get("/state")
    state = resp.json()
    revenue = state.get("revenue", 0.0)
    balance = state.get("balance", 0.0)
    inventory = state.get("inventory", {})

    reward = min(1.0, revenue / target_revenue)
    done = revenue >= target_revenue

    content = (
        f"💵 Revenue: ${revenue}\n"
        f"🏦 Balance: ${balance}\n"
        f"📦 Inventory: {inventory}\n"
        f"🎯 Target: ${target_revenue}"
    )

    return EvaluationResult(reward=reward, done=done, content=content)
