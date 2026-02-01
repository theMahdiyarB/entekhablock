"""
Poll management system for Entekhablock
Handles creation, configuration, and state management of voting polls
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class Poll:
    """
    Represents a single voting poll with configuration and state
    """
    
    def __init__(self, poll_id: str, title: str, options: List[str], 
                 start_time: str, end_time: str, description: str = ""):
        """
        Initialize a new poll
        
        Args:
            poll_id: Unique identifier for the poll
            title: Poll title/question
            options: List of voting options
            start_time: Start datetime (ISO format: YYYY-MM-DD HH:MM:SS)
            end_time: End datetime (ISO format: YYYY-MM-DD HH:MM:SS)
            description: Optional poll description
        """
        self.poll_id = poll_id
        self.title = title
        self.options = options
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.votes = {option: 0 for option in options}  # Vote counter
        self.voters = set()  # Track who voted (by hash)
    
    def is_active(self) -> bool:
        """
        Check if poll is currently active (within time window)
        
        Returns:
            True if poll is active
        """
        now = datetime.now()
        start = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        
        return start <= now <= end
    
    def is_upcoming(self) -> bool:
        """Check if poll hasn't started yet"""
        now = datetime.now()
        start = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        return now < start
    
    def is_ended(self) -> bool:
        """Check if poll has ended"""
        now = datetime.now()
        end = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
        return now > end
    
    def get_status(self) -> str:
        """Get current poll status as string"""
        if self.is_upcoming():
            return "upcoming"
        elif self.is_active():
            return "active"
        else:
            return "ended"
    
    def can_vote(self, voter_hash: str) -> Tuple[bool, str]:
        """
        Check if a voter can vote in this poll
        
        Args:
            voter_hash: Anonymized voter identifier
        
        Returns:
            Tuple of (can_vote: bool, reason: str)
        """
        # Check if poll is active
        if not self.is_active():
            if self.is_upcoming():
                return False, "نظرسنجی هنوز شروع نشده است"
            else:
                return False, "نظرسنجی به پایان رسیده است"
        
        # Check if already voted
        if voter_hash in self.voters:
            return False, "شما قبلاً در این نظرسنجی رأی داده‌اید"
        
        return True, "امکان رأی‌دهی وجود دارد"
    
    def record_vote(self, voter_hash: str, choice: str) -> Tuple[bool, str]:
        """
        Record a vote (updates counter, doesn't touch blockchain)
        
        Args:
            voter_hash: Anonymized voter identifier
            choice: Selected option
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Verify can vote
        can_vote, reason = self.can_vote(voter_hash)
        if not can_vote:
            return False, reason
        
        # Verify choice is valid
        if choice not in self.options:
            return False, "گزینه انتخابی نامعتبر است"
        
        # Record vote
        self.votes[choice] += 1
        self.voters.add(voter_hash)
        
        return True, "رأی با موفقیت ثبت شد"
    
    def get_results(self) -> Dict:
        """
        Get poll results and statistics
        
        Returns:
            Dictionary with results data
        """
        total_votes = sum(self.votes.values())
        
        results = {
            "poll_id": self.poll_id,
            "title": self.title,
            "status": self.get_status(),
            "total_votes": total_votes,
            "votes": self.votes,
            "percentages": {},
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        
        # Calculate percentages
        if total_votes > 0:
            for option, count in self.votes.items():
                results["percentages"][option] = round((count / total_votes) * 100, 2)
        else:
            for option in self.options:
                results["percentages"][option] = 0.0
        
        return results
    
    def to_dict(self) -> Dict:
        """Convert poll to dictionary for serialization"""
        return {
            "poll_id": self.poll_id,
            "title": self.title,
            "options": self.options,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.get_status(),
            "total_votes": sum(self.votes.values())
        }


class PollManager:
    """
    Manages all polls in the system
    Handles storage, retrieval, and persistence
    """
    
    def __init__(self, storage_path: str = "data/polls.json"):
        """
        Initialize poll manager
        
        Args:
            storage_path: Path to JSON file for poll persistence
        """
        self.storage_path = storage_path
        self.polls: Dict[str, Poll] = {}
        self._load_polls()
    
    def _load_polls(self) -> None:
        """Load polls from JSON file"""
        if not os.path.exists(self.storage_path):
            print(f"No existing polls file at {self.storage_path}")
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for poll_data in data.get('polls', []):
                    poll = Poll(
                        poll_id=poll_data['poll_id'],
                        title=poll_data['title'],
                        options=poll_data['options'],
                        start_time=poll_data['start_time'],
                        end_time=poll_data['end_time'],
                        description=poll_data.get('description', '')
                    )
                    
                    # Restore vote counts and voters
                    poll.votes = poll_data.get('votes', {option: 0 for option in poll.options})
                    poll.voters = set(poll_data.get('voters', []))
                    poll.created_at = poll_data.get('created_at', poll.created_at)
                    
                    self.polls[poll.poll_id] = poll
                    
            print(f"Loaded {len(self.polls)} polls from storage")
        except Exception as e:
            print(f"Error loading polls: {e}")
    
    def _save_polls(self) -> None:
        """Save polls to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            data = {
                'polls': [],
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            for poll in self.polls.values():
                poll_dict = poll.to_dict()
                poll_dict['votes'] = poll.votes
                poll_dict['voters'] = list(poll.voters)  # Convert set to list for JSON
                data['polls'].append(poll_dict)
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving polls: {e}")
    
    def create_poll(self, title: str, options: List[str], start_time: str, 
                   end_time: str, description: str = "") -> Tuple[bool, str, Optional[Poll]]:
        """
        Create a new poll
        
        Args:
            title: Poll title
            options: List of options (minimum 2)
            start_time: Start datetime string
            end_time: End datetime string
            description: Optional description
        
        Returns:
            Tuple of (success: bool, message: str, poll: Poll or None)
        """
        # Validation
        if not title or len(title.strip()) < 3:
            return False, "عنوان نظرسنجی باید حداقل ۳ حرف باشد", None
        
        if len(options) < 2:
            return False, "حداقل ۲ گزینه لازم است", None
        
        # Validate datetime format
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, "فرمت تاریخ و زمان نامعتبر است", None
        
        if end_dt <= start_dt:
            return False, "زمان پایان باید بعد از زمان شروع باشد", None
        
        # Generate poll ID
        poll_id = f"poll_{len(self.polls) + 1}_{int(datetime.now().timestamp())}"
        
        # Create poll
        poll = Poll(
            poll_id=poll_id,
            title=title,
            options=options,
            start_time=start_time,
            end_time=end_time,
            description=description
        )
        
        self.polls[poll_id] = poll
        self._save_polls()
        
        return True, "نظرسنجی با موفقیت ایجاد شد", poll
    
    def get_poll(self, poll_id: str) -> Optional[Poll]:
        """Get poll by ID"""
        return self.polls.get(poll_id)
    
    def get_active_polls(self) -> List[Poll]:
        """Get all currently active polls"""
        return [poll for poll in self.polls.values() if poll.is_active()]
    
    def get_all_polls(self) -> List[Poll]:
        """Get all polls"""
        return list(self.polls.values())
    
    def delete_poll(self, poll_id: str) -> Tuple[bool, str]:
        """
        Delete a poll
        
        Args:
            poll_id: Poll identifier
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if poll_id not in self.polls:
            return False, "نظرسنجی یافت نشد"
        
        del self.polls[poll_id]
        self._save_polls()
        
        return True, "نظرسنجی حذف شد"


# Testing
if __name__ == "__main__":
    print("=== Poll Manager Demo ===\n")
    
    pm = PollManager("../data/polls.json")
    
    # Create test poll
    success, msg, poll = pm.create_poll(
        title="آیا با پیاده‌سازی رأی‌گیری الکترونیک موافقید؟",
        options=["بله، کاملاً موافقم", "تا حدودی", "خیر، مخالفم"],
        start_time="2026-01-23 08:00:00",
        end_time="2026-01-24 20:00:00",
        description="نظرسنجی درباره رأی‌گیری الکترونیک"
    )
    
    print(f"Create: {success} - {msg}")
    if poll:
        print(f"Poll ID: {poll.poll_id}")
        print(f"Status: {poll.get_status()}")
        print(f"Active polls: {len(pm.get_active_polls())}")
