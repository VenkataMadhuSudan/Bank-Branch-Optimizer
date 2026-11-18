"""
NLP Customer Feedback & Sentiment Root-Cause Engine.
Analyzes customer reviews, detects friction topics, calculates sentiment polarity,
and links customer feedback to staff members and counter terminals.
"""
import re
from collections import Counter
import polars as pl

POSITIVE_WORDS = {
    "fast", "quick", "helpful", "excellent", "smooth", "great", "easy", "effortless",
    "polite", "friendly", "satisfied", "prompt", "efficient", "professional", "clear",
    "wonderful", "delighted", "superb", "courteous", "impressed", "kind"
}

NEGATIVE_WORDS = {
    "waited", "waiting", "long", "slow", "terrible", "crowd", "overwhelmed", "delay",
    "frustrated", "shortage", "poor", "confusing", "horrible", "awful", "rude",
    "stuck", "useless", "broken", "angry", "tired", "ignored", "waste", "disappointed"
}

TOPIC_PATTERNS = {
    "Excessive Wait Time / Bottleneck": [
        r"wait", r"long queue", r"delay", r"minutes", r"hours", r"crowd", r"slow", r"line"
    ],
    "Staff / Counter Shortage": [
        r"counter", r"staff", r"shortage", r"only \d counter", r"lunch hour", r"teller",
        r"overwhelmed", r"understaffed", r"closed counter"
    ],
    "Digital Kiosk & Deflection Opportunity": [
        r"kiosk", r"atm", r"app", r"mobile", r"passbook", r"online", r"statement",
        r"video kyc", r"self[- ]service", r"cheque drop"
    ],
    "Fast & Courteous Service Quality": [
        r"helpful", r"polite", r"quick turnaround", r"friendly", r"great support",
        r"smooth", r"prompt", r"efficient", r"satisfied"
    ],
    "Specialist Advisory & Loan Quality": [
        r"loan", r"mortgage", r"advisor", r"forex", r"investment", r"trade", r"wealth",
        r"explanation", r"consultation"
    ]
}

class FeedbackSentimentAnalyzer:
    def __init__(self):
        self.is_trained = True

    def analyze_sentiment(self, text: str, rating: int = None) -> dict:
        """Rule & Lexicon based sentiment scoring with topic attribution and staff recognition."""
        raw_text = str(text)
        clean_text = re.sub(r"[^\w\s]", " ", raw_text.lower())
        words = clean_text.split()
        
        pos_hits = [w for w in words if w in POSITIVE_WORDS]
        neg_hits = [w for w in words if w in NEGATIVE_WORDS]
        
        pos_count = len(pos_hits)
        neg_count = len(neg_hits)
        
        # Calculate continuous polarity score [-1.0, 1.0]
        if pos_count > neg_count:
            sentiment = "Positive"
            score = min(1.0, 0.4 + 0.15 * (pos_count - neg_count))
        elif neg_count > pos_count:
            sentiment = "Negative"
            score = max(-1.0, -0.4 - 0.15 * (neg_count - pos_count))
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

        # Staff / Counter recognition in text
        counter_match = re.search(r"counter\s+(c_?\d+|[0-9]+)", clean_text)
        mentioned_counter = counter_match.group(0).upper() if counter_match else None

        return {
            "sentiment": sentiment,
            "sentiment_score": round(score, 2),
            "topics": matched_topics,
            "mentioned_counter": mentioned_counter,
            "positive_keywords": pos_hits,
            "friction_keywords": neg_hits
        }

    def process_feedback_batch(self, feedback_records: list) -> list:
        """Processes list of feedback records with sentiments, topics, and counter attributions."""
        results = []
        for r in feedback_records:
            rating = r.get("rating")
            text = r.get("feedback_text", "")
            res = self.analyze_sentiment(text, rating=rating)
            
            r_copy = dict(r)
            r_copy["sentiment_label"] = res["sentiment"]
            r_copy["sentiment_polarity"] = res["sentiment_score"]
            r_copy["detected_topics"] = "; ".join(res["topics"])
            r_copy["mentioned_counter"] = res["mentioned_counter"]
            results.append(r_copy)
        return results

    def get_insights_summary(self, feedback_processed: list) -> dict:
        """Aggregates topic frequencies, pain points, and staff compliments."""
        if not feedback_processed:
            return {
                "sentiment_distribution": {"Positive": 0, "Negative": 0, "Neutral": 0},
                "overall_top_topics": {},
                "key_pain_points": {},
                "total_reviews": 0,
                "avg_sentiment_polarity": 0.0,
                "counter_feedback_leaderboard": {}
            }
            
        all_topics = []
        sentiments = []
        polarities = []
        neg_topics = []
        counter_mentions = {}
        
        for r in feedback_processed:
            sentiments.append(r["sentiment_label"])
            polarities.append(r["sentiment_polarity"])
            
            topics = [t.strip() for t in str(r.get("detected_topics", "")).split(";") if t.strip()]
            all_topics.extend(topics)
            
            if r["sentiment_label"] == "Negative":
                neg_topics.extend(topics)
                
            cnt = r.get("mentioned_counter")
            if cnt:
                if cnt not in counter_mentions:
                    counter_mentions[cnt] = {"praise": 0, "complaints": 0}
                if r["sentiment_label"] == "Positive":
                    counter_mentions[cnt]["praise"] += 1
                elif r["sentiment_label"] == "Negative":
                    counter_mentions[cnt]["complaints"] += 1
                
        topic_counts = dict(Counter(all_topics).most_common(5))
        sentiment_dist = dict(Counter(sentiments))
        pain_points = dict(Counter(neg_topics).most_common(4))

        return {
            "sentiment_distribution": sentiment_dist,
            "overall_top_topics": topic_counts,
            "key_pain_points": pain_points,
            "total_reviews": len(feedback_processed),
            "avg_sentiment_polarity": round(sum(polarities) / max(1, len(polarities)), 2),
            "counter_feedback_leaderboard": counter_mentions
        }
