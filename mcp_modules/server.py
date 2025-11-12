from mcp.server.fastmcp import FastMCP
from typing import Any
from decimal import Decimal, InvalidOperation
from utils.logger_setup import get_logger
from mcp_modules.classify_veg_dishes import classify_dishes

logger = get_logger(__name__)

mcp = FastMCP("Demo-Server", stateless_http=True)

@mcp.tool(
    description="Classifya veg dishes and calculate the total price of vegetarian dishes. Each dish must include a 'price' field."
)
def classify_sum_veg_prices(dishes: list[dict[str, Any]]) -> dict[str, Any]:
    
    logger.debug(f'dishes inside MCP : {dishes} and type : {type(dishes)}')
    
    total = Decimal('0')
    
    if not dishes:
        return {}

    #--log input inside MCP tool

    #--STEP 1 -> perform classification
    classification_output_list=classify_dishes(dishes=dishes)
    logger.debug(f'classification_output_list inside MCP : {classification_output_list} and type : {type(classification_output_list)}')


    # for dish in dishes:
    #     name = dish.get("name", "unknown")

    #     if "price" not in dish:
    #         return {"error": f"Dish '{name}' is missing required field 'price'."}

    #     try:
    #         total += Decimal(str(dish["price"]))
    #     except (InvalidOperation, TypeError):
    #         return {"error": f"Invalid price value for dish '{name}': {dish['price']}"}

    return {
        'dishes':classification_output_list,
        "total_price": float(total)
        }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )
