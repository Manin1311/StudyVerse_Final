
from extensions import db
from models import User, Friendship, TopicProficiency
from datetime import datetime, timedelta
import random

class MatchmakingService:
    @staticmethod
    def find_matches(user):
        # 1. Get candidates (not self, not already friends)
        subq = db.session.query(Friendship.friend_id).filter(Friendship.user_id == user.id)
        subq2 = db.session.query(Friendship.user_id).filter(Friendship.friend_id == user.id)
        
        candidates = User.query.filter(
            User.id != user.id,
            ~User.id.in_(subq),
            ~User.id.in_(subq2),
            User.is_public_profile == True
        ).limit(50).all()
        
        matches = []
        user_proficiencies = {p.topic_name for p in TopicProficiency.query.filter_by(user_id=user.id).all()}
        
        for candidate in candidates:
            score = 0
            
            # Level Compatibility
            level_diff = abs(user.level - candidate.level)
            if level_diff <= 5:
                score += 20
            elif level_diff <= 10:
                score += 10
                
            # Topic Overlap
            cand_prof = {p.topic_name for p in TopicProficiency.query.filter_by(user_id=candidate.id).all()}
            overlap = user_proficiencies.intersection(cand_prof)
            score += len(overlap) * 10
            
            # Recency
            if candidate.last_seen: 
                 delta = datetime.utcnow() - candidate.last_seen
                 if delta < timedelta(days=1):
                    score += 30 
                 elif delta < timedelta(days=7):
                    score += 10
            
            # Random jitter to keep list fresh if scores are tie
            score += random.randint(0, 5)

            matches.append({
                'user': candidate,
                'score': score,
                'common_topics': list(overlap)[:3]
            })
            
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:5]
