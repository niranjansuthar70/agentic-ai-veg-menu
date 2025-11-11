from mcp.server.fastmcp import FastMCP
from typing import Any
from decimal import Decimal, InvalidOperation

mcp = FastMCP("Demo-Server", stateless_http=True)

@mcp.tool(
    description="Calculate the total price of vegetarian dishes. Each dish must include a 'price' field."
)
def sum_veg_prices(dishes: list[dict[str, Any]]) -> dict[str, Any]:
    if not dishes:
        return {"error": "No dishes were provided."}

    total = Decimal('0')

    print("dishes: ", dishes)
    print("type of dishes: ", type(dishes))

    # for dish in dishes:
    #     name = dish.get("name", "unknown")

    #     if "price" not in dish:
    #         return {"error": f"Dish '{name}' is missing required field 'price'."}

    #     try:
    #         total += Decimal(str(dish["price"]))
    #     except (InvalidOperation, TypeError):
    #         return {"error": f"Invalid price value for dish '{name}': {dish['price']}"}

    # return {"total_price": float(total)}
    return {}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
