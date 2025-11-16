from mcp.server.fastmcp import FastMCP
from typing import Any
from decimal import Decimal, InvalidOperation
from utils.logger_setup import get_logger
from mcp_modules.classify_veg_dishes import classify_dishes

# --- LANGSMITH: Step 1: Import tracing components ---
from langsmith import Client, traceable

logger = get_logger(__name__)

# --- LANGSMITH: Step 2: Initialize Client ---
try:
    client = Client()
    logger.info("LangSmith Client initialized successfully for MCP Server.")
except Exception as e:
    logger.warning(f"Could not initialize LangSmith Client. Tracing will be disabled. Error: {e}")


mcp = FastMCP("Demo-Server", stateless_http=True)

# --- LANGSMITH: Step 3: Decorate the tool (This is the most important part) ---
@traceable(name="MCP Tool: Classify & Sum Veg Prices", run_type="tool")
@mcp.tool(
    description="Classifya veg dishes and calculate the total price of vegetarian dishes. Each dish must include a 'price' field."
)
def classify_sum_veg_prices(dishes: list[dict[str, Any]]) -> dict[str, Any]:
    
    logger.debug(f'dishes inside MCP : {dishes} and type : {type(dishes)}')
    
    total_price = float(0)
    
    if not dishes:
        return {}

    #--STEP 1 -> perform classification
    
    # --- LANGSMITH: Step 4: REMOVED the nested 'with traceable(...)' block ---
    # We just call the function directly now.
    classification_output_list=classify_dishes(dishes=dishes)
        
    logger.debug(f'classification_output_list inside MCP : {classification_output_list} and type : {type(classification_output_list)}')

    #--get sum of all prices
    if classification_output_list:
        for sample_dish_items in classification_output_list:
            # Basic type check in case price is missing or invalid
            try:
                total_price += float(sample_dish_items.get('dish_price', 0))
            except (ValueError, TypeError):
                logger.warning(f"Invalid price for dish: {sample_dish_items.get('dish_name', 'Unknown')}")
                pass

    result = {
        'dishes':classification_output_list,
        "total_price": float(total_price)
    }
    
    # This return value is automatically logged as the tool's output
    # by the @traceable decorator above.
    return result


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )