# keep_alive.py

import os
from aiohttp import web

async def keep_alive():
    async def handle(request):
        return web.Response(text="Bot is alive and kicking!")

    app = web.Application()
    app.router.add_get('/', handle)

    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
