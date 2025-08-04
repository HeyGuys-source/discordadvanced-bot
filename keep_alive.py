import os
import asyncio
import logging
from aiohttp import web
from datetime import datetime

# Setup logger - so you can see what's going on under the hood
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('keep_alive_server')

app = web.Application()

# Health check endpoint - Render can ping this to check if app is alive
async def healthcheck(request):
    return web.json_response({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": "Bot is alive and kicking!"
    })

# Simple root handler for browser visits or checks
async def handle_root(request):
    return web.Response(text="Hello, your bot is alive and thriving!")

# Global middleware for logging all incoming requests (for monitoring)
@web.middleware
async def logging_middleware(request, handler):
    logger.info(f"Incoming request: {request.method} {request.path}")
    try:
        response = await handler(request)
        logger.info(f"Response status: {response.status}")
        return response
    except Exception as e:
        logger.error(f"Error handling request: {e}", exc_info=True)
        return web.Response(status=500, text="Internal Server Error")

app.middlewares.append(logging_middleware)

# Add routes
app.router.add_get('/', handle_root)
app.router.add_get('/healthz', healthcheck)

# Example async background task: logs uptime every 60 seconds
async def uptime_logger(app):
    start_time = datetime.utcnow()
    while True:
        uptime = datetime.utcnow() - start_time
        logger.info(f"Server uptime: {uptime}")
        await asyncio.sleep(60)

# Startup hook to start background tasks
async def on_startup(app):
    app['uptime_logger'] = asyncio.create_task(uptime_logger(app))
    logger.info("Keep-alive server startup complete.")

# Cleanup hook to cancel background tasks gracefully
async def on_cleanup(app):
    logger.info("Keep-alive server cleaning up...")
    app['uptime_logger'].cancel()
    try:
        await app['uptime_logger']
    except asyncio.CancelledError:
        logger.info("Background uptime logger task cancelled.")

app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

# Run the app, listening on Render's assigned port and all interfaces
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting keep-alive server on port {port}...")
    web.run_app(app, host='0.0.0.0', port=port)
