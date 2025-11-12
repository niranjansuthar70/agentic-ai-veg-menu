from mcp.server.fastmcp import FastMCP
from typing import Any
from decimal import Decimal, InvalidOperation
from utils.logger_setup import get_logger

logger = get_logger(__name__)

mcp = FastMCP("Demo-Server", stateless_http=True)

@mcp.tool(
    description="Classifya veg dishes and calculate the total price of vegetarian dishes. Each dish must include a 'price' field."
)
def classify_sum_veg_prices(dishes: list[dict[str, Any]]) -> dict[str, Any]:
    
    total = Decimal('0')
    
    if not dishes:
        return {}

    #--log input inside MCP tool
    logger.debug(f'dishes inside MCP : {dishes} and type : {type(dishes)}')

    #--STEP 1 -> perform classification
    




    # for dish in dishes:
    #     name = dish.get("name", "unknown")

    #     if "price" not in dish:
    #         return {"error": f"Dish '{name}' is missing required field 'price'."}

    #     try:
    #         total += Decimal(str(dish["price"]))
    #     except (InvalidOperation, TypeError):
    #         return {"error": f"Invalid price value for dish '{name}': {dish['price']}"}

    return {"total_price": float(total)}


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )
