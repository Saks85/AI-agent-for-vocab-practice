import tkinter as tk
from tkinter import ttk, messagebox
import json
import random
import os
import csv
import time
import numpy as np
from datetime import datetime
from collections import deque
import math

# File constants
PROGRESS_FILE = "vocab_progress.json"
DATASET_FILE = "english_spanish.csv"
SESSION_COUNTER_FILE = "session_counter.json"
AI_LOGS_FILE = "ai_learning_logs.json"
USER_MODEL_FILE = "user_model.json"

# Default Leitner schedule (will be personalized)
BASE_LEITNER_SCHEDULE = {
    1: 1,   # Review after 1 session
    2: 2,   # Review after 2 sessions  
    3: 4,   # Review after 4 sessions
    4: 7,   # Review after 7 sessions
    5: 15   # Review after 15 sessions
}

class PersonalizedLearningAgent:
    """AI agent that adapts to user's learning patterns"""
    
    def __init__(self):
        self.user_model = self.load_user_model()
        self.session_logs = self.load_session_logs()
        
        
    def load_user_model(self):
        """Load or initialize user's learning model"""
        if os.path.exists(USER_MODEL_FILE):
            try:
                with open(USER_MODEL_FILE, "r", encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "forgetting_curve_params": {"a": 0.9, "b": 1.2},  # Personal forgetting curve
            "optimal_session_sizes": [12, 16, 20],  # Preferred session sizes
            "fatigue_threshold": 0.7,  # Accuracy drop indicating fatigue
            "learning_style": "balanced",  # adaptive, aggressive, conservative
            "response_time_baseline": 3.0,  # Average response time in seconds
            "accuracy_trends": deque(maxlen=10),  # Last 10 sessions
            "forget_rates": {},  # Per-word forget patterns
            "confidence_level": 0.5,  # How confident the AI is in its predictions
        }
    
    def load_session_logs(self):
        """Load historical session data for learning"""
        if os.path.exists(AI_LOGS_FILE):
            try:
                with open(AI_LOGS_FILE, "r", encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_models(self):
        """Save AI models and logs"""
        try:
            with open(USER_MODEL_FILE, "w", encoding='utf-8') as f:
                # Convert deque to list for JSON serialization
                model_copy = self.user_model.copy()
                model_copy["accuracy_trends"] = list(self.user_model["accuracy_trends"])
                json.dump(model_copy, f, indent=2)
            
            with open(AI_LOGS_FILE, "w", encoding='utf-8') as f:
                json.dump(self.session_logs, f, indent=2)
        except Exception as e:
            print(f"Error saving AI models: {e}")
    
    def extract_features(self, progress_data, session_stats):
        """Extract features for decision making"""
        # Calculate recent accuracy trend
        if len(self.user_model["accuracy_trends"]) >= 3:
            recent_trend = np.mean(list(self.user_model["accuracy_trends"])[-3:])
        else:
            recent_trend = 0.75
        
        # Calculate average response time trend
        recent_logs = self.session_logs[-5:] if len(self.session_logs) >= 5 else self.session_logs
        avg_response_time = np.mean([log.get("avg_response_time", 3.0) for log in recent_logs]) if recent_logs else 3.0
        
        # Calculate fatigue indicator (accuracy drop within session)
        fatigue_score = 0
        if len(self.session_logs) > 0:
            last_session = self.session_logs[-1]
            if "word_accuracies" in last_session and len(last_session["word_accuracies"]) > 5:
                first_half = np.mean(last_session["word_accuracies"][:len(last_session["word_accuracies"])//2])
                second_half = np.mean(last_session["word_accuracies"][len(last_session["word_accuracies"])//2:])
                fatigue_score = max(0, first_half - second_half)  # Positive if accuracy dropped
        
        # Calculate forget rate
        total_reviews = sum(1 for stats in progress_data.values() if stats["attempts"] > 1)
        failed_reviews = sum(1 for stats in progress_data.values() 
                           if stats["attempts"] > 1 and stats["correct"]/stats["attempts"] < 0.8)
        forget_rate = failed_reviews / max(1, total_reviews)
        
        return {
            "recent_accuracy": recent_trend,
            "avg_response_time": avg_response_time,
            "fatigue_score": fatigue_score,
            "forget_rate": forget_rate,
            "session_count": len(self.session_logs),
            "time_since_last": self.get_time_since_last_session()
        }
    
    def get_time_since_last_session(self):
        """Get hours since last session"""
        if not self.session_logs:
            return 24  # Default to 24 hours
        
        last_session_time = self.session_logs[-1].get("timestamp", time.time() - 86400)
        hours_since = (time.time() - last_session_time) / 3600
        return min(hours_since, 168)  # Cap at 1 week
    
    def predict_optimal_session(self, features, progress_data):
        """Use AI to predict optimal session parameters"""
        # Simple decision tree logic (can be replaced with ML model)
        confidence_boost = min(0.3, self.user_model["confidence_level"] * 0.5)
        
        # Adjust session size based on performance and fatigue
        base_size = 15
        
        # Performance adjustment
        if features["recent_accuracy"] >= 0.85:
            size_multiplier = 1.3 + confidence_boost
            difficulty_bias = "challenging"
        elif features["recent_accuracy"] >= 0.70:
            size_multiplier = 1.0
            difficulty_bias = "balanced"
        else:
            size_multiplier = 0.7
            difficulty_bias = "review_heavy"
        
        # Fatigue adjustment
        if features["fatigue_score"] > self.user_model["fatigue_threshold"]:
            size_multiplier *= 0.8
            difficulty_bias = "easy"
        
        # Response time adjustment (if too slow, reduce cognitive load)
        if features["avg_response_time"] > self.user_model["response_time_baseline"] * 1.5:
            size_multiplier *= 0.9
        
        # Time since last session adjustment
        if features["time_since_last"] > 48:  # More than 2 days
            difficulty_bias = "review_heavy"
        elif features["time_since_last"] < 4:  # Less than 4 hours
            size_multiplier *= 0.8  # Don't overload
        
        optimal_size = int(base_size * size_multiplier)
        optimal_size = max(8, min(25, optimal_size))  # Clamp between 8-25
        
        return {
            "session_size": optimal_size,
            "difficulty_bias": difficulty_bias,
            "reasoning": self.generate_reasoning(features, optimal_size, difficulty_bias),
            "confidence": min(1.0, self.user_model["confidence_level"] + 0.1)
        }
    
    def generate_reasoning(self, features, size, bias):
        """Generate explanation for AI decisions"""
        reasons = []
        
        if features["recent_accuracy"] >= 0.85:
            reasons.append("You've been performing excellently, so I'm challenging you more")
        elif features["recent_accuracy"] < 0.65:
            reasons.append("Let's focus on reviewing familiar words to build confidence")
        
        if features["fatigue_score"] > 0.3:
            reasons.append("I noticed accuracy dropped in your last session, so taking it easier")
        
        if features["avg_response_time"] > 4:
            reasons.append("You've been taking time to think, so I'm reducing the session size")
        
        if features["time_since_last"] > 48:
            reasons.append("It's been a while since your last session, so including more review")
        
        if not reasons:
            reasons.append("Maintaining a balanced approach based on your progress")
        
        return f"Session size: {size} words. " + ". ".join(reasons) + "."
    
    def update_personal_schedule(self, word, correct, days_since_last):
        """Update personalized spaced repetition schedule"""
        if word not in self.user_model["forget_rates"]:
            self.user_model["forget_rates"][word] = []
        
        # Record this review outcome
        self.user_model["forget_rates"][word].append({
            "correct": correct,
            "days_since": days_since_last,
            "timestamp": time.time()
        })
        
        # Keep only last 10 reviews per word
        self.user_model["forget_rates"][word] = self.user_model["forget_rates"][word][-10:]
    
    def get_personalized_interval(self, word, box_level):
        """Get personalized review interval based on forgetting curve"""
        base_interval = BASE_LEITNER_SCHEDULE.get(box_level, 15)
        
        # If we don't have enough data, use base interval
        if word not in self.user_model["forget_rates"] or len(self.user_model["forget_rates"][word]) < 3:
            return base_interval
        
        # Calculate personal success rate for this word
        recent_reviews = self.user_model["forget_rates"][word][-5:]
        success_rate = sum(1 for r in recent_reviews if r["correct"]) / len(recent_reviews)
        
        # Adjust interval based on personal performance
        if success_rate >= 0.9:
            multiplier = 1.5  # Extend interval if consistently correct
        elif success_rate >= 0.7:
            multiplier = 1.0  # Keep standard interval
        else:
            multiplier = 0.6  # Shorten interval if struggling
        
        return max(1, int(base_interval * multiplier))
    
    def log_session_outcome(self, session_data):
        """Log session results for continuous learning"""
        log_entry = {
            "timestamp": time.time(),
            "session_number": session_data.get("session_number", 0),
            "total_words": session_data.get("total_words", 0),
            "new_words": session_data.get("new_words", 0),
            "accuracy": session_data.get("accuracy", 0),
            "avg_response_time": session_data.get("avg_response_time", 0),
            "word_accuracies": session_data.get("word_accuracies", []),
            "features_used": session_data.get("features_used", {}),
            "prediction_used": session_data.get("prediction_used", {}),
        }
        
        self.session_logs.append(log_entry)
        
        # Keep only last 50 sessions
        if len(self.session_logs) > 50:
            self.session_logs = self.session_logs[-50:]
        
        # Update accuracy trends
        if "accuracy" in session_data:
            self.user_model["accuracy_trends"].append(session_data["accuracy"])
        
        # Update confidence based on prediction accuracy
        if "prediction_accuracy" in session_data:
            if session_data["prediction_accuracy"] > 0.8:
                self.user_model["confidence_level"] = min(1.0, self.user_model["confidence_level"] + 0.05)
            else:
                self.user_model["confidence_level"] = max(0.1, self.user_model["confidence_level"] - 0.02)


class VocabularyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Enhanced Spanish Vocabulary Learning App")
        self.root.geometry("900x700")
        self.root.minsize(600, 400)

        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Initialize AI agent
        self.ai_agent = PersonalizedLearningAgent()

        self.vocab = []
        self.progress = {}
        self.session_counter = 0

        self.session_words = []
        self.current_word_index = 0
        self.current_word_data = None
        self.translation_shown = False
        self.quiz_options = []
        self.correct_answer = ""
        self.user_answered = False
        
        # Enhanced session tracking
        self.session_start_time = None
        self.word_start_time = None
        self.word_response_times = []
        self.word_accuracies = []

        self.session_stats = {
            "new_correct": 0,
            "new_total": 0,
            "review_correct": 0,
            "review_total": 0,
            "new_words": [],
            "response_times": [],
            "ai_prediction": None
        }

        try:
            self.load_data()
            self.setup_main_frame()
            self.show_welcome_page()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            root.quit()

    def load_data(self):
        """Load vocabulary, progress, and session counter"""
        if not os.path.exists(DATASET_FILE):
            raise FileNotFoundError(f"Dataset file '{DATASET_FILE}' not found.")

        # Load vocabulary
        with open(DATASET_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                english = (row.get("english") or row.get("English") or row.get("ENG") or row.get("en") or row.get("EN"))
                spanish = (row.get("spanish") or row.get("Spanish") or row.get("ESP") or row.get("es") or row.get("ES"))

                if english and spanish:
                    english = english.strip().lower()
                    spanish = spanish.strip().lower()
                    if english and spanish:
                        self.vocab.append({"english": english, "spanish": spanish})

        if not self.vocab:
            raise ValueError("No valid vocabulary pairs found.")

        # Load session counter
        if os.path.exists(SESSION_COUNTER_FILE):
            try:
                with open(SESSION_COUNTER_FILE, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.session_counter = data.get("session_counter", 0)
            except:
                self.session_counter = 0
        else:
            self.session_counter = 0

        # Load progress
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.progress = {}
                    for item in self.vocab:
                        word = item["english"]
                        if word in loaded:
                            self.progress[word] = loaded[word]
                        else:
                            self.progress[word] = {
                                "mastery": 0, 
                                "attempts": 0, 
                                "correct": 0,
                                "box": 0, 
                                "last_reviewed_session": 0,
                                "response_times": [],
                                "last_review_timestamp": 0
                            }
            except:
                self.progress = {item["english"]: {
                    "mastery": 0, "attempts": 0, "correct": 0,
                    "box": 0, "last_reviewed_session": 0,
                    "response_times": [], "last_review_timestamp": 0
                } for item in self.vocab}
        else:
            self.progress = {item["english"]: {
                "mastery": 0, "attempts": 0, "correct": 0,
                "box": 0, "last_reviewed_session": 0,
                "response_times": [], "last_review_timestamp": 0
            } for item in self.vocab}

    def save_progress(self):
        """Save progress, session counter, and AI models"""
        try:
            with open(PROGRESS_FILE, "w", encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
            
            with open(SESSION_COUNTER_FILE, "w", encoding='utf-8') as f:
                json.dump({"session_counter": self.session_counter}, f, indent=2)
                
            self.ai_agent.save_models()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save progress: {str(e)}")

    def count_due_words(self):
        """Count words that are due for review using AI-personalized intervals"""
        due_count = 0
        for word_data in self.vocab:
            word = word_data["english"]
            progress_data = self.progress[word]
            if progress_data["box"] > 0:  # Only words that have been learned before
                sessions_since_last_review = self.session_counter - progress_data["last_reviewed_session"]
                required_interval = self.ai_agent.get_personalized_interval(word, progress_data["box"])
                if sessions_since_last_review >= required_interval:
                    due_count += 1
        return due_count

    def get_due_words(self):
        """Get list of words that are due for review using AI scheduling"""
        due_words = []
        for word_data in self.vocab:
            word = word_data["english"]
            progress_data = self.progress[word]
            if progress_data["box"] > 0:  # Only words that have been learned before
                sessions_since_last_review = self.session_counter - progress_data["last_reviewed_session"]
                required_interval = self.ai_agent.get_personalized_interval(word, progress_data["box"])
                if sessions_since_last_review >= required_interval:
                    due_words.append(word_data)
        return due_words

    def show_welcome_page(self):
        """Show AI-enhanced welcome page with intelligent recommendations"""
        self.clear_content()
        due_count = self.count_due_words()
        
        # Get AI prediction for optimal session
        features = self.ai_agent.extract_features(self.progress, self.session_stats)
        ai_prediction = self.ai_agent.predict_optimal_session(features, self.progress)
        self.session_stats["ai_prediction"] = ai_prediction
        
        # Welcome title
        ttk.Label(self.content_frame, text="🤖 AI Spanish Vocabulary Trainer",
                  font=('Arial', 20, 'bold')).grid(row=0, column=0, pady=20)

        # Session counter info
        ttk.Label(self.content_frame, text=f"Session #{self.session_counter + 1}",
                  font=('Arial', 14)).grid(row=1, column=0, pady=5)

        # AI recommendation box
        ai_frame = ttk.LabelFrame(self.content_frame, text="🧠 AI Recommendation", padding="10")
        ai_frame.grid(row=2, column=0, pady=15, padx=20, sticky=(tk.W, tk.E))
        
        ttk.Label(ai_frame, text=ai_prediction["reasoning"],
                  font=('Arial', 12), wraplength=600, justify=tk.LEFT,
                  foreground='blue').pack(pady=5)
        
        confidence_text = f"Confidence: {ai_prediction['confidence']:.1%}"
        ttk.Label(ai_frame, text=confidence_text,
                  font=('Arial', 10), foreground='gray').pack()

        row = 3
        
        # Show revision option if there are words due
        if due_count >= 5:
            ttk.Label(self.content_frame, text=f"🔄 {due_count} words ready for review!",
                      font=('Arial', 14), foreground='orange').grid(row=row, column=0, pady=10)
            
            ttk.Button(self.content_frame, text="Start AI-Optimized Revision Session",
                       command=self.start_revision_session).grid(row=row+1, column=0, pady=5)
            
            ttk.Button(self.content_frame, text="Skip to New Learning Session",
                       command=self.start_new_session).grid(row=row+2, column=0, pady=5)
            row += 3
        else:
            if due_count > 0:
                ttk.Label(self.content_frame, text=f"{due_count} words due (need 5+ for revision session)",
                          font=('Arial', 12), foreground='gray').grid(row=row, column=0, pady=10)
                row += 1
            
            ttk.Button(self.content_frame, text="Start AI-Optimized Learning Session",
                       command=self.start_new_session).grid(row=row, column=0, pady=10)
            row += 1

        # Enhanced stats
        total_words = len(self.vocab)
        learned_words = sum(1 for stats in self.progress.values() if stats["attempts"] > 0)
        mastered_words = sum(1 for stats in self.progress.values() if stats["mastery"] >= 8)
        
        # Calculate recent performance if available
        recent_perf_text = ""
        if len(self.ai_agent.user_model["accuracy_trends"]) > 0:
            recent_acc = list(self.ai_agent.user_model["accuracy_trends"])[-1]
            recent_perf_text = f" | Recent accuracy: {recent_acc:.1%}"
        
        stats_text = f"Progress: {learned_words}/{total_words} words learned, {mastered_words} mastered{recent_perf_text}"
        ttk.Label(self.content_frame, text=stats_text,
                  font=('Arial', 11), foreground='darkblue').grid(row=row, column=0, pady=15)

    def start_revision_session(self):
        """Start AI-optimized revision session"""
        due_words = self.get_due_words()
        ai_prediction = self.session_stats.get("ai_prediction", {"session_size": 15})
        
        # Prioritize words based on AI insights
        due_words.sort(key=lambda w: (
            -self.progress[w["english"]]["mastery"],  # Lower mastery first
            self.progress[w["english"]]["last_reviewed_session"]  # Older reviews first
        ))
        
        max_words = min(ai_prediction["session_size"], len(due_words))
        self.session_words = due_words[:max_words]
        
        if not self.session_words:
            messagebox.showinfo("No Words", "No words are currently due for review.")
            self.show_welcome_page()
            return
            
        self.current_word_index = 0
        self.session_counter += 1
        self.session_start_time = time.time()
        self.show_flashcard()

    def start_new_session(self):
        """Start AI-optimized new learning session"""
        self.session_words = self.select_ai_session_words()
        self.current_word_index = 0
        if not self.session_words:
            self.show_no_words_message()
        else:
            self.session_counter += 1
            self.session_start_time = time.time()
            self.show_flashcard()

    def select_ai_session_words(self):
        """AI-powered word selection using learned patterns"""
        ai_prediction = self.session_stats.get("ai_prediction", {
            "session_size": 15,
            "difficulty_bias": "balanced"
        })
        
        max_session_size = ai_prediction["session_size"]
        difficulty_bias = ai_prediction["difficulty_bias"]

        # Categorize words with more nuanced criteria
        new_words = sorted(
            [w for w in self.vocab if self.progress[w["english"]]["attempts"] == 0],
            key=lambda x: len(x["english"])
        )
        
        struggling_words = [w for w in self.vocab 
                          if 0 < self.progress[w["english"]]["mastery"] <= 3
                          and self.progress[w["english"]]["attempts"] >= 2]
        
        progressing_words = [w for w in self.vocab 
                           if 4 <= self.progress[w["english"]]["mastery"] <= 6]
        
        strong_words = [w for w in self.vocab 
                       if self.progress[w["english"]]["mastery"] >= 7]

        # AI-driven proportions based on difficulty bias
        if difficulty_bias == "challenging":
            proportions = {"new": 0.5, "struggling": 0.2, "progressing": 0.25, "strong": 0.05}
        elif difficulty_bias == "review_heavy":
            proportions = {"new": 0.2, "struggling": 0.5, "progressing": 0.25, "strong": 0.05}
        elif difficulty_bias == "easy":
            proportions = {"new": 0.3, "struggling": 0.3, "progressing": 0.3, "strong": 0.1}
        else:  # balanced
            proportions = {"new": 0.4, "struggling": 0.3, "progressing": 0.25, "strong": 0.05}

        # Calculate target counts
        target_counts = {
            "new": int(max_session_size * proportions["new"]),
            "struggling": int(max_session_size * proportions["struggling"]),
            "progressing": int(max_session_size * proportions["progressing"]),
            "strong": int(max_session_size * proportions["strong"])
        }

        # Select words
        random.shuffle(struggling_words)
        random.shuffle(progressing_words)
        random.shuffle(strong_words)
        
        selected_new = new_words[:target_counts["new"]]
        selected_struggling = struggling_words[:target_counts["struggling"]]
        selected_progressing = progressing_words[:target_counts["progressing"]]
        selected_strong = strong_words[:target_counts["strong"]]

        # Fill remaining slots
        all_selected = selected_new + selected_struggling + selected_progressing + selected_strong
        if len(all_selected) < max_session_size:
            remaining = max_session_size - len(all_selected)
            extra_pool = (new_words[len(selected_new):] + 
                         struggling_words[len(selected_struggling):] +
                         progressing_words[len(selected_progressing):])
            random.shuffle(extra_pool)
            all_selected.extend(extra_pool[:remaining])

        random.shuffle(all_selected)
        self.session_stats["new_words"] = selected_new
        
        return all_selected

    def setup_main_frame(self):
        """Setup the main GUI frame"""
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        self.title_label = ttk.Label(self.main_frame, text="🤖 AI Spanish Vocabulary Learning",
                                     font=('Arial', 24, 'bold'))
        self.title_label.grid(row=0, column=0, pady=(0, 20))

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

    def show_flashcard(self):
        """Show flashcard with response time tracking"""
        self.clear_content()
        self.translation_shown = False
        self.current_word_data = self.session_words[self.current_word_index]
        self.word_start_time = time.time()  # Start timing

        # Check if this is a new word
        is_new_word = self.progress[self.current_word_data["english"]]["attempts"] == 0

        if not is_new_word:
            self.show_quiz()
            return

        # Show flashcard for new words
        progress_label = ttk.Label(self.content_frame,
                                text=f"Word {self.current_word_index + 1} of {len(self.session_words)}",
                                font=('Arial', 12))
        progress_label.grid(row=0, column=0, pady=(0, 30))

        english_label = ttk.Label(self.content_frame,
                                text=f"English: {self.current_word_data['english'].title()}",
                                font=('Arial', 24, 'bold'))
        english_label.grid(row=1, column=0, pady=20)

        self.spanish_label = ttk.Label(self.content_frame, text="", font=('Arial', 24, 'bold'), foreground='blue')
        self.spanish_label.grid(row=2, column=0, pady=20)

        self.instruction_label = ttk.Label(self.content_frame,
                                        text="Think of the Spanish translation, then click 'Show Translation'",
                                        font=('Arial', 14))
        self.instruction_label.grid(row=3, column=0, pady=30)

        self.show_translation_btn = ttk.Button(self.content_frame, text="Show Translation",
                                            command=self.show_translation)
        self.show_translation_btn.grid(row=4, column=0, pady=10)
        self.show_translation_btn.focus()

    def show_translation(self):
        """Show translation and continue timing"""
        if not self.translation_shown:
            self.spanish_label.config(text=f"Spanish: {self.current_word_data['spanish'].title()}")
            self.instruction_label.config(text="Study it, then click 'Next' to take the quiz")
            self.show_translation_btn.config(text="Next → Quiz", command=self.show_quiz)
            self.translation_shown = True

    def show_quiz(self):
        """Show quiz with enhanced timing and accuracy tracking"""
        self.clear_content()
        self.user_answered = False
        self.current_word_data = self.session_words[self.current_word_index]
        self.correct_answer = self.current_word_data["spanish"]
        
        # Reset timing for quiz phase
        if not hasattr(self, 'word_start_time') or self.word_start_time is None:
            self.word_start_time = time.time()

        # Progress indicator
        progress_label = ttk.Label(self.content_frame,
                                text=f"Quiz: Word {self.current_word_index + 1} of {len(self.session_words)}",
                                font=('Arial', 12))
        progress_label.grid(row=0, column=0, pady=(0, 20))

        # Question
        question_label = ttk.Label(self.content_frame,
                          text=f"What is the Spanish translation of '{self.current_word_data['english'].title()}'?",
                          font=('Arial', 16, 'bold'), wraplength=600)
        question_label.grid(row=1, column=0, pady=20)

        # Generate options
        self.quiz_options = [self.correct_answer]
        attempts = 0
        while len(self.quiz_options) < 4 and attempts < 20:
            candidate = random.choice(self.vocab)["spanish"]
            if candidate not in self.quiz_options:
                self.quiz_options.append(candidate)
            attempts += 1

        random.shuffle(self.quiz_options)
        self.option_buttons = []

        # Create option buttons
        for i, opt in enumerate(self.quiz_options):
            btn = ttk.Button(self.content_frame, text=f"{i + 1}. {opt.title()}",
                             command=lambda val=opt: self.check_answer(val), width=40)
            btn.grid(row=2 + i, column=0, pady=5, padx=20, sticky=(tk.W, tk.E))
            self.option_buttons.append(btn)

    def check_answer(self, selected):
        """Enhanced answer checking with detailed tracking"""
        if self.user_answered:
            return
        
        self.user_answered = True
        correct = selected == self.correct_answer
        word = self.current_word_data["english"]
        
        # Calculate response time
        response_time = time.time() - self.word_start_time if self.word_start_time else 0
        self.word_response_times.append(response_time)
        self.word_accuracies.append(1 if correct else 0)
        
        # Update session stats
        if self.progress[word]["attempts"] == 0:
            self.session_stats["new_total"] += 1
            if correct:
                self.session_stats["new_correct"] += 1
        else:
            self.session_stats["review_total"] += 1
            if correct:
                self.session_stats["review_correct"] += 1

        self.session_stats["response_times"].append(response_time)

        # Update progress with enhanced tracking
        self.update_progress_enhanced(word, correct, response_time)

        # Update button styles
        for btn, opt in zip(self.option_buttons, self.quiz_options):
            if opt == self.correct_answer:
                btn.configure(style='Correct.TButton')
            elif opt == selected and not correct:
                btn.configure(style='Wrong.TButton')
            btn.configure(state='disabled')

        # Configure styles
        self.style.configure('Correct.TButton', background='lightgreen')
        self.style.configure('Wrong.TButton', background='lightcoral')

        # Show result with response time
        if correct:
            result_msg = f"¡Correcto! (Correct!) - {response_time:.1f}s"
            if response_time < 2:
                result_msg += " ⚡ Fast!"
            elif response_time > 5:
                result_msg += " 🐢 Take your time to think"
        else:
            result_msg = f"Incorrecto. The correct answer is '{self.correct_answer}' - {response_time:.1f}s"
        
        result_color = "green" if correct else "red"
        result_label = ttk.Label(self.content_frame, text=result_msg,
                           font=('Arial', 14, 'bold'), foreground=result_color)
        result_label.grid(row=7, column=0, pady=20)

        # Next button
        next_btn = ttk.Button(self.content_frame, text="Next", command=self.next_word)
        next_btn.grid(row=8, column=0, pady=10)
        next_btn.focus()

    def update_progress_enhanced(self, word, correct, response_time):
        """Enhanced progress update with AI learning integration"""
        entry = self.progress[word]
        entry["attempts"] += 1
        entry["last_reviewed_session"] = self.session_counter
        entry["last_review_timestamp"] = time.time()
        
        # Track response times
        if "response_times" not in entry:
            entry["response_times"] = []
        entry["response_times"].append(response_time)
        entry["response_times"] = entry["response_times"][-10:]  # Keep last 10
        
        if correct:
            entry["correct"] += 1
            entry["mastery"] = min(10, entry["mastery"] + 1)
            entry["box"] = min(5, entry["box"] + 1)
        else:
            entry["mastery"] = max(0, entry["mastery"] - 1)
            entry["box"] = max(1, entry["box"] - 1) if entry["box"] > 0 else 1

        # Update AI agent's personal learning data
        days_since_last = max(0.1, (time.time() - entry.get("last_review_timestamp", time.time())) / 86400)
        self.ai_agent.update_personal_schedule(word, correct, days_since_last)

    def next_word(self):
        """Move to next word or end session"""
        self.current_word_index += 1
        if self.current_word_index < len(self.session_words):
            self.show_flashcard()
        else:
            self.show_session_summary()

    def show_session_summary(self):
        """Enhanced session summary with AI insights"""
        self.clear_content()
        self.save_progress()

        # Calculate session metrics
        total_time = time.time() - self.session_start_time if self.session_start_time else 0
        avg_response_time = np.mean(self.word_response_times) if self.word_response_times else 0
        session_accuracy = np.mean(self.word_accuracies) if self.word_accuracies else 0

        # Log session data for AI learning
        session_data = {
            "session_number": self.session_counter,
            "total_words": len(self.session_words),
            "new_words": len(self.session_stats["new_words"]),
            "accuracy": session_accuracy,
            "avg_response_time": avg_response_time,
            "word_accuracies": self.word_accuracies,
            "features_used": self.ai_agent.extract_features(self.progress, self.session_stats),
            "prediction_used": self.session_stats.get("ai_prediction", {}),
            "total_time": total_time
        }
        
        # Calculate prediction accuracy (how well AI predicted performance)
        predicted_difficulty = self.session_stats.get("ai_prediction", {}).get("difficulty_bias", "balanced")
        if predicted_difficulty == "challenging" and session_accuracy >= 0.8:
            prediction_accuracy = 1.0
        elif predicted_difficulty == "easy" and session_accuracy >= 0.9:
            prediction_accuracy = 1.0
        elif predicted_difficulty == "balanced" and 0.7 <= session_accuracy <= 0.9:
            prediction_accuracy = 1.0
        else:
            prediction_accuracy = max(0, 1 - abs(session_accuracy - 0.8))
        
        session_data["prediction_accuracy"] = prediction_accuracy
        
        self.ai_agent.log_session_outcome(session_data)

        # Title
        ttk.Label(self.content_frame, text=f"🎯 Session #{self.session_counter} Complete!",
                  font=('Arial', 24, 'bold')).grid(row=0, column=0, pady=20)

        # AI Performance Analysis
        ai_frame = ttk.LabelFrame(self.content_frame, text="🤖 AI Analysis", padding="10")
        ai_frame.grid(row=1, column=0, pady=15, padx=20, sticky=(tk.W, tk.E))
        
        ai_feedback = self.generate_ai_feedback(session_data, prediction_accuracy)
        ttk.Label(ai_frame, text=ai_feedback,
                  font=('Arial', 12), wraplength=700, justify=tk.LEFT,
                  foreground='darkgreen').pack(pady=5)

        # Enhanced Results
        results_frame = ttk.Frame(self.content_frame)
        results_frame.grid(row=2, column=0, pady=10)

        row = 0
        
        # Overall session stats
        ttk.Label(results_frame,
                  text=f"📊 Overall: {len([a for a in self.word_accuracies if a])}/{len(self.word_accuracies)} correct ({session_accuracy:.1%})",
                  font=('Arial', 14, 'bold')).grid(row=row, column=0, pady=5)
        row += 1
        
        # Time stats
        ttk.Label(results_frame,
                  text=f"⏱️ Avg response time: {avg_response_time:.1f}s | Total time: {total_time/60:.1f} min",
                  font=('Arial', 12)).grid(row=row, column=0, pady=5)
        row += 1

        # New words results
        if self.session_stats["new_total"]:
            acc = self.session_stats["new_correct"] / self.session_stats["new_total"] * 100
            ttk.Label(results_frame,
                      text=f"🆕 New Words: {self.session_stats['new_correct']}/{self.session_stats['new_total']} ({acc:.1f}%)",
                      font=('Arial', 14)).grid(row=row, column=0, pady=5)
            row += 1

        # Review words results
        if self.session_stats["review_total"]:
            acc = self.session_stats["review_correct"] / self.session_stats["review_total"] * 100
            ttk.Label(results_frame,
                      text=f"🔄 Review Words: {self.session_stats['review_correct']}/{self.session_stats['review_total']} ({acc:.1f}%)",
                      font=('Arial', 14)).grid(row=row, column=0, pady=5)
            row += 1

        # Show new words introduced
        if self.session_stats["new_words"]:
            row += 1
            ttk.Label(results_frame, text="📚 New Words Introduced:",
                      font=('Arial', 13, 'bold')).grid(row=row, column=0, pady=(15, 5))
            for idx, word in enumerate(self.session_stats["new_words"][:8], start=1):  # Show max 8
                ttk.Label(results_frame,
                          text=f"{idx}. {word['english'].title()} → {word['spanish'].title()}",
                          font=('Arial', 12)).grid(row=row + idx, column=0, sticky=tk.W)
            
            if len(self.session_stats["new_words"]) > 8:
                ttk.Label(results_frame,
                          text=f"... and {len(self.session_stats['new_words']) - 8} more",
                          font=('Arial', 10), foreground='gray').grid(row=row + 9, column=0, sticky=tk.W)

        # Action buttons
        button_frame = ttk.Frame(self.content_frame)
        button_frame.grid(row=3, column=0, pady=30)
        
        ttk.Button(button_frame, text="🚀 New AI Session", 
                  command=self.restart_session).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="📊 View Progress", 
                  command=self.show_detailed_progress).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="❌ Quit", 
                  command=self.root.quit).grid(row=0, column=2, padx=10)

    def generate_ai_feedback(self, session_data, prediction_accuracy):
        """Generate personalized AI feedback based on session performance"""
        accuracy = session_data["accuracy"]
        avg_time = session_data["avg_response_time"]
        prediction_used = session_data.get("prediction_used", {})
        
        feedback_parts = []
        
        # Performance feedback
        if accuracy >= 0.9:
            feedback_parts.append("Outstanding performance! 🌟")
        elif accuracy >= 0.8:
            feedback_parts.append("Great job! You're making excellent progress! 💪")
        elif accuracy >= 0.7:
            feedback_parts.append("Good work! You're building solid foundations. 👍")
        else:
            feedback_parts.append("Keep practicing! Every session makes you stronger. 🌱")
        
        # Response time feedback
        baseline = self.ai_agent.user_model.get("response_time_baseline", 3.0)
        if avg_time < baseline * 0.7:
            feedback_parts.append("Your response speed is impressive!")
        elif avg_time > baseline * 1.5:
            feedback_parts.append("Take your time - understanding is more important than speed.")
        
        # AI prediction feedback
        if prediction_accuracy > 0.8:
            feedback_parts.append("My session planning was spot-on for you today.")
            # Increase confidence
        elif prediction_accuracy < 0.5:
            feedback_parts.append("I'm adjusting my approach based on today's session.")
        
        # Adaptive suggestions
        confidence = self.ai_agent.user_model.get("confidence_level", 0.5)
        if confidence > 0.8:
            feedback_parts.append("I'm getting better at understanding your learning style!")
        
        return " ".join(feedback_parts)

    def show_detailed_progress(self):
        """Show detailed progress analytics"""
        self.clear_content()
        
        ttk.Label(self.content_frame, text="📈 Your Learning Analytics",
                  font=('Arial', 20, 'bold')).grid(row=0, column=0, pady=20)
        
        # Create scrollable frame
        canvas = tk.Canvas(self.content_frame, height=400)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Progress statistics
        total_words = len(self.vocab)
        attempted_words = [word for word, stats in self.progress.items() if stats["attempts"] > 0]
        mastery_levels = {
            "Beginner (1-3)": len([w for w in attempted_words if 1 <= self.progress[w]["mastery"] <= 3]),
            "Intermediate (4-6)": len([w for w in attempted_words if 4 <= self.progress[w]["mastery"] <= 6]),
            "Advanced (7-10)": len([w for w in attempted_words if 7 <= self.progress[w]["mastery"] <= 10])
        }
        
        # AI model stats
        ai_stats_frame = ttk.LabelFrame(scrollable_frame, text="🤖 AI Learning Model", padding="10")
        ai_stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        confidence = self.ai_agent.user_model.get("confidence_level", 0.5)
        ttk.Label(ai_stats_frame, text=f"AI Confidence Level: {confidence:.1%}",
                  font=('Arial', 12)).pack(anchor=tk.W)
        
        if len(self.ai_agent.user_model["accuracy_trends"]) > 0:
            recent_trends = list(self.ai_agent.user_model["accuracy_trends"])
            trend_text = f"Recent accuracy trend: {', '.join([f'{t:.1%}' for t in recent_trends[-5:]])}"
            ttk.Label(ai_stats_frame, text=trend_text,
                      font=('Arial', 12)).pack(anchor=tk.W)
        
        # Mastery distribution
        mastery_frame = ttk.LabelFrame(scrollable_frame, text="📊 Mastery Distribution", padding="10")
        mastery_frame.pack(fill=tk.X, padx=20, pady=10)
        
        for level, count in mastery_levels.items():
            percentage = count / max(1, len(attempted_words)) * 100
            ttk.Label(mastery_frame, text=f"{level}: {count} words ({percentage:.1f}%)",
                      font=('Arial', 12)).pack(anchor=tk.W)
        
        # Session history
        if len(self.ai_agent.session_logs) > 0:
            history_frame = ttk.LabelFrame(scrollable_frame, text="📚 Recent Sessions", padding="10")
            history_frame.pack(fill=tk.X, padx=20, pady=10)
            
            recent_sessions = self.ai_agent.session_logs[-5:]  # Last 5 sessions
            for i, session in enumerate(reversed(recent_sessions)):
                session_num = session.get("session_number", i+1)
                accuracy = session.get("accuracy", 0)
                words_count = session.get("total_words", 0)
                avg_time = session.get("avg_response_time", 0)
                
                session_text = f"Session #{session_num}: {accuracy:.1%} accuracy, {words_count} words, {avg_time:.1f}s avg"
                ttk.Label(history_frame, text=session_text,
                          font=('Arial', 11)).pack(anchor=tk.W)
        
        # Back button
        ttk.Button(scrollable_frame, text="← Back to Menu",
                  command=self.show_welcome_page).pack(pady=20)

    def restart_session(self):
        """Restart with a new AI-optimized session"""
        # Reset session stats
        self.session_stats = {
            "new_correct": 0,
            "new_total": 0,
            "review_correct": 0,
            "review_total": 0,
            "new_words": [],
            "response_times": [],
            "ai_prediction": None
        }
        self.current_word_index = 0
        self.word_response_times = []
        self.word_accuracies = []
        self.show_welcome_page()

    def show_no_words_message(self):
        """Show message when no words are available"""
        self.clear_content()
        ttk.Label(self.content_frame, text="🎉 Congratulations! No words available for learning.",
                  font=('Arial', 16)).grid(row=0, column=0, pady=50)
        ttk.Label(self.content_frame, text="You've mastered all available vocabulary!",
                  font=('Arial', 14), foreground='green').grid(row=1, column=0, pady=10)
        ttk.Button(self.content_frame, text="View Progress", 
                  command=self.show_detailed_progress).grid(row=2, column=0, pady=10)
        ttk.Button(self.content_frame, text="Quit", 
                  command=self.root.quit).grid(row=3, column=0, pady=10)

    def clear_content(self):
        """Clear the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()


def main():
    root = tk.Tk()
    app = VocabularyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
