import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter
from fuzzywuzzy import fuzz
import re

logger = logging.getLogger(__name__)

class PatternDetector:
    """Advanced pattern detection for identifying potential alt accounts."""
    
    def __init__(self):
        self.username_cache = {}
        self.pattern_cache = {}
    
    async def analyze_creation_patterns(self, members: List[Dict]) -> List[Dict]:
        """
        Analyze account creation date patterns to identify potential mass-created accounts.
        
        Args:
            members: List of member data dictionaries
            
        Returns:
            List of potential alt groups based on creation patterns
        """
        results = []
        
        # Filter out bots and accounts without creation dates
        valid_members = [
            m for m in members 
            if not m.get('is_bot', False) and m.get('created_at')
        ]
        
        if len(valid_members) < 2:
            return results
        
        # Group members by creation time windows
        time_groups = await self._group_by_creation_time(valid_members)
        
        # Analyze each time group for suspicious patterns
        for time_window, group_members in time_groups.items():
            if len(group_members) < 2:
                continue
            
            # Check for rapid succession creation
            creation_times = [m['created_at'] for m in group_members]
            creation_times.sort()
            
            suspicious_groups = await self._find_rapid_creation_groups(group_members, creation_times)
            results.extend(suspicious_groups)
        
        return results
    
    async def analyze_username_similarities(self, members: List[Dict]) -> List[Dict]:
        """
        Analyze username and display name similarities using fuzzy matching.
        
        Args:
            members: List of member data dictionaries
            
        Returns:
            List of potential alt groups based on username similarities
        """
        results = []
        
        # Filter out bots
        valid_members = [m for m in members if not m.get('is_bot', False)]
        
        if len(valid_members) < 2:
            return results
        
        # Analyze different types of username similarities
        username_groups = await self._analyze_username_patterns(valid_members)
        display_name_groups = await self._analyze_display_name_patterns(valid_members)
        pattern_groups = await self._analyze_naming_patterns(valid_members)
        
        # Combine all username-based results
        all_groups = username_groups + display_name_groups + pattern_groups
        
        # Remove duplicates and merge overlapping groups
        merged_groups = await self._merge_similar_groups(all_groups)
        
        return merged_groups
    
    async def analyze_join_patterns(self, members: List[Dict]) -> List[Dict]:
        """
        Analyze server join patterns to identify coordinated account entries.
        
        Args:
            members: List of member data dictionaries
            
        Returns:
            List of potential alt groups based on join patterns
        """
        results = []
        
        # Filter members with valid join dates
        valid_members = [
            m for m in members 
            if not m.get('is_bot', False) and m.get('joined_at')
        ]
        
        if len(valid_members) < 2:
            return results
        
        # Group by join time windows
        join_groups = await self._group_by_join_time(valid_members)
        
        # Analyze each group for suspicious patterns
        for time_window, group_members in join_groups.items():
            if len(group_members) < 2:
                continue
            
            join_times = [m['joined_at'] for m in group_members]
            join_times.sort()
            
            # Look for rapid successive joins
            suspicious_groups = await self._find_rapid_join_groups(group_members, join_times)
            results.extend(suspicious_groups)
        
        return results
    
    async def _group_by_creation_time(self, members: List[Dict]) -> Dict[str, List[Dict]]:
        """Group members by creation time windows."""
        time_groups = defaultdict(list)
        
        for member in members:
            created_at = member['created_at']
            
            # Create time windows (6-hour periods)
            window_start = created_at.replace(hour=(created_at.hour // 6) * 6, minute=0, second=0, microsecond=0)
            window_key = window_start.isoformat()
            
            time_groups[window_key].append(member)
        
        return dict(time_groups)
    
    async def _group_by_join_time(self, members: List[Dict]) -> Dict[str, List[Dict]]:
        """Group members by join time windows."""
        time_groups = defaultdict(list)
        
        for member in members:
            joined_at = member['joined_at']
            
            # Create time windows (1-hour periods for join times)
            window_start = joined_at.replace(minute=0, second=0, microsecond=0)
            window_key = window_start.isoformat()
            
            time_groups[window_key].append(member)
        
        return dict(time_groups)
    
    async def _find_rapid_creation_groups(self, members: List[Dict], creation_times: List[datetime]) -> List[Dict]:
        """Find groups of accounts created in rapid succession."""
        results = []
        
        # Define thresholds for suspicious creation patterns
        rapid_threshold = timedelta(minutes=30)  # 30 minutes
        burst_threshold = timedelta(hours=2)     # 2 hours
        
        # Check for rapid creation (within 30 minutes)
        for i in range(len(creation_times)):
            rapid_group = [members[i]]
            
            for j in range(len(creation_times)):
                if i != j:
                    time_diff = abs(creation_times[i] - creation_times[j])
                    if time_diff <= rapid_threshold:
                        rapid_group.append(members[j])
            
            if len(rapid_group) >= 2:
                member_ids = [m['id'] for m in rapid_group]
                max_diff = max(abs(creation_times[i] - t) for t in creation_times)
                
                evidence = f"Accounts created within {max_diff} (rapid creation pattern)"
                details = {
                    'creation_window': str(max_diff),
                    'threshold_type': 'rapid',
                    'account_count': len(rapid_group)
                }
                
                results.append({
                    'member_ids': member_ids,
                    'evidence': evidence,
                    'details': details
                })
        
        # Check for burst creation (multiple accounts within 2 hours)
        if len(members) >= 3:
            for i in range(len(creation_times) - 2):
                burst_window = creation_times[i + 2] - creation_times[i]
                
                if burst_window <= burst_threshold:
                    burst_group = members[i:i+3]
                    member_ids = [m['id'] for m in burst_group]
                    
                    evidence = f"Account creation burst: 3+ accounts within {burst_window}"
                    details = {
                        'creation_window': str(burst_window),
                        'threshold_type': 'burst',
                        'account_count': len(burst_group)
                    }
                    
                    results.append({
                        'member_ids': member_ids,
                        'evidence': evidence,
                        'details': details
                    })
        
        return results
    
    async def _find_rapid_join_groups(self, members: List[Dict], join_times: List[datetime]) -> List[Dict]:
        """Find groups of accounts that joined in rapid succession."""
        results = []
        
        rapid_threshold = timedelta(minutes=15)  # 15 minutes for joins
        
        for i in range(len(join_times)):
            rapid_group = [members[i]]
            
            for j in range(len(join_times)):
                if i != j:
                    time_diff = abs(join_times[i] - join_times[j])
                    if time_diff <= rapid_threshold:
                        rapid_group.append(members[j])
            
            if len(rapid_group) >= 2:
                member_ids = [m['id'] for m in rapid_group]
                max_diff = max(abs(join_times[i] - t) for t in join_times)
                
                evidence = f"Accounts joined within {max_diff} (coordinated join pattern)"
                details = {
                    'join_window': str(max_diff),
                    'threshold_type': 'rapid_join',
                    'account_count': len(rapid_group)
                }
                
                results.append({
                    'member_ids': member_ids,
                    'evidence': evidence,
                    'details': details
                })
        
        return results
    
    async def _analyze_username_patterns(self, members: List[Dict]) -> List[Dict]:
        """Analyze username similarities using fuzzy matching."""
        results = []
        
        # Extract usernames and clean them
        username_data = []
        for member in members:
            username = member.get('username', '').lower().strip()
            if username:
                username_data.append({
                    'id': member['id'],
                    'username': username,
                    'original': member.get('username', '')
                })
        
        # Compare all usernames pairwise
        for i in range(len(username_data)):
            for j in range(i + 1, len(username_data)):
                user1 = username_data[i]
                user2 = username_data[j]
                
                # Calculate various similarity metrics
                ratio = fuzz.ratio(user1['username'], user2['username'])
                partial_ratio = fuzz.partial_ratio(user1['username'], user2['username'])
                token_sort_ratio = fuzz.token_sort_ratio(user1['username'], user2['username'])
                
                # Check for specific patterns
                pattern_similarity = await self._check_username_patterns(user1['username'], user2['username'])
                
                # Determine if usernames are suspiciously similar
                max_similarity = max(ratio, partial_ratio, token_sort_ratio, pattern_similarity)
                
                if max_similarity >= 85:  # High similarity threshold
                    evidence = f"Username similarity: {user1['original']} ↔ {user2['original']} ({max_similarity}% similar)"
                    details = {
                        'similarity_score': max_similarity,
                        'ratio': ratio,
                        'partial_ratio': partial_ratio,
                        'token_sort_ratio': token_sort_ratio,
                        'pattern_similarity': pattern_similarity
                    }
                    
                    results.append({
                        'member_ids': [user1['id'], user2['id']],
                        'evidence': evidence,
                        'details': details
                    })
        
        return results
    
    async def _analyze_display_name_patterns(self, members: List[Dict]) -> List[Dict]:
        """Analyze display name similarities."""
        results = []
        
        # Extract display names
        display_name_data = []
        for member in members:
            display_name = member.get('display_name', '').lower().strip()
            username = member.get('username', '').lower().strip()
            
            # Use display name if different from username, otherwise skip
            if display_name and display_name != username:
                display_name_data.append({
                    'id': member['id'],
                    'display_name': display_name,
                    'original': member.get('display_name', '')
                })
        
        # Compare display names
        for i in range(len(display_name_data)):
            for j in range(i + 1, len(display_name_data)):
                name1 = display_name_data[i]
                name2 = display_name_data[j]
                
                ratio = fuzz.ratio(name1['display_name'], name2['display_name'])
                partial_ratio = fuzz.partial_ratio(name1['display_name'], name2['display_name'])
                
                max_similarity = max(ratio, partial_ratio)
                
                if max_similarity >= 80:  # Slightly lower threshold for display names
                    evidence = f"Display name similarity: {name1['original']} ↔ {name2['original']} ({max_similarity}% similar)"
                    details = {
                        'similarity_score': max_similarity,
                        'ratio': ratio,
                        'partial_ratio': partial_ratio
                    }
                    
                    results.append({
                        'member_ids': [name1['id'], name2['id']],
                        'evidence': evidence,
                        'details': details
                    })
        
        return results
    
    async def _analyze_naming_patterns(self, members: List[Dict]) -> List[Dict]:
        """Analyze naming patterns for common alt account strategies."""
        results = []
        
        # Common alt account naming patterns
        patterns = [
            r'^(.+)\d+$',           # Base name followed by numbers
            r'^(.+)_+(.+)$',        # Names with underscores
            r'^(.+)alt\d*$',        # Names ending with 'alt'
            r'^alt(.+)$',           # Names starting with 'alt'
            r'^(.+)backup\d*$',     # Names with 'backup'
            r'^(.+)new\d*$',        # Names with 'new'
            r'^(.+)[._-]\d+$',      # Names with separators and numbers
        ]
        
        # Group members by detected patterns
        pattern_groups = defaultdict(list)
        
        for member in members:
            username = member.get('username', '').lower()
            
            for pattern in patterns:
                match = re.match(pattern, username)
                if match:
                    base_name = match.group(1)
                    if len(base_name) >= 3:  # Minimum base name length
                        pattern_groups[base_name].append(member)
        
        # Find groups with multiple members
        for base_name, group_members in pattern_groups.items():
            if len(group_members) >= 2:
                member_ids = [m['id'] for m in group_members]
                usernames = [m.get('username', '') for m in group_members]
                
                evidence = f"Common naming pattern detected: base '{base_name}' in usernames {usernames}"
                details = {
                    'base_pattern': base_name,
                    'usernames': usernames,
                    'pattern_type': 'naming_convention'
                }
                
                results.append({
                    'member_ids': member_ids,
                    'evidence': evidence,
                    'details': details
                })
        
        return results
    
    async def _check_username_patterns(self, username1: str, username2: str) -> int:
        """Check for specific patterns indicating potential alt accounts."""
        # Pattern 1: One username is a substring of another with numbers
        if username1 in username2 or username2 in username1:
            longer = username2 if len(username2) > len(username1) else username1
            shorter = username1 if len(username1) < len(username2) else username2
            
            if longer.startswith(shorter) and longer[len(shorter):].isdigit():
                return 95  # Very high similarity
        
        # Pattern 2: Same base with different numbers/suffixes
        base1 = re.sub(r'\d+$', '', username1)
        base2 = re.sub(r'\d+$', '', username2)
        
        if base1 == base2 and len(base1) >= 3:
            return 90
        
        # Pattern 3: Similar with character substitutions (leet speak, etc.)
        substitutions = {
            '0': 'o', '1': 'i', '1': 'l', '3': 'e', '4': 'a', 
            '5': 's', '7': 't', '@': 'a', '8': 'b'
        }
        
        normalized1 = username1
        normalized2 = username2
        
        for digit, letter in substitutions.items():
            normalized1 = normalized1.replace(digit, letter)
            normalized2 = normalized2.replace(digit, letter)
        
        if normalized1 == normalized2:
            return 85
        
        return 0
    
    async def _merge_similar_groups(self, groups: List[Dict]) -> List[Dict]:
        """Merge groups that have overlapping members."""
        if not groups:
            return []
        
        merged = []
        processed_members = set()
        
        for group in groups:
            member_ids = set(group['member_ids'])
            
            # Check if this group overlaps with any processed members
            if member_ids.intersection(processed_members):
                # Find existing group to merge with
                for existing_group in merged:
                    existing_ids = set(existing_group['member_ids'])
                    if member_ids.intersection(existing_ids):
                        # Merge groups
                        existing_group['member_ids'] = list(existing_ids.union(member_ids))
                        existing_group['evidence'] += f"; {group['evidence']}"
                        existing_group['details'].update(group.get('details', {}))
                        break
            else:
                # New group
                merged.append(group)
                processed_members.update(member_ids)
        
        return merged
