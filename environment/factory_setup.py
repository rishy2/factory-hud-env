from abc import ABC
from typing import Dict


class Item(ABC):
    """Base class for all materials and products."""

    def __init__(self, name: str, cost: float = 0.0, sell_price: float = 0.0):
        self.name = name
        self.cost = cost
        self.sell_price = sell_price

    def __repr__(self):
        return f"{self.name}"


class RawMaterial(Item):
    """Basic purchasable input item."""

    pass


class Product(Item):
    """Product created via a recipe."""

    def __init__(self, name: str, recipe: Dict[str, int], sell_price: float = 0.0):
        super().__init__(name, sell_price=sell_price)
        self.recipe = recipe


# -----------------------------------------------------------
class Factory:
    def __init__(self, starting_balance: float = 2_000):
        self.balance = starting_balance
        self.revenue = 0.0
        self.inventory: Dict[str, int] = {}
        self.products: Dict[str, Product] = {}
        self.raw_materials: Dict[str, RawMaterial] = {}

    # Registration
    def register_raw_material(self, material: RawMaterial):
        self.raw_materials[material.name] = material
        self.inventory[material.name] = 0

    def register_product(self, product: Product):
        self.products[product.name] = product
        self.inventory[product.name] = 0

    # Core operations
    def buy(self, material_name: str, quantity: int):
        mat = self.raw_materials[material_name]
        cost = quantity * mat.cost
        if cost > self.balance:
            raise ValueError("Not enough balance to buy materials.")
        self.balance -= cost
        self.inventory[material_name] += quantity

    def craft(self, product_name: str, quantity: int):
        product = self.products[product_name]
        for req, amt in product.recipe.items():
            if self.inventory.get(req, 0) < amt * quantity:
                raise ValueError(f"Not enough {req} to craft {product_name}")
        for req, amt in product.recipe.items():
            self.inventory[req] -= amt * quantity
        self.inventory[product_name] += quantity

    def sell(self, product_name: str, quantity: int):
        if product_name not in self.products:
            raise ValueError(f"{product_name} is not a sellable product.")
        if self.inventory.get(product_name, 0) < quantity:
            raise ValueError(f"Not enough {product_name} to sell.")

        product = self.products[product_name]
        revenue = quantity * product.sell_price

        self.revenue += revenue

        self.inventory[product_name] -= quantity

    def get_state(self):
        return {
            "balance": self.balance,
            "inventory": self.inventory,
            "revenue": self.revenue,
        }

    def get_graph(self):
        nodes = []
        links = []

        for name, mat in self.raw_materials.items():
            nodes.append(
                {
                    "id": name,
                    "type": "raw",
                    "can_buy": True,
                    "can_craft": False,
                    "can_sell": False,
                    "cost": mat.cost,
                    "sell_price": mat.sell_price,
                    "recipe": None,
                }
            )

        for name, prod in self.products.items():
            nodes.append(
                {
                    "id": name,
                    "type": "product",
                    "can_buy": False,
                    "can_craft": True,
                    "can_sell": prod.sell_price > 0,
                    "cost": 0.0,
                    "sell_price": prod.sell_price,
                    "recipe": prod.recipe,
                }
            )
            for src in prod.recipe.keys():
                links.append({"source": src, "target": name})

        return {"nodes": nodes, "links": links}

    # --------------------------------------------------------------------
    # LLM-oriented helper methods
    # --------------------------------------------------------------------
    def llm_describe_graph(self) -> str:
        """Return a human-readable explanation of the factory dependency graph."""
        graph = self.get_graph()
        raw_nodes = [n for n in graph["nodes"] if n["type"] == "raw"]
        product_nodes = [n for n in graph["nodes"] if n["type"] == "product"]

        lines = ["FACTORY DEPENDENCY OVERVIEW", "==============================", ""]

        # Raw materials
        lines.append("🪨 Raw Materials (can be bought):")
        for r in raw_nodes:
            lines.append(f"  - {r['id']} (cost ${r['cost']})")
        lines.append("")

        # Products by dependency level
        lines.append("🏭 Products (crafted from other materials):")
        for p in product_nodes:
            recipe = ", ".join(f"{k} ×{v}" for k, v in p["recipe"].items())
            sell = f" — sells for ${p['sell_price']}" if p["sell_price"] > 0 else ""
            lines.append(f"  - {p['id']} crafted from {recipe}{sell}")
        lines.append("")

        # Top-level outputs
        sellables = [p["id"] for p in product_nodes if p["sell_price"] > 0]
        lines.append("💰 Final sellable products:")
        lines.append(f"  {', '.join(sellables)}")

        return "\n".join(lines)

    def llm_describe_state(self) -> str:
        """Return a textual description of the current factory state."""
        state = self.get_state()
        lines = ["FACTORY STATE", "==============", ""]
        lines.append(f"💵 Balance: ${state['balance']}")
        lines.append(f"📈 Revenue: ${state['revenue']}")
        lines.append("")
        lines.append("📦 Inventory:")
        for k, v in state["inventory"].items():
            if v > 0:
                lines.append(f"  - {k}: {v}")
        if not any(v > 0 for v in state["inventory"].values()):
            lines.append("  (empty)")
        return "\n".join(lines)

    def llm_get_actions(self) -> str:
        """Explain what actions the LLM can take in natural language."""
        return (
            "Available Actions:\n"
            "------------------\n"
            "1️⃣  **buy(material_name, quantity)** – Purchase raw materials using available balance.\n"
            "     Example: buy('Fiber', 5)\n"
            "2️⃣  **craft(product_name, quantity)** – Combine materials to produce a product.\n"
            "     Example: craft('Reinforced Fabric', 2)\n"
            "3️⃣  **sell(product_name, quantity)** – Sell finished products for revenue.\n"
            "     Example: sell('Spacesuit', 1)\n"
            "\n"
            "Remember: you can only buy raw materials, only craft if ingredients exist, "
            "and only sell if the product has a sell_price."
        )

    def llm_get_context(self) -> str:
        """Combine graph, state, and actions into one prompt-style context."""
        return "\n\n".join(
            [
                self.llm_describe_graph(),
                self.llm_describe_state(),
                self.llm_get_actions(),
            ]
        )


