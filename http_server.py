"""HTTP wrapper for MCP Server"""
import json
from aiohttp import web
from server import app as mcp_app

async def handle_tool_call(request):
    try:
        data = await request.json()
        tool_name = data.get('tool')
        arguments = data.get('arguments', {})
        
        result = await mcp_app.call_tool(tool_name, arguments)
        response_text = result[0].text if result else "{}"
        
        return web.json_response({
            'success': True,
            'data': json.loads(response_text)
        })
    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

async def handle_list_tools(request):
    try:
        tools = await mcp_app.list_tools()
        tools_data = [{
            'name': tool.name,
            'description': tool.description,
            'inputSchema': tool.inputSchema
        } for tool in tools]
        return web.json_response({'success': True, 'tools': tools_data})
    except Exception as e:
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def health_check(request):
    return web.json_response({'status': 'healthy'})

def create_app():
    app = web.Application()
    app.router.add_post('/call', handle_tool_call)
    app.router.add_get('/tools', handle_list_tools)
    app.router.add_get('/health', health_check)
    return app

if __name__ == '__main__':
    web.run_app(create_app(), host='0.0.0.0', port=8080)