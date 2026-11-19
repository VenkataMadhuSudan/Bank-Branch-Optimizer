"""
NLP Customer Feedback, Sentiment Analysis & Topic Attribution Engine.
Features:
- Deterministic Lexicon Polarity Scoring [-1.0, 1.0].
- Multi-Topic Friction Classification (Wait times, Staff shortages, Digital Kiosks, Service Quality).
- Staff & Counter Entity Extraction.
- Actionability Flagging for Managerial Operational Alarms.
- Privacy-Preserving: Entirely local processing with zero external LLM API dependencies.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

POSITIVE_WORDS = {
    "fast", "quick", "helpful", "excellent", "smooth", "great", "easy", "effortless",
    "polite", "friendly", "satisfied", "prompt", "efficient", "professional", "clear",
    "wonderful", "delighted", "superb", "courteous", "impressed", "kind", "competent",
    "speedy", "resolved", "seamless"
}

NEGATIVE_WORDS = {
    "waited", "waiting", "long", "slow", "terrible", "crowd", "overwhelmed", "delay",
    "frustrated", "shortage", "poor", "confusing", "horrible", "awful", "rude",
    "stuck", "useless", "broken", "angry", "tired", "ignored", "waste", "disappointed",
    "unacceptable", "unhelpful", "chaotic", "unbearable", "abandoned"
}

TOPIC_PATTERNS = {
    "Excessive Wait Time / Queue Bottleneck": [
        r"\bwait(?:ed|ing)?\b", r"\blong (?:queue|line)\b", r"\bdelay\b", r"\b(?:hours?|minutes?)\b",
        r"\bcrowd(?:ed)?\b", r"\bslow\b", r"\bstanding\b"
    ],
    "Staff / Counter Shortage": [
        r"\bcounter\b", r"\bstaff\b", r"\bshortage\b", r"\bonly \d counter\b", r"\blunch\b",
        r"\bteller\b", r"\boverwhelmed\b", r"\bunderstaffed\b", r"\bclosed counter\b"
    ],
    "Digital Kiosk & Lobby Hardware Friction": [
        r"\bkiosk\b", r"\batm\b", r"\bapp\b", r"\bmobile\b", r"\bpassbook\b", r"\bonline\b",
        r"\bstatement\b", r"\bself[- ]service\b", r"\bcard machine\b", r"\bcheque deposit\b"
    ],
    "Fast & Courteous Service Quality": [
        r"\bhelpful\b", r"\bpolite\b", r"\bquick turnaround\b", r"\bfriendly\b", r"\bgreat support\b",
        r"\bsmooth\b", r"\bprompt\b", r"\befficient\b", r"\bsatisfied\b", r"\bprofessional\b"
    ],
    "Specialist Advisory & Loan Quality": [
        r"\bloan\b", r"\bmortgage\b", r"\badvisor\b", r"\bforex\b", r"\binvestment\b",
        r"\btrade\b", r"\bwealth\b", r"\bconsultation\b", r"\bexplanation\b"
    ]
}

ACTIONABLE_KEYWORDS = [
    r"counter \d+ (?:was )?closed",
    r"(?:broken|offline|out of order|not working) (?:atm|kiosk|printer)",
    r"waited (?:more than|over) \d+ (?:mins|minutes|hours)",
    r"rude (?:staff|teller|manager)",
    r"lunch break (?:delay|rush)",
    r"only 1 counter open"
]


class FeedbackSentimentAnalyzer:
    """
    Deterministic Rule-Based and Lexical NLP Customer Sentiment Analyzer.
    """

    def __init__(self):
        self.is_trained = True

    def analyze_sentiment(self, text: str, rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyzes customer review text:
        - Polarity score in [-1.0, 1.0]
        - Topic classification
        - Entity extraction (counter/staff codes)
        - Actionability flag for operations alarms
        """
        raw_text = str(text or "")
        clean_text = re.sub(r"[^\w\s]", " ", raw_text.lower())
        words = clean_text.split()

        pos_hits = [w for w in words if w in POSITIVE_WORDS]
        neg_hits = [w for w in words if w in NEGATIVE_WORDS]

        pos_count = len(pos_hits)
        neg_count = len(neg_hits)

        # Polarity score [-1.0, 1.0]
        if pos_count > neg_count:
            sentiment = "Positive"
            score = min(1.0, 0.35 + 0.15 * (pos_count - neg_count))
        elif neg_count > pos_count:
            sentiment = "Negative"
            score = max(-1.0, -0.35 - 0.15 * (neg_count - pos_count))
        else:
            if rating is not None:
                if rating >= 4:
                    sentiment = "Positive"
                    score = 0.5
                elif rating <= 2:
                    sentiment = "Negative"
                    score = -0.5
                else:
                    sentiment = "Neutral"
                    score = 0.0
            else:
                sentiment = "Neutral"
                score = 0.0

        # Topic detection
        matched_topics = []
        for topic, patterns in TOPIC_PATTERNS.items():
            for p in patterns:
                if re.search(p, clean_text):
                    matched_topics.append(topic)
                    break

        if not matched_topics:
            matched_topics.append("General Branch Experience")

        # Entity Extraction: Counter & Staff mentions
        counter_match = re.search(r"counter\s+(?:c_?)?(\d+)", clean_text)
        mentioned_counter = f"C_{int(counter_match.group(1)):02d}" if counter_match else None

        staff_match = re.search(r"(?:emp_?|teller\s+)(\d+)", clean_text)
        mentioned_staff = f"EMP_{int(staff_match.group(1)):03d}" if staff_match else None

        # Actionability detection
        is_actionable = False
        action_reason = None
        for kw_pattern in ACTIONABLE_KEYWORDS:
            m = re.search(kw_pattern, clean_text)
            if m:
                is_actionable = True
                action_reason = f"Detected operational complaint: '{m.group(0)}'"
                break

        if rating is not None and rating <= 2 and not is_actionable:
            is_actionable = True
            action_reason = f"Critical low customer rating ({rating}/5 stars)"

        return {
            "sentiment": sentiment,
            "sentiment_score": round(score, 2),
            "topics": matched_topics,
            "mentioned_counter": mentioned_counter,
            "mentioned_staff": mentioned_staff,
            "is_actionable": is_actionable,
            "action_reason": action_reason,
            "positive_keywords_found": pos_hits,
            "negative_keywords_found": neg_hits,
        }

    def aggregate_feedback_batch(self, feedback_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregates a batch of customer feedback records into branch-wide sentiment KPIs."""
        if not feedback_list:
            return {
                "total_reviews": 0,
                "net_sentiment_score": 0.0,
                "positive_pct": 0.0,
                "neutral_pct": 0.0,
                "negative_pct": 0.0,
                "actionable_alerts_count": 0,
                "top_friction_topics": [],
            }

        analyzed = []
        for f in feedback_list:
            text = f.get("feedback_text", "")
            rating = f.get("rating")
            analyzed.append(self.analyze_sentiment(text, rating))

        total = len(analyzed)
        pos = sum(1 for a in analyzed if a["sentiment"] == "Positive")
        neu = sum(1 for a in analyzed if a["sentiment"] == "Neutral")
        neg = sum(1 for a in analyzed if a["sentiment"] == "Negative")
        actionable = sum(1 for a in analyzed if a["is_actionable"])

        avg_score = float(sum(a["sentiment_score"] for a in analyzed) / total)

        # Count topics
        topic_counter: Counter = Counter()
        for a in analyzed:
            for t in a["topics"]:
                topic_counter[t] += 1

        top_topics = [
            {"topic": t, "count": count, "pct": round((count / total) * 100, 1)}
            for t, count in topic_counter.most_common(5)
        ]

        return {
            "total_reviews": total,
            "net_sentiment_score": round(avg_score, 2),
            "positive_pct": round((pos / total) * 100, 1),
            "neutral_pct": round((neu / total) * 100, 1),
            "negative_pct": round((neg / total) * 100, 1),
            "actionable_alerts_count": actionable,
            "top_friction_topics": top_topics,
        }
