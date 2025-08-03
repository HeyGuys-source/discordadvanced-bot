import re
import discord
from datetime import datetime, timedelta
from typing import Optional, Union

def parse_time(time_str: str) -> Optional[timedelta]:
    """Parse time string into timedelta object"""
    if not time_str:
        return None
    
    # Time units and their multipliers in seconds
    time_units = {
        's': 1,
        'sec': 1, 'second': 1, 'seconds': 1,
        'm': 60,
        'min': 60, 'minute': 60, 'minutes': 60,
        'h': 3600,
        'hr': 3600, 'hour': 3600, 'hours': 3600,
        'd': 86400,
        'day': 86400, 'days': 86400,
        'w': 604800,
        'week': 604800, 'weeks': 604800,
        'mo': 2592000,
        'month': 2592000, 'months': 2592000,
        'y': 31536000,
        'year': 31536000, 'years': 31536000
    }
    
    # Pattern to match time components
    pattern = r'(\d+)\s*([a-zA-Z]+)'
    matches = re.findall(pattern, time_str.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    
    for amount, unit in matches:
        try:
            amount = int(amount)
        except ValueError:
            continue
        
        if unit in time_units:
            total_seconds += amount * time_units[unit]
        else:
            # Try partial matching
            matching_units = [u for u in time_units.keys() if u.startswith(unit)]
            if matching_units:
                total_seconds += amount * time_units[matching_units[0]]
    
    if total_seconds == 0:
        return None
    
    return timedelta(seconds=total_seconds)

def format_time(td: timedelta) -> str:
    """Format timedelta into human-readable string"""
    total_seconds = int(td.total_seconds())
    
    if total_seconds == 0:
        return "0 seconds"
    
    units = [
        (31536000, 'year', 'years'),
        (2592000, 'month', 'months'),
        (604800, 'week', 'weeks'),
        (86400, 'day', 'days'),
        (3600, 'hour', 'hours'),
        (60, 'minute', 'minutes'),
        (1, 'second', 'seconds')
    ]
    
    parts = []
    
    for unit_seconds, singular, plural in units:
        if total_seconds >= unit_seconds:
            amount = total_seconds // unit_seconds
            unit_name = singular if amount == 1 else plural
            parts.append(f"{amount} {unit_name}")
            total_seconds %= unit_seconds
            
            # Only show the two largest units
            if len(parts) >= 2:
                break
    
    return ', '.join(parts)

def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def create_embed(title: str = None, description: str = None, color: int = 0x5865F2, **kwargs) -> discord.Embed:
    """Create a Discord embed with default settings"""
    embed = discord.Embed(title=title, description=description, color=color)
    
    # Add timestamp
    if kwargs.get('timestamp', True):
        embed.timestamp = datetime.utcnow()
    
    # Add footer
    if 'footer' in kwargs:
        embed.set_footer(text=kwargs['footer'])
    
    # Add author
    if 'author' in kwargs:
        author = kwargs['author']
        if isinstance(author, dict):
            embed.set_author(**author)
        else:
            embed.set_author(name=str(author))
    
    # Add thumbnail
    if 'thumbnail' in kwargs:
        embed.set_thumbnail(url=kwargs['thumbnail'])
    
    # Add image
    if 'image' in kwargs:
        embed.set_image(url=kwargs['image'])
    
    # Add fields
    if 'fields' in kwargs:
        for field in kwargs['fields']:
            embed.add_field(**field)
    
    return embed

def create_success_embed(title: str, description: str = None) -> discord.Embed:
    """Create a success embed"""
    return create_embed(
        title=f"✅ {title}",
        description=description,
        color=0x57F287
    )

def create_error_embed(title: str, description: str = None) -> discord.Embed:
    """Create an error embed"""
    return create_embed(
        title=f"❌ {title}",
        description=description,
        color=0xED4245
    )

def create_warning_embed(title: str, description: str = None) -> discord.Embed:
    """Create a warning embed"""
    return create_embed(
        title=f"⚠️ {title}",
        description=description,
        color=0xFEE75C
    )

def create_info_embed(title: str, description: str = None) -> discord.Embed:
    """Create an info embed"""
    return create_embed(
        title=f"ℹ️ {title}",
        description=description,
        color=0x5865F2
    )

def format_permissions(permissions: discord.Permissions) -> str:
    """Format permissions into a readable string"""
    perms = []
    
    perm_names = {
        'administrator': 'Administrator',
        'manage_guild': 'Manage Server',
        'manage_roles': 'Manage Roles',
        'manage_channels': 'Manage Channels',
        'manage_messages': 'Manage Messages',
        'manage_webhooks': 'Manage Webhooks',
        'manage_nicknames': 'Manage Nicknames',
        'manage_emojis': 'Manage Emojis',
        'kick_members': 'Kick Members',
        'ban_members': 'Ban Members',
        'create_instant_invite': 'Create Invite',
        'view_audit_log': 'View Audit Log',
        'priority_speaker': 'Priority Speaker',
        'stream': 'Video',
        'read_messages': 'Read Messages',
        'send_messages': 'Send Messages',
        'send_tts_messages': 'Send TTS Messages',
        'embed_links': 'Embed Links',
        'attach_files': 'Attach Files',
        'read_message_history': 'Read Message History',
        'mention_everyone': 'Mention Everyone',
        'external_emojis': 'Use External Emojis',
        'add_reactions': 'Add Reactions',
        'connect': 'Connect',
        'speak': 'Speak',
        'mute_members': 'Mute Members',
        'deafen_members': 'Deafen Members',
        'move_members': 'Move Members',
        'use_voice_activation': 'Use Voice Activity'
    }
    
    for perm, value in permissions:
        if value and perm in perm_names:
            perms.append(perm_names[perm])
    
    return ', '.join(perms) if perms else 'No permissions'

def get_member_status(member: discord.Member) -> str:
    """Get member status as string"""
    status_map = {
        discord.Status.online: '🟢 Online',
        discord.Status.idle: '🟡 Idle',
        discord.Status.dnd: '🔴 Do Not Disturb',
        discord.Status.offline: '⚫ Offline'
    }
    return status_map.get(member.status, '⚫ Offline')

def truncate_string(text: str, max_length: int = 2000, suffix: str = "...") -> str:
    """Truncate string if it exceeds max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def clean_code_block(text: str) -> str:
    """Remove code block formatting from text"""
    if text.startswith('```') and text.endswith('```'):
        # Remove language identifier if present
        lines = text[3:-3].split('\n')
        if lines and not lines[0].strip():
            lines = lines[1:]
        elif lines and lines[0].strip() and ' ' not in lines[0].strip():
            lines = lines[1:]  # Remove language identifier
        return '\n'.join(lines)
    return text

def escape_markdown(text: str) -> str:
    """Escape Discord markdown characters"""
    markdown_chars = ['*', '_', '`', '~', '|', '\\']
    for char in markdown_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_user_info(user: Union[discord.User, discord.Member]) -> dict:
    """Format user information into a dictionary"""
    info = {
        'id': user.id,
        'name': user.name,
        'display_name': user.display_name,
        'discriminator': user.discriminator,
        'avatar_url': str(user.display_avatar.url),
        'created_at': user.created_at.isoformat(),
        'is_bot': user.bot
    }
    
    if isinstance(user, discord.Member):
        info.update({
            'joined_at': user.joined_at.isoformat() if user.joined_at else None,
            'premium_since': user.premium_since.isoformat() if user.premium_since else None,
            'status': str(user.status),
            'top_role': user.top_role.name,
            'roles': [role.name for role in user.roles if role.name != '@everyone'],
            'permissions': format_permissions(user.guild_permissions)
        })
    
    return info

def format_guild_info(guild: discord.Guild) -> dict:
    """Format guild information into a dictionary"""
    return {
        'id': guild.id,
        'name': guild.name,
        'description': guild.description,
        'owner_id': guild.owner_id,
        'member_count': guild.member_count,
        'created_at': guild.created_at.isoformat(),
        'verification_level': str(guild.verification_level),
        'explicit_content_filter': str(guild.explicit_content_filter),
        'mfa_level': guild.mfa_level,
        'premium_tier': guild.premium_tier,
        'premium_subscription_count': guild.premium_subscription_count,
        'preferred_locale': str(guild.preferred_locale),
        'icon_url': str(guild.icon.url) if guild.icon else None,
        'banner_url': str(guild.banner.url) if guild.banner else None,
        'features': guild.features
    }

def create_paginated_embed(items: list, title: str, items_per_page: int = 10, 
                          page: int = 1, formatter=None) -> discord.Embed:
    """Create a paginated embed from a list of items"""
    total_pages = (len(items) - 1) // items_per_page + 1
    page = max(1, min(page, total_pages))
    
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    page_items = items[start_index:end_index]
    
    embed = discord.Embed(
        title=title,
        color=0x5865F2
    )
    
    if formatter:
        content = formatter(page_items)
    else:
        content = '\n'.join(str(item) for item in page_items)
    
    embed.description = content
    embed.set_footer(text=f"Page {page}/{total_pages} • {len(items)} total items")
    
    return embed

def is_valid_hex_color(color_str: str) -> bool:
    """Check if string is a valid hex color"""
    if color_str.startswith('#'):
        color_str = color_str[1:]
    
    if len(color_str) != 6:
        return False
    
    try:
        int(color_str, 16)
        return True
    except ValueError:
        return False

def hex_to_int(color_str: str) -> int:
    """Convert hex color string to integer"""
    if color_str.startswith('#'):
        color_str = color_str[1:]
    return int(color_str, 16)

def ordinal(n: int) -> str:
    """Convert number to ordinal string (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"
