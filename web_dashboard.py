from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import requests
import os
import logging

def create_app(bot):
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
    CORS(app)
    
    # Discord OAuth2 settings
    DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
    DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/callback')
    
    @app.route('/')
    def index():
        """Dashboard home page"""
        return render_template('dashboard.html', bot=bot)
    
    @app.route('/login')
    def login():
        """Login page"""
        if not DISCORD_CLIENT_ID:
            return "Discord OAuth2 not configured", 500
        
        discord_login_url = (
            f"https://discord.com/oauth2/authorize"
            f"?client_id={DISCORD_CLIENT_ID}"
            f"&redirect_uri={DISCORD_REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=identify%20guilds"
        )
        return redirect(discord_login_url)
    
    @app.route('/callback')
    def callback():
        """OAuth2 callback"""
        code = request.args.get('code')
        if not code:
            return "No code provided", 400
        
        # Exchange code for token
        data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            token_response = requests.post(
                'https://discord.com/api/oauth2/token',
                data=data,
                headers=headers
            )
            token_data = token_response.json()
            
            if 'access_token' not in token_data:
                return "Failed to get access token", 400
            
            # Get user info
            user_headers = {'Authorization': f"Bearer {token_data['access_token']}"}
            user_response = requests.get(
                'https://discord.com/api/users/@me',
                headers=user_headers
            )
            user_data = user_response.json()
            
            # Get user guilds
            guilds_response = requests.get(
                'https://discord.com/api/users/@me/guilds',
                headers=user_headers
            )
            guilds_data = guilds_response.json()
            
            # Store in session
            session['user'] = user_data
            session['guilds'] = guilds_data
            session['access_token'] = token_data['access_token']
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logging.error(f"OAuth callback error: {e}")
            return "Authentication failed", 500
    
    @app.route('/dashboard')
    def dashboard():
        """Main dashboard"""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user = session['user']
        guilds = session.get('guilds', [])
        
        # Filter guilds where user has manage_guild permission and bot is present
        manageable_guilds = []
        for guild in guilds:
            permissions = int(guild.get('permissions', 0))
            has_manage_guild = permissions & 0x20 != 0  # MANAGE_GUILD permission
            
            if has_manage_guild:
                # Check if bot is in guild
                bot_guild = bot.get_guild(int(guild['id']))
                if bot_guild:
                    guild['bot_present'] = True
                    manageable_guilds.append(guild)
                else:
                    guild['bot_present'] = False
                    manageable_guilds.append(guild)
        
        return render_template('dashboard.html', 
                             user=user, 
                             guilds=manageable_guilds,
                             bot=bot)
    
    @app.route('/guild/<int:guild_id>')
    def guild_config(guild_id):
        """Guild configuration page"""
        if 'user' not in session:
            return redirect(url_for('login'))
        
        # Verify user has access to this guild
        guilds = session.get('guilds', [])
        guild_access = False
        guild_info = None
        
        for guild in guilds:
            if int(guild['id']) == guild_id:
                permissions = int(guild.get('permissions', 0))
                has_manage_guild = permissions & 0x20 != 0
                if has_manage_guild:
                    guild_access = True
                    guild_info = guild
                break
        
        if not guild_access:
            return "Access denied", 403
        
        # Get bot guild
        bot_guild = bot.get_guild(guild_id)
        if not bot_guild:
            return "Bot not in guild", 404
        
        return render_template('guild_config.html', 
                             guild=guild_info, 
                             bot_guild=bot_guild,
                             bot=bot)
    
    @app.route('/api/guild/<int:guild_id>/settings', methods=['GET', 'POST'])
    async def guild_settings_api(guild_id):
        """API endpoint for guild settings"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Verify access
        guilds = session.get('guilds', [])
        has_access = any(
            int(g['id']) == guild_id and (int(g.get('permissions', 0)) & 0x20 != 0)
            for g in guilds
        )
        
        if not has_access:
            return jsonify({'error': 'Access denied'}), 403
        
        if request.method == 'GET':
            # Get current settings
            settings = await bot.db.get_guild_settings(guild_id)
            return jsonify(settings or {})
        
        elif request.method == 'POST':
            # Update settings
            data = request.json
            
            for key, value in data.items():
                if key in ['prefix', 'log_channel_id', 'welcome_channel_id', 
                          'welcome_message', 'farewell_message', 'auto_role_id',
                          'starboard_channel_id', 'starboard_threshold', 'automod_enabled']:
                    await bot.db.update_guild_setting(guild_id, key, value)
            
            return jsonify({'success': True})
    
    @app.route('/api/guild/<int:guild_id>/stats')
    async def guild_stats_api(guild_id):
        """API endpoint for guild statistics"""
        if 'user' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get basic stats
        bot_guild = bot.get_guild(guild_id)
        if not bot_guild:
            return jsonify({'error': 'Guild not found'}), 404
        
        stats = {
            'member_count': bot_guild.member_count,
            'channel_count': len(bot_guild.channels),
            'role_count': len(bot_guild.roles),
            'bot_count': sum(1 for member in bot_guild.members if member.bot)
        }
        
        return jsonify(stats)
    
    @app.route('/logout')
    def logout():
        """Logout user"""
        session.clear()
        return redirect(url_for('index'))
    
    return app
