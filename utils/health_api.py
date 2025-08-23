from flask import Flask, jsonify, request
import asyncio
import threading
import logging
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class HealthAPI:
    """Flask API for health monitoring and UptimeRobot integration."""
    
    def __init__(self, bot, port=None):
        self.bot = bot
        # Use Render's PORT environment variable or default to 8080
        self.port = port or int(os.environ.get('PORT', 8080))
        self.app = Flask(__name__)
        self.setup_routes()
        self.server_thread = None
        
    def setup_routes(self):
        """Setup Flask routes for health monitoring."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Main health check endpoint for UptimeRobot."""
            try:
                # Get health monitor cog
                health_cog = self.bot.get_cog('HealthMonitor')
                
                if not health_cog:
                    return jsonify({
                        'status': 'error',
                        'message': 'Health monitor not available',
                        'timestamp': datetime.utcnow().isoformat()
                    }), 500
                
                # Get health data
                health_data = health_cog.get_health_data()
                
                # Determine HTTP status code based on health
                status_code = 200 if health_data['status'] == 'healthy' else 503
                
                return jsonify(health_data), status_code
                
            except Exception as e:
                logger.error(f"Health check endpoint error: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/ping', methods=['GET'])
        def ping():
            """Simple ping endpoint."""
            return jsonify({
                'status': 'pong',
                'timestamp': datetime.utcnow().isoformat(),
                'bot_ready': self.bot.is_ready() if self.bot else False
            }), 200
        
        @self.app.route('/status', methods=['GET'])
        def bot_status():
            """Detailed bot status endpoint."""
            try:
                if not self.bot:
                    return jsonify({'error': 'Bot not available'}), 500
                
                health_cog = self.bot.get_cog('HealthMonitor')
                health_data = health_cog.get_health_data() if health_cog else {}
                
                status_data = {
                    'bot_ready': self.bot.is_ready(),
                    'bot_user': {
                        'id': self.bot.user.id,
                        'name': self.bot.user.name,
                        'discriminator': self.bot.user.discriminator
                    } if self.bot.user else None,
                    'guild_count': len(self.bot.guilds) if self.bot.guilds else 0,
                    'user_count': len(self.bot.users) if self.bot.users else 0,
                    'latency': round(self.bot.latency * 1000, 2) if hasattr(self.bot, 'latency') else None,
                    'health': health_data,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                return jsonify(status_data), 200
                
            except Exception as e:
                logger.error(f"Status endpoint error: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Prometheus-style metrics endpoint."""
            try:
                health_cog = self.bot.get_cog('HealthMonitor')
                
                if not health_cog:
                    return "# Health monitor not available\n", 500
                
                health_data = health_cog.get_health_data()
                metrics_data = health_data.get('metrics', {})
                
                metrics_output = []
                metrics_output.append(f"# HELP bot_uptime_seconds Bot uptime in seconds")
                metrics_output.append(f"# TYPE bot_uptime_seconds gauge")
                metrics_output.append(f"bot_uptime_seconds {metrics_data.get('uptime', 0)}")
                
                metrics_output.append(f"# HELP bot_latency_milliseconds Bot latency in milliseconds")
                metrics_output.append(f"# TYPE bot_latency_milliseconds gauge")
                metrics_output.append(f"bot_latency_milliseconds {metrics_data.get('latency', 0)}")
                
                metrics_output.append(f"# HELP bot_guild_count Number of guilds")
                metrics_output.append(f"# TYPE bot_guild_count gauge")
                metrics_output.append(f"bot_guild_count {metrics_data.get('guild_count', 0)}")
                
                metrics_output.append(f"# HELP bot_user_count Number of users")
                metrics_output.append(f"# TYPE bot_user_count gauge")
                metrics_output.append(f"bot_user_count {metrics_data.get('user_count', 0)}")
                
                metrics_output.append(f"# HELP bot_errors_total Total number of errors")
                metrics_output.append(f"# TYPE bot_errors_total counter")
                metrics_output.append(f"bot_errors_total {metrics_data.get('errors_handled', 0)}")
                
                metrics_output.append(f"# HELP bot_memory_usage_percent Memory usage percentage")
                metrics_output.append(f"# TYPE bot_memory_usage_percent gauge")
                metrics_output.append(f"bot_memory_usage_percent {metrics_data.get('memory_usage', 0)}")
                
                metrics_output.append(f"# HELP bot_health_status Bot health status (1=healthy, 0.5=degraded, 0=critical)")
                metrics_output.append(f"# TYPE bot_health_status gauge")
                
                status_value = 1 if health_data.get('status') == 'healthy' else 0.5 if health_data.get('status') == 'degraded' else 0
                metrics_output.append(f"bot_health_status {status_value}")
                
                return '\n'.join(metrics_output) + '\n', 200, {'Content-Type': 'text/plain; charset=utf-8'}
                
            except Exception as e:
                logger.error(f"Metrics endpoint error: {e}")
                return f"# Error: {str(e)}\n", 500
        
        @self.app.route('/recover', methods=['POST'])
        def trigger_recovery():
            """Endpoint to trigger manual recovery (requires authentication)."""
            try:
                # Simple authentication check using environment variable
                auth_header = request.headers.get('Authorization')
                expected_token = os.environ.get('RECOVERY_AUTH_TOKEN', 'your-secret-key-here')
                if not auth_header or auth_header != f'Bearer {expected_token}':
                    return jsonify({'error': 'Unauthorized'}), 401
                
                health_cog = self.bot.get_cog('HealthMonitor')
                
                if not health_cog:
                    return jsonify({'error': 'Health monitor not available'}), 500
                
                # Trigger recovery in a separate task
                asyncio.create_task(health_cog._attempt_recovery())
                
                return jsonify({
                    'status': 'recovery_triggered',
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Recovery endpoint error: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors."""
            return jsonify({
                'error': 'Endpoint not found',
                'available_endpoints': ['/health', '/ping', '/status', '/metrics'],
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            logger.error(f"Internal server error: {error}")
            return jsonify({
                'error': 'Internal server error',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    def start_server(self):
        """Start the Flask server in a separate thread."""
        def run_server():
            try:
                self.app.run(
                    host='0.0.0.0',
                    port=self.port,
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                logger.error(f"Health API server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"Health API server started on port {self.port}")
    
    def stop_server(self):
        """Stop the Flask server."""
        # Flask doesn't have a clean shutdown method when running in threads
        # The daemon thread will be killed when the main process exits
        logger.info("Health API server stopping...")