# -----------------------------------------------------------
# Initialize factory and register everything once
factory = Factory()

# Raw materials
factory.register_raw_material(RawMaterial("Fiber", cost=2.0))
factory.register_raw_material(RawMaterial("Metal", cost=0.5))
factory.register_raw_material(RawMaterial("Chemicals", cost=0.25))
factory.register_raw_material(RawMaterial("Polymers", cost=0.25))
factory.register_raw_material(RawMaterial("Minerals", cost=0.5))

# Base & composite products
factory.register_product(Product("Reinforced Fabric", {"Fiber": 2, "Metal": 1}))
factory.register_product(Product("Spacesuit", {"Reinforced Fabric": 4}, sell_price=30))
factory.register_product(Product("Resins", {"Chemicals": 3, "Polymers": 1}))
factory.register_product(Product("Antenna", {"Metal": 3, "Resins": 2}))
factory.register_product(Product("Heat Shield", {"Resins": 1, "Polymers": 2}))
factory.register_product(Product("Insulation Panels", {"Resins": 2, "Polymers": 3}))
factory.register_product(
    Product("Map System", {"Antenna": 3, "Heat Shield": 1}, sell_price=140)
)
factory.register_product(
    Product("Calling System", {"Antenna": 2, "Insulation Panels": 2}, sell_price=150)
)
factory.register_product(Product("Wires", {"Polymers": 3}))
factory.register_product(Product("Plastic Shells", {"Polymers": 1, "Minerals": 3}))
factory.register_product(Product("Batteries", {"Wires": 2, "Plastic Shells": 1}))
factory.register_product(Product("Power Cores", {"Batteries": 4}))
factory.register_product(Product("Catalyst", {"Minerals": 3}))
factory.register_product(Product("Air Purifier", {"Plastic Shells": 1, "Catalyst": 3}))
factory.register_product(Product("Life Jacket", {"Air Purifier": 2}, sell_price=165))
factory.register_product(
    Product("Escape Pods", {"Heat Shield": 3, "Power Cores": 1}, sell_price=130)
)
factory.register_product(
    Product("Survey Probes", {"Insulation Panels": 2, "Power Cores": 2}, sell_price=120)
)
