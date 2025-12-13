"""
MCP Server with useful real-world tools
"""
import asyncio
from datetime import datetime
import json
import hashlib
import base64
from typing import Sequence
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("mcp-server")
API_KEY = "e0fd9fd39cacfe425fd60c78967d4627"


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_weather",
            description="Get current weather for any city worldwide",
            inputSchema={
                "type": "object",   
                "properties": {
                    "city": {"type": "string", "description": "City name (e.g., New York, London, Tokyo)"}
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="wikipedia_search",
            description="Search Wikipedia and get article summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="generate_qr_code",
            description="Generate QR code image URL for any text or URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Text or URL to encode in QR code"}
                },
                "required": ["data"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_weather":
            city = arguments.get("city", "")
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": API_KEY, "units": "metric"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                result = {
                    "city": data.get("name", city),
                    "country": data.get("sys", {}).get("country", "Unknown"),
                    "temperature": f"{data['main']['temp']}°C / {data['main']['temp'] * 9/5 + 32:.1f}°F",
                    "condition": data.get("weather", [{}])[0].get("description", "Unknown").title(),
                    "humidity": f"{data['main']['humidity']}%",
                    "wind_speed": f"{data.get('wind', {}).get('speed', 0) * 3.6:.1f} km/h",
                    "feels_like": f"{data['main']['feels_like']}°C",
                    "pressure": f"{data['main']['pressure']} hPa",
                    "visibility": f"{data.get('visibility', 0) / 1000:.1f} km" if data.get('visibility') else "N/A",
                    "timestamp": datetime.now().isoformat()
                }
        
        elif name == "wikipedia_search":
            query = arguments.get("query", "")
            headers = {"User-Agent": "MCP-Server/1.0 (contact@example.com)"}
            async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
                try:
                    # First, search for the page
                    search_url = "https://en.wikipedia.org/w/api.php"
                    search_params = {
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "format": "json",
                        "srlimit": 1
                    }
                    search_response = await client.get(search_url, params=search_params)
                    search_data = search_response.json()
                    
                    # Get the page title from search results
                    if search_data.get("query", {}).get("search"):
                        page_title = search_data["query"]["search"][0]["title"]
                    else:
                        # Try direct page title
                        page_title = query.replace(" ", "_")
                    
                    # Now get the summary
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
                    response = await client.get(summary_url)
                    response.raise_for_status()
                    data = response.json()
                    result = {
                        "title": data.get("title", query),
                        "extract": data.get("extract", "No summary available"),
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "thumbnail": data.get("thumbnail", {}).get("source", "") if data.get("thumbnail") else "",
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    result = {
                        "error": f"Failed to get Wikipedia info: {str(e)}",
                        "suggestion": f"Try searching for '{query}' directly on Wikipedia"
                    }
        
        elif name == "generate_qr_code":
            data_text = arguments.get("data", "")
            # Use QR code API (free, no key needed)
            encoded = base64.b64encode(data_text.encode()).decode()
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={data_text}"
            result = {
                "data": data_text,
                "qr_code_url": qr_url,
                "instructions": "Open the URL in a browser to view/download the QR code",
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            result = {"error": f"Unknown tool: {name}"}
    
    except Exception as e:
        result = {"error": f"Failed to execute {name}: {str(e)}"}
    
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
