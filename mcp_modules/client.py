# client.py
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import json

#--read filtered_result.json
with open('filtered_result.json', 'r') as file:
    filtered_result = json.load(file)

print("filtered_result: ", filtered_result)
print("type of filtered_result: ", type(filtered_result))

async def main():
    url = "http://127.0.0.1:8000/mcp"
    async with streamablehttp_client(url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()            # JSON-RPC „initialize“
            result = await session.call_tool("sum_veg_prices", {"dishes": filtered_result})
            #--extract text
            print("Ergebnis vom Server:", result, "type: ", type(result))

            text = result.content[0].text
            print("Text:", text)

if __name__ == "__main__":
    asyncio.run(main())