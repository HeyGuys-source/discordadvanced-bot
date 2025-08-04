import os
import asyncio
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is alive and kicking!")

async def run_server():
    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Keep-alive server running on port {port}")

    # This keeps the server running forever
    while True:
        await asyncio.sleep(3600)  # sleep an hour, then loop again

def keep_alive():
    asyncio.run(run_server())
