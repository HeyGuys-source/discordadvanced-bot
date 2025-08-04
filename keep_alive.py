import os
from aiohttp import web
import asyncio

async def run_server():
    async def handle(request):
        return web.Response(text="Bot is alive and kicking!")

    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Keep-alive server running on port {port}")

def keep_alive():
    loop = asyncio.get_event_loop()
    loop.create_task(run_server())
