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
    
    total_price = float(0)
    
    if not dishes:
        return {}

    #--STEP 1 -> perform classification
    classification_output_list=classify_dishes(dishes=dishes)
    logger.debug(f'classification_output_list inside MCP : {classification_output_list} and type : {type(classification_output_list)}')

    #--get sum of all prices
    if classification_output_list:
        for sample_dish_items in classification_output_list:
            total_price+=sample_dish_items['dish_price']

    return {
        'dishes':classification_output_list,
        "total_price": float(total_price)
        }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )
