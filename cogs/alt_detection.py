import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import sqlite3
from database import AltDetectionDB
from utils.analysis import BehavioralAnalyzer
from utils.patterns import PatternDetector
from config import EXCLUDED_CHANNELS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AltDetectionCog(commands.Cog):
    """Advanced alt account detection cog using behavioral analysis and pattern recognition."""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = AltDetectionDB()
        self.analyzer = BehavioralAnalyzer()
        self.pattern_detector = PatternDetector()
        self.excluded_channels = EXCLUDED_CHANNELS
        
    async def cog_load(self):
        """Initialize the cog and database."""
        await self.db.initialize()
        logger.info("Alt Detection Cog loaded successfully")
    
    @app_commands.command(name="serveraltcheck", description="Detect potential alt accounts in the server")
    @app_commands.describe(
        confidence_threshold="Minimum confidence score for reporting (0-100, default: 70)",
        detailed="Include detailed analysis in report (default: False)"
    )
    async def server_alt_check(
        self, 
        interaction: discord.Interaction, 
        confidence_threshold: int = 70,
        detailed: bool = False
    ):
        """
        Advanced alt account detection command.
        Analyzes all server members for potential alt accounts using behavioral patterns.
        """
        # Check if command is used in a guild
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return
        
        # Check permissions
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ You need 'Manage Server' permissions to use this command.",
                ephemeral=True
            )
            return
        
        # Check if in excluded channels
        if interaction.channel and interaction.channel.id in self.excluded_channels:
            await interaction.response.send_message(
                "❌ This command cannot be used in this channel.",
                ephemeral=True
            )
            return
        
        # Validate confidence threshold
        if not 0 <= confidence_threshold <= 100:
            await interaction.response.send_message(
                "❌ Confidence threshold must be between 0 and 100.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            if not guild:
                await interaction.followup.send(
                    "❌ This command can only be used in a server.",
                    ephemeral=True
                )
                return
                
            logger.info(f"Starting alt detection scan for guild: {guild.name} (ID: {guild.id})")
            
            # Fetch all members with extended information
            await interaction.followup.send("🔍 **Phase 1:** Fetching member data...", ephemeral=True)
            members = await self._fetch_member_data(guild)
            
            if len(members) < 2:
                await interaction.followup.send(
                    "❌ Not enough members to perform analysis.",
                    ephemeral=True
                )
                return
            
            # Store member data for analysis
            await interaction.followup.send("💾 **Phase 2:** Storing member data for analysis...", ephemeral=True)
            await self.db.store_member_batch(guild.id, members)
            
            # Perform comprehensive analysis
            await interaction.followup.send("🧠 **Phase 3:** Analyzing patterns and behaviors...", ephemeral=True)
            analysis_results = await self._perform_comprehensive_analysis(guild.id, members)
            
            # Filter results by confidence threshold
            filtered_results = [
                result for result in analysis_results 
                if result['confidence_score'] >= confidence_threshold
            ]
            
            # Generate and send report
            await interaction.followup.send("📊 **Phase 4:** Generating detailed report...", ephemeral=True)
            
            if not filtered_results:
                embed = discord.Embed(
                    title="🔍 Alt Account Detection Report",
                    description=f"No potential alt accounts found with confidence ≥ {confidence_threshold}%",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(
                    name="📈 Analysis Summary",
                    value=f"• **Members Analyzed:** {len(members)}\n"
                          f"• **Confidence Threshold:** {confidence_threshold}%\n"
                          f"• **Potential Alts Found:** 0",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Generate detailed report
            report_embeds = await self._generate_report(
                guild, filtered_results, confidence_threshold, detailed
            )
            
            # Send report embeds
            for embed in report_embeds:
                await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Log the analysis
            logger.info(
                f"Alt detection completed for {guild.name}: "
                f"{len(filtered_results)} potential alt groups found"
            )
            
        except discord.HTTPException as e:
            logger.error(f"Discord API error during alt detection: {e}")
            await interaction.followup.send(
                "❌ Discord API error occurred. Please try again later.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Unexpected error during alt detection: {e}")
            await interaction.followup.send(
                "❌ An unexpected error occurred during analysis. Please contact the bot administrator.",
                ephemeral=True
            )
    
    async def _fetch_member_data(self, guild: discord.Guild) -> List[Dict]:
        """Fetch comprehensive member data for analysis."""
        members = []
        
        # Use chunking for large servers to avoid rate limits
        async for member in guild.fetch_members(limit=None):
            try:
                member_data = {
                    'id': member.id,
                    'username': member.name,
                    'display_name': member.display_name,
                    'discriminator': member.discriminator,
                    'created_at': member.created_at,
                    'joined_at': member.joined_at,
                    'avatar_url': str(member.avatar.url) if member.avatar else None,
                    'is_bot': member.bot,
                    'roles': [role.id for role in member.roles if role.id != guild.default_role.id],
                    'premium_since': member.premium_since,
                    'status': str(member.status) if hasattr(member, 'status') else 'unknown'
                }
                
                # Get recent message activity (last 30 days)
                recent_activity = await self._get_member_activity(guild, member)
                member_data.update(recent_activity)
                
                members.append(member_data)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error fetching data for member {member.id}: {e}")
                continue
        
        return members
    
    async def _get_member_activity(self, guild: discord.Guild, member: discord.Member) -> Dict:
        """Get member activity data for behavioral analysis."""
        activity_data = {
            'message_count_7d': 0,
            'message_count_30d': 0,
            'channels_used': set(),
            'message_times': [],
            'avg_message_length': 0,
            'reaction_count': 0
        }
        
        cutoff_7d = datetime.utcnow() - timedelta(days=7)
        cutoff_30d = datetime.utcnow() - timedelta(days=30)
        
        message_lengths = []
        
        try:
            # Sample activity from text channels (limit to avoid rate limits)
            for channel in guild.text_channels[:10]:  # Limit channel scanning
                if not channel.permissions_for(guild.me).read_message_history:
                    continue
                
                try:
                    async for message in channel.history(limit=100, after=cutoff_30d):
                        if message.author.id == member.id:
                            activity_data['message_count_30d'] += 1
                            activity_data['channels_used'].add(channel.id)
                            activity_data['message_times'].append(message.created_at)
                            message_lengths.append(len(message.content))
                            activity_data['reaction_count'] += len(message.reactions)
                            
                            if message.created_at >= cutoff_7d:
                                activity_data['message_count_7d'] += 1
                    
                    # Small delay between channels
                    await asyncio.sleep(0.2)
                    
                except discord.Forbidden:
                    continue
                except Exception as e:
                    logger.warning(f"Error reading channel {channel.id}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error getting activity for member {member.id}: {e}")
        
        # Calculate averages
        activity_data['channels_used'] = len(activity_data['channels_used'])
        activity_data['avg_message_length'] = (
            sum(message_lengths) / len(message_lengths) if message_lengths else 0
        )
        
        return activity_data
    
    async def _perform_comprehensive_analysis(self, guild_id: int, members: List[Dict]) -> List[Dict]:
        """Perform comprehensive alt account analysis using multiple methods."""
        results = []
        
        # 1. Account Creation Date Pattern Analysis
        creation_clusters = await self.pattern_detector.analyze_creation_patterns(members)
        
        # 2. Username Similarity Analysis
        username_similarities = await self.pattern_detector.analyze_username_similarities(members)
        
        # 3. Join Pattern Analysis
        join_patterns = await self.pattern_detector.analyze_join_patterns(members)
        
        # 4. Behavioral Pattern Analysis
        behavioral_patterns = await self.analyzer.analyze_behavioral_patterns(members)
        
        # 5. Account Age and Activity Correlation
        activity_correlations = await self.analyzer.analyze_activity_correlations(members)
        
        # Combine all analysis results
        all_analyses = [
            creation_clusters,
            username_similarities,
            join_patterns,
            behavioral_patterns,
            activity_correlations
        ]
        
        # Merge and score potential alt groups
        potential_groups = await self._merge_analysis_results(all_analyses, members)
        
        for group in potential_groups:
            confidence_score = await self._calculate_confidence_score(group, members)
            
            if confidence_score > 0:  # Only include groups with some evidence
                results.append({
                    'members': group['members'],
                    'confidence_score': confidence_score,
                    'evidence': group['evidence'],
                    'analysis_details': group['details']
                })
        
        # Sort by confidence score (highest first)
        results.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return results
    
    async def _merge_analysis_results(self, analyses: List[List], members: List[Dict]) -> List[Dict]:
        """Merge results from different analysis methods to identify potential alt groups."""
        member_connections = {}
        
        # Initialize connections for each member
        for member in members:
            member_connections[member['id']] = {
                'connected_to': set(),
                'evidence': [],
                'details': {}
            }
        
        # Process each analysis method
        for analysis_type, analysis_results in enumerate(analyses):
            for result in analysis_results:
                member_ids = result.get('member_ids', [])
                evidence = result.get('evidence', '')
                details = result.get('details', {})
                
                # Connect all members in this result to each other
                for i, member_id in enumerate(member_ids):
                    for j, other_id in enumerate(member_ids):
                        if i != j and member_id in member_connections:
                            member_connections[member_id]['connected_to'].add(other_id)
                            if evidence:
                                member_connections[member_id]['evidence'].append(evidence)
                            if details:
                                member_connections[member_id]['details'][f'analysis_{analysis_type}'] = details
        
        # Group connected members
        groups = []
        processed = set()
        
        for member_id, connections in member_connections.items():
            if member_id in processed or not connections['connected_to']:
                continue
            
            # Build group using BFS
            group_members = {member_id}
            queue = [member_id]
            
            while queue:
                current = queue.pop(0)
                if current in member_connections:
                    for connected_id in member_connections[current]['connected_to']:
                        if connected_id not in group_members:
                            group_members.add(connected_id)
                            queue.append(connected_id)
            
            # Collect evidence for the group
            group_evidence = set()
            group_details = {}
            
            for gm_id in group_members:
                if gm_id in member_connections:
                    group_evidence.update(member_connections[gm_id]['evidence'])
                    group_details.update(member_connections[gm_id]['details'])
            
            groups.append({
                'members': list(group_members),
                'evidence': list(group_evidence),
                'details': group_details
            })
            
            processed.update(group_members)
        
        return groups
    
    async def _calculate_confidence_score(self, group: Dict, members: List[Dict]) -> int:
        """Calculate confidence score for a potential alt group based on evidence strength."""
        base_score = 0
        evidence_count = len(group['evidence'])
        member_count = len(group['members'])
        
        if member_count < 2:
            return 0
        
        # Base score from evidence count
        base_score += min(evidence_count * 15, 60)  # Max 60 from evidence count
        
        # Bonus for multiple members
        if member_count > 2:
            base_score += min((member_count - 2) * 10, 30)  # Max 30 bonus
        
        # Analyze evidence quality
        evidence_quality_bonus = 0
        evidence_text = ' '.join(group['evidence']).lower()
        
        # High-confidence indicators
        if 'creation time' in evidence_text:
            evidence_quality_bonus += 20
        if 'username similarity' in evidence_text:
            evidence_quality_bonus += 15
        if 'join pattern' in evidence_text:
            evidence_quality_bonus += 10
        if 'behavioral pattern' in evidence_text:
            evidence_quality_bonus += 15
        if 'activity correlation' in evidence_text:
            evidence_quality_bonus += 10
        
        # Get member data for additional analysis
        group_member_data = [m for m in members if m['id'] in group['members']]
        
        # Account age similarity bonus
        if len(group_member_data) > 1:
            creation_times = [m['created_at'] for m in group_member_data]
            time_diffs = []
            for i in range(len(creation_times)):
                for j in range(i + 1, len(creation_times)):
                    diff = abs((creation_times[i] - creation_times[j]).total_seconds())
                    time_diffs.append(diff)
            
            if time_diffs:
                avg_diff = sum(time_diffs) / len(time_diffs)
                if avg_diff < 86400:  # Within 24 hours
                    evidence_quality_bonus += 25
                elif avg_diff < 604800:  # Within 1 week
                    evidence_quality_bonus += 15
                elif avg_diff < 2592000:  # Within 1 month
                    evidence_quality_bonus += 10
        
        final_score = min(base_score + evidence_quality_bonus, 100)
        return max(final_score, 0)
    
    async def _generate_report(
        self, 
        guild: discord.Guild, 
        results: List[Dict], 
        threshold: int, 
        detailed: bool
    ) -> List[discord.Embed]:
        """Generate detailed report embeds for alt detection results."""
        embeds = []
        
        # Main summary embed
        summary_embed = discord.Embed(
            title="🔍 Alt Account Detection Report",
            description=f"Comprehensive analysis completed for **{guild.name}**",
            color=discord.Color.red() if results else discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        summary_embed.add_field(
            name="📊 Analysis Summary",
            value=f"• **Members Analyzed:** {len(guild.members)}\n"
                  f"• **Confidence Threshold:** {threshold}%\n"
                  f"• **Potential Alt Groups:** {len(results)}\n"
                  f"• **Total Suspected Accounts:** {sum(len(r['members']) for r in results)}",
            inline=False
        )
        
        if results:
            summary_embed.add_field(
                name="⚠️ Detection Methods Used",
                value="• Account creation pattern analysis\n"
                      "• Username similarity detection\n"
                      "• Server join pattern analysis\n"
                      "• Behavioral pattern matching\n"
                      "• Activity correlation analysis",
                inline=False
            )
        
        embeds.append(summary_embed)
        
        # Individual group reports
        for i, result in enumerate(results[:10]):  # Limit to first 10 groups
            confidence = result['confidence_score']
            member_ids = result['members']
            evidence = result['evidence']
            
            # Get member objects
            group_members = []
            for member_id in member_ids:
                member = guild.get_member(member_id)
                if member:
                    group_members.append(member)
            
            if not group_members:
                continue
            
            # Determine embed color based on confidence
            if confidence >= 90:
                color = discord.Color.dark_red()
                risk_level = "🔴 CRITICAL"
            elif confidence >= 80:
                color = discord.Color.red()
                risk_level = "🟠 HIGH"
            elif confidence >= 70:
                color = discord.Color.orange()
                risk_level = "🟡 MEDIUM"
            else:
                color = discord.Color.yellow()
                risk_level = "🟢 LOW"
            
            group_embed = discord.Embed(
                title=f"Potential Alt Group #{i + 1}",
                description=f"**Risk Level:** {risk_level}\n**Confidence Score:** {confidence}%",
                color=color,
                timestamp=datetime.utcnow()
            )
            
            # Member information
            member_info = []
            for member in group_members[:5]:  # Limit to 5 members per group
                created_days = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
                joined_days = (datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days if member.joined_at else "Unknown"
                
                member_info.append(
                    f"**{member.display_name}** (`{member.name}`)\n"
                    f"└ ID: `{member.id}`\n"
                    f"└ Created: {created_days} days ago\n"
                    f"└ Joined: {joined_days} days ago" if isinstance(joined_days, int) else f"└ Joined: {joined_days}"
                )
            
            if len(group_members) > 5:
                member_info.append(f"... and {len(group_members) - 5} more members")
            
            group_embed.add_field(
                name=f"👥 Suspected Members ({len(group_members)})",
                value="\n\n".join(member_info),
                inline=False
            )
            
            # Evidence
            if evidence:
                evidence_text = "\n".join([f"• {ev}" for ev in evidence[:5]])
                if len(evidence) > 5:
                    evidence_text += f"\n• ... and {len(evidence) - 5} more indicators"
                
                group_embed.add_field(
                    name="🔍 Evidence Found",
                    value=evidence_text,
                    inline=False
                )
            
            # Detailed analysis if requested
            if detailed and 'analysis_details' in result:
                details = result['analysis_details']
                if details:
                    detail_text = ""
                    for key, value in details.items():
                        if isinstance(value, dict):
                            detail_text += f"**{key.replace('_', ' ').title()}:**\n"
                            for k, v in value.items():
                                detail_text += f"└ {k}: {v}\n"
                        else:
                            detail_text += f"**{key.replace('_', ' ').title()}:** {value}\n"
                    
                    if detail_text:
                        group_embed.add_field(
                            name="📋 Detailed Analysis",
                            value=detail_text[:1024],  # Discord field limit
                            inline=False
                        )
            
            embeds.append(group_embed)
        
        # Add footer to last embed
        if embeds:
            embeds[-1].set_footer(
                text=f"Alt Detection System • Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
        
        return embeds

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(AltDetectionCog(bot))
    logger.info("Alt Detection Cog setup completed")
