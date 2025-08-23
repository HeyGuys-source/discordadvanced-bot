import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
import statistics
from collections import defaultdict, Counter
import math

logger = logging.getLogger(__name__)

class BehavioralAnalyzer:
    """Advanced behavioral analysis for detecting alt account patterns."""
    
    def __init__(self):
        self.analysis_cache = {}
    
    async def analyze_behavioral_patterns(self, members: List[Dict]) -> List[Dict]:
        """
        Analyze behavioral patterns to identify potential alt accounts.
        
        Args:
            members: List of member data dictionaries
            
        Returns:
            List of potential alt groups with evidence
        """
        results = []
        
        # Filter out bots and inactive accounts
        active_members = [
            m for m in members 
            if not m.get('is_bot', False) and 
            (m.get('message_count_30d', 0) > 0 or m.get('message_count_7d', 0) > 0)
        ]
        
        if len(active_members) < 2:
            return results
        
        # 1. Message timing pattern analysis
        timing_groups = await self._analyze_message_timing_patterns(active_members)
        results.extend(timing_groups)
        
        # 2. Activity level correlation analysis
        activity_groups = await self._analyze_activity_correlations(active_members)
        results.extend(activity_groups)
        
        # 3. Communication pattern analysis
        communication_groups = await self._analyze_communication_patterns(active_members)
        results.extend(communication_groups)
        
        # 4. Channel usage pattern analysis
        channel_groups = await self._analyze_channel_usage_patterns(active_members)
        results.extend(channel_groups)
        
        return results
    
    async def _analyze_message_timing_patterns(self, members: List[Dict]) -> List[Dict]:
        """Analyze message timing patterns to identify synchronized activity."""
        results = []
        
        # Group members by their message timing patterns
        timing_profiles = {}
        
        for member in members:
            message_times = member.get('message_times', [])
            if not message_times:
                continue
            
            # Create timing profile based on hour-of-day distribution
            hour_distribution = [0] * 24
            for timestamp in message_times:
                hour = timestamp.hour
                hour_distribution[hour] += 1
            
            # Normalize distribution
            total_messages = sum(hour_distribution)
            if total_messages > 0:
                normalized_dist = [count / total_messages for count in hour_distribution]
                timing_profiles[member['id']] = {
                    'distribution': normalized_dist,
                    'total_messages': total_messages,
                    'peak_hours': self._get_peak_hours(normalized_dist),
                    'activity_variance': statistics.variance(normalized_dist) if len(normalized_dist) > 1 else 0
                }
        
        # Find members with similar timing patterns
        member_ids = list(timing_profiles.keys())
        
        for i in range(len(member_ids)):
            for j in range(i + 1, len(member_ids)):
                member1_id = member_ids[i]
                member2_id = member_ids[j]
                
                profile1 = timing_profiles[member1_id]
                profile2 = timing_profiles[member2_id]
                
                # Calculate timing similarity
                similarity = await self._calculate_timing_similarity(profile1, profile2)
                
                if similarity > 0.8:  # High similarity threshold
                    evidence = f"Message timing pattern similarity: {similarity:.2%}"
                    details = {
                        'timing_similarity': similarity,
                        'member1_peak_hours': profile1['peak_hours'],
                        'member2_peak_hours': profile2['peak_hours'],
                        'variance_diff': abs(profile1['activity_variance'] - profile2['activity_variance'])
                    }
                    
                    results.append({
                        'member_ids': [member1_id, member2_id],
                        'evidence': evidence,
                        'details': details
                    })
        
        return results
    
    async def _analyze_activity_correlations(self, members: List[Dict]) -> List[Dict]:
        """Analyze activity level correlations between members."""
        results = []
        
        # Create activity profiles
        activity_profiles = {}
        
        for member in members:
            profile = {
                'message_count_7d': member.get('message_count_7d', 0),
                'message_count_30d': member.get('message_count_30d', 0),
                'channels_used': member.get('channels_used', 0),
                'avg_message_length': member.get('avg_message_length', 0),
                'reaction_count': member.get('reaction_count', 0)
            }
            
            # Calculate activity score
            activity_score = (
                profile['message_count_7d'] * 2 +
                profile['message_count_30d'] +
                profile['channels_used'] * 5 +
                min(profile['avg_message_length'] / 10, 20) +
                profile['reaction_count']
            )
            
            profile['activity_score'] = activity_score
            activity_profiles[member['id']] = profile
        
        # Find members with suspiciously similar activity levels
        member_ids = list(activity_profiles.keys())
        
        for i in range(len(member_ids)):
            for j in range(i + 1, len(member_ids)):
                member1_id = member_ids[i]
                member2_id = member_ids[j]
                
                profile1 = activity_profiles[member1_id]
                profile2 = activity_profiles[member2_id]
                
                # Calculate activity correlation
                correlation = await self._calculate_activity_correlation(profile1, profile2)
                
                if correlation > 0.85:  # High correlation threshold
                    evidence = f"Activity level correlation: {correlation:.2%}"
                    details = {
                        'activity_correlation': correlation,
                        'member1_score': profile1['activity_score'],
                        'member2_score': profile2['activity_score'],
                        'score_difference': abs(profile1['activity_score'] - profile2['activity_score'])
                    }
                    
                    results.append({
                        'member_ids': [member1_id, member2_id],
                        'evidence': evidence,
                        'details': details
                    })
        
        return results
    
    async def _analyze_communication_patterns(self, members: List[Dict]) -> List[Dict]:
        """Analyze communication patterns for similarities."""
        results = []
        
        # Group members by communication characteristics
        communication_profiles = {}
        
        for member in members:
            avg_length = member.get('avg_message_length', 0)
            message_count = member.get('message_count_30d', 0)
            reaction_count = member.get('reaction_count', 0)
            
            if message_count == 0:
                continue
            
            # Calculate communication metrics
            reaction_ratio = reaction_count / message_count if message_count > 0 else 0
            activity_intensity = message_count / max(member.get('channels_used', 1), 1)
            
            profile = {
                'avg_message_length': avg_length,
                'reaction_ratio': reaction_ratio,
                'activity_intensity': activity_intensity,
                'message_frequency': message_count / 30  # Messages per day
            }
            
            communication_profiles[member['id']] = profile
        
        # Compare communication patterns
        member_ids = list(communication_profiles.keys())
        
        for i in range(len(member_ids)):
            for j in range(i + 1, len(member_ids)):
                member1_id = member_ids[i]
                member2_id = member_ids[j]
                
                profile1 = communication_profiles[member1_id]
                profile2 = communication_profiles[member2_id]
                
                # Calculate communication similarity
                similarity = await self._calculate_communication_similarity(profile1, profile2)
                
                if similarity > 0.8:  # High similarity threshold
                    evidence = f"Communication pattern similarity: {similarity:.2%}"
                    details = {
                        'communication_similarity': similarity,
                        'avg_length_diff': abs(profile1['avg_message_length'] - profile2['avg_message_length']),
                        'reaction_ratio_diff': abs(profile1['reaction_ratio'] - profile2['reaction_ratio']),
                        'intensity_diff': abs(profile1['activity_intensity'] - profile2['activity_intensity'])
                    }
                    
                    results.append({
                        'member_ids': [member1_id, member2_id],
                        'evidence': evidence,
                        'details': details
                    })
        
        return results
    
    async def _analyze_channel_usage_patterns(self, members: List[Dict]) -> List[Dict]:
        """Analyze channel usage patterns for similarities."""
        results = []
        
        # This would require more detailed channel usage data
        # For now, we'll use basic channel count analysis
        channel_usage = {}
        
        for member in members:
            channels_used = member.get('channels_used', 0)
            message_count = member.get('message_count_30d', 0)
            
            if message_count == 0:
                continue
            
            # Calculate channel diversity ratio
            diversity_ratio = channels_used / max(message_count, 1)
            
            channel_usage[member['id']] = {
                'channels_used': channels_used,
                'diversity_ratio': diversity_ratio,
                'messages_per_channel': message_count / max(channels_used, 1)
            }
        
        # Find similar channel usage patterns
        member_ids = list(channel_usage.keys())
        
        for i in range(len(member_ids)):
            for j in range(i + 1, len(member_ids)):
                member1_id = member_ids[i]
                member2_id = member_ids[j]
                
                usage1 = channel_usage[member1_id]
                usage2 = channel_usage[member2_id]
                
                # Calculate usage similarity
                channels_diff = abs(usage1['channels_used'] - usage2['channels_used'])
                diversity_diff = abs(usage1['diversity_ratio'] - usage2['diversity_ratio'])
                
                # Consider similar if channel usage is very close
                if channels_diff <= 1 and diversity_diff < 0.1:
                    similarity_score = 1.0 - (channels_diff * 0.2 + diversity_diff * 2)
                    
                    if similarity_score > 0.8:
                        evidence = f"Channel usage pattern similarity: {similarity_score:.2%}"
                        details = {
                            'usage_similarity': similarity_score,
                            'channels_diff': channels_diff,
                            'diversity_diff': diversity_diff
                        }
                        
                        results.append({
                            'member_ids': [member1_id, member2_id],
                            'evidence': evidence,
                            'details': details
                        })
        
        return results
    
    async def analyze_activity_correlations(self, members: List[Dict]) -> List[Dict]:
        """Analyze correlations between account age and activity levels."""
        results = []
        
        # Calculate expected activity based on account age
        activity_analysis = {}
        
        for member in members:
            if member.get('is_bot', False):
                continue
            
            created_at = member.get('created_at')
            joined_at = member.get('joined_at')
            
            if not created_at or not joined_at:
                continue
            
            # Calculate account age and server tenure
            now = datetime.utcnow()
            account_age_days = (now - created_at.replace(tzinfo=None)).days
            server_tenure_days = (now - joined_at.replace(tzinfo=None)).days
            
            message_count = member.get('message_count_30d', 0)
            
            # Calculate activity ratios
            activity_per_day = message_count / max(server_tenure_days, 1)
            activity_per_account_day = message_count / max(account_age_days, 1)
            
            activity_analysis[member['id']] = {
                'account_age_days': account_age_days,
                'server_tenure_days': server_tenure_days,
                'activity_per_day': activity_per_day,
                'activity_per_account_day': activity_per_account_day,
                'message_count': message_count
            }
        
        # Find suspicious activity patterns
        member_ids = list(activity_analysis.keys())
        
        # Group by similar account ages (within 7 days)
        age_groups = defaultdict(list)
        for member_id in member_ids:
            age_days = activity_analysis[member_id]['account_age_days']
            age_group = age_days // 7  # Group by week
            age_groups[age_group].append(member_id)
        
        # Analyze each age group for similar activity patterns
        for group_members in age_groups.values():
            if len(group_members) < 2:
                continue
            
            # Check for suspiciously similar activity levels
            for i in range(len(group_members)):
                for j in range(i + 1, len(group_members)):
                    member1_id = group_members[i]
                    member2_id = group_members[j]
                    
                    analysis1 = activity_analysis[member1_id]
                    analysis2 = activity_analysis[member2_id]
                    
                    # Check for similar activity patterns
                    age_diff = abs(analysis1['account_age_days'] - analysis2['account_age_days'])
                    activity_diff = abs(analysis1['activity_per_day'] - analysis2['activity_per_day'])
                    
                    if age_diff <= 7 and activity_diff < 0.5:  # Very similar patterns
                        correlation_score = 1.0 - (age_diff / 7 * 0.3 + activity_diff * 0.4)
                        
                        if correlation_score > 0.8:
                            evidence = f"Activity correlation with account age: {correlation_score:.2%}"
                            details = {
                                'age_correlation': correlation_score,
                                'age_difference_days': age_diff,
                                'activity_difference': activity_diff,
                                'member1_activity': analysis1['activity_per_day'],
                                'member2_activity': analysis2['activity_per_day']
                            }
                            
                            results.append({
                                'member_ids': [member1_id, member2_id],
                                'evidence': evidence,
                                'details': details
                            })
        
        return results
    
    def _get_peak_hours(self, distribution: List[float]) -> List[int]:
        """Get peak activity hours from distribution."""
        if not distribution:
            return []
        
        avg = sum(distribution) / len(distribution)
        threshold = avg * 1.5  # 50% above average
        
        peak_hours = []
        for hour, activity in enumerate(distribution):
            if activity >= threshold:
                peak_hours.append(hour)
        
        return peak_hours
    
    async def _calculate_timing_similarity(self, profile1: Dict, profile2: Dict) -> float:
        """Calculate similarity between timing profiles."""
        dist1 = profile1['distribution']
        dist2 = profile2['distribution']
        
        if len(dist1) != len(dist2):
            return 0.0
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(dist1, dist2))
        magnitude1 = math.sqrt(sum(a * a for a in dist1))
        magnitude2 = math.sqrt(sum(b * b for b in dist2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Bonus for similar peak hours
        peaks1 = set(profile1['peak_hours'])
        peaks2 = set(profile2['peak_hours'])
        
        if peaks1 and peaks2:
            peak_overlap = len(peaks1.intersection(peaks2)) / len(peaks1.union(peaks2))
            similarity = similarity * 0.7 + peak_overlap * 0.3
        
        return max(0.0, min(1.0, similarity))
    
    async def _calculate_activity_correlation(self, profile1: Dict, profile2: Dict) -> float:
        """Calculate correlation between activity profiles."""
        # Extract numeric values for correlation
        values1 = [
            profile1['message_count_7d'],
            profile1['message_count_30d'],
            profile1['channels_used'],
            min(profile1['avg_message_length'], 1000),  # Cap message length
            profile1['reaction_count']
        ]
        
        values2 = [
            profile2['message_count_7d'],
            profile2['message_count_30d'],
            profile2['channels_used'],
            min(profile2['avg_message_length'], 1000),
            profile2['reaction_count']
        ]
        
        # Calculate correlation coefficient
        if len(values1) != len(values2) or all(v == 0 for v in values1) or all(v == 0 for v in values2):
            return 0.0
        
        # Normalize values to 0-1 range
        max_vals = [max(v1, v2) for v1, v2 in zip(values1, values2)]
        norm_vals1 = [v1 / max(mv, 1) for v1, mv in zip(values1, max_vals)]
        norm_vals2 = [v2 / max(mv, 1) for v2, mv in zip(values2, max_vals)]
        
        # Calculate similarity as inverse of distance
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(norm_vals1, norm_vals2)))
        similarity = 1.0 / (1.0 + distance)
        
        return similarity
    
    async def _calculate_communication_similarity(self, profile1: Dict, profile2: Dict) -> float:
        """Calculate similarity between communication profiles."""
        # Weight different aspects of communication
        weights = {
            'avg_message_length': 0.3,
            'reaction_ratio': 0.25,
            'activity_intensity': 0.25,
            'message_frequency': 0.2
        }
        
        similarity_score = 0.0
        
        for metric, weight in weights.items():
            val1 = profile1.get(metric, 0)
            val2 = profile2.get(metric, 0)
            
            if val1 == 0 and val2 == 0:
                metric_similarity = 1.0
            elif val1 == 0 or val2 == 0:
                metric_similarity = 0.0
            else:
                # Calculate relative similarity
                max_val = max(val1, val2)
                min_val = min(val1, val2)
                metric_similarity = min_val / max_val
            
            similarity_score += metric_similarity * weight
        
        return similarity_score
