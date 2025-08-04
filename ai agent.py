import tkinter as tk
from tkinter import ttk, messagebox
import json
import random
import os
import csv

PROGRESS_FILE = "vocab_progress.json"
DATASET_FILE = "english_spanish.csv"
SESSION_COUNTER_FILE = "session_counter.json"

# Leitner system based on number of sessions instead of days
LEITNER_SCHEDULE = {
    1: 1,   # Review after 1 session
    2: 2,   # Review after 2 sessions  
    3: 4,   # Review after 4 sessions
    4: 7,   # Review after 7 sessions
    5: 15   # Review after 15 sessions
}


class VocabularyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Spanish Vocabulary Learning App")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        self.style = ttk.Style()
        self.style.theme_use('clam')

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

        self.session_stats = {
            "new_correct": 0,
            "new_total": 0,
            "review_correct": 0,
            "review_total": 0,
            "new_words": []
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
                                "last_reviewed_session": 0
                            }
            except:
                self.progress = {item["english"]: {
                    "mastery": 0, "attempts": 0, "correct": 0,
                    "box": 0, "last_reviewed_session": 0
                } for item in self.vocab}
        else:
            self.progress = {item["english"]: {
                "mastery": 0, "attempts": 0, "correct": 0,
                "box": 0, "last_reviewed_session": 0
            } for item in self.vocab}

    def save_progress(self):
        """Save progress and session counter"""
        try:
            with open(PROGRESS_FILE, "w", encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
            
            with open(SESSION_COUNTER_FILE, "w", encoding='utf-8') as f:
                json.dump({"session_counter": self.session_counter}, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save progress: {str(e)}")
    
    def count_due_words(self):
        """Count words that are due for review based on session intervals"""
        due_count = 0
        for word, data in self.progress.items():
            if data["box"] > 0:  # Only words that have been learned before
                sessions_since_last_review = self.session_counter - data["last_reviewed_session"]
                required_interval = LEITNER_SCHEDULE.get(data["box"], 15)
                if sessions_since_last_review >= required_interval:
                    due_count += 1
        return due_count

    def get_due_words(self):
        """Get list of words that are due for review"""
        due_words = []
        for word_data in self.vocab:
            word = word_data["english"]
            progress_data = self.progress[word]
            if progress_data["box"] > 0:  # Only words that have been learned before
                sessions_since_last_review = self.session_counter - progress_data["last_reviewed_session"]
                required_interval = LEITNER_SCHEDULE.get(progress_data["box"], 15)
                if sessions_since_last_review >= required_interval:
                    due_words.append(word_data)
        return due_words

    def show_welcome_page(self):
        """Show welcome page with intelligent session recommendation"""
        self.clear_content()
        due_count = self.count_due_words()
        
        # Welcome title
        ttk.Label(self.content_frame, text="Welcome to Spanish Vocabulary Trainer!",
                  font=('Arial', 20, 'bold')).grid(row=0, column=0, pady=20)

        # Session counter info
        ttk.Label(self.content_frame, text=f"Session #{self.session_counter + 1}",
                  font=('Arial', 14)).grid(row=1, column=0, pady=5)

        row = 2
        
        # Show revision option only if there are enough words (minimum 5) due for review
        if due_count >= 5:
            ttk.Label(self.content_frame, text=f"🔄 You have {due_count} words due for review!",
                      font=('Arial', 14), foreground='orange').grid(row=row, column=0, pady=10)
            
            ttk.Button(self.content_frame, text="Start Revision Session",
                       command=self.start_revision_session).grid(row=row+1, column=0, pady=5)
            
            ttk.Button(self.content_frame, text="Skip to New Learning Session",
                       command=self.start_new_session).grid(row=row+2, column=0, pady=5)
            row += 3
        else:
            if due_count > 0:
                ttk.Label(self.content_frame, text=f"You have {due_count} words due for review (need 5+ for revision session)",
                          font=('Arial', 12), foreground='gray').grid(row=row, column=0, pady=10)
                row += 1
            else:
                ttk.Label(self.content_frame, text="No words currently due for review",
                          font=('Arial', 12), foreground='gray').grid(row=row, column=0, pady=10)
                row += 1
            
            ttk.Button(self.content_frame, text="Start Learning Session",
                       command=self.start_new_session).grid(row=row, column=0, pady=10)
            row += 1

        # Show some stats
        total_words = len(self.vocab)
        learned_words = sum(1 for stats in self.progress.values() if stats["attempts"] > 0)
        mastered_words = sum(1 for stats in self.progress.values() if stats["mastery"] >= 8)
        
        stats_text = f"Progress: {learned_words}/{total_words} words learned, {mastered_words} mastered"
        ttk.Label(self.content_frame, text=stats_text,
                  font=('Arial', 11), foreground='blue').grid(row=row, column=0, pady=15)

    def start_revision_session(self):
        """Start a revision session with due words"""
        due_words = self.get_due_words()
        # Select up to 20 words for revision, prioritizing older reviews
        due_words.sort(key=lambda w: self.progress[w["english"]]["last_reviewed_session"])
        self.session_words = due_words[:min(20, len(due_words))]
        
        if not self.session_words:
            messagebox.showinfo("No Words", "No words are currently due for review.")
            self.show_welcome_page()
            return
            
        self.current_word_index = 0
        self.session_counter += 1  # Increment session counter
        self.show_flashcard()

    def start_new_session(self):
        """Start a new learning session"""
        self.session_words = self.select_session_words()
        self.current_word_index = 0
        if not self.session_words:
            self.show_no_words_message()
        else:
            self.session_counter += 1  # Increment session counter
            self.show_flashcard()

    def select_session_words(self):
        """Select words for a learning session with better distribution"""
        # Get words by category
        new_words = sorted(
            [w for w in self.vocab if self.progress[w["english"]]["attempts"] == 0],
            key=lambda x: len(x["english"])
        )
        low_mastery = [w for w in self.vocab if 0 < self.progress[w["english"]]["mastery"] <= 2]
        mid_mastery = [w for w in self.vocab if 3 <= self.progress[w["english"]]["mastery"] <= 6]
        high_mastery = [w for w in self.vocab if self.progress[w["english"]]["mastery"] >= 7]

        # Shuffle for variety
        random.shuffle(low_mastery)
        random.shuffle(mid_mastery)
        random.shuffle(high_mastery)

        # Select words with better balance
        selected_new = new_words[:3]  # Focus more on new words
        selected_low = low_mastery[:4]
        selected_mid = mid_mastery[:2]
        selected_high = high_mastery[:1] if random.random() < 0.3 else []  # Less frequent high mastery

        session = selected_new + selected_low + selected_mid + selected_high
        random.shuffle(session)

        # Save new words for summary
        self.session_stats["new_words"] = selected_new

        return session

    def setup_main_frame(self):
        """Setup the main GUI frame"""
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        self.title_label = ttk.Label(self.main_frame, text="Spanish Vocabulary Learning",
                                     font=('Arial', 24, 'bold'))
        self.title_label.grid(row=0, column=0, pady=(0, 20))

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

    def show_flashcard(self):
        """Show flashcard for learning (new words) or go directly to quiz (review words)"""
        self.clear_content()
        self.translation_shown = False
        self.current_word_data = self.session_words[self.current_word_index]

        # Check if this is a new word (no prior attempts)
        is_new_word = self.progress[self.current_word_data["english"]]["attempts"] == 0

        if not is_new_word:
            # If it's a review word, skip flashcard and go directly to quiz
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
        """Show the translation and prepare for quiz"""
        if not self.translation_shown:
            self.spanish_label.config(text=f"Spanish: {self.current_word_data['spanish'].title()}")
            self.instruction_label.config(text="Study it, then click 'Next' to take the quiz")
            self.show_translation_btn.config(text="Next → Quiz", command=self.show_quiz)
            self.translation_shown = True

    def show_quiz(self):
        """Show quiz for the current word"""
        self.clear_content()
        self.user_answered = False
        self.current_word_data = self.session_words[self.current_word_index]
        self.correct_answer = self.current_word_data["spanish"]

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
        """Check the selected answer and provide feedback"""
        if self.user_answered:
            return
        
        self.user_answered = True
        correct = selected == self.correct_answer
        word = self.current_word_data["english"]

        # Update session stats
        if self.progress[word]["attempts"] == 0:
            self.session_stats["new_total"] += 1
            if correct:
                self.session_stats["new_correct"] += 1
        else:
            self.session_stats["review_total"] += 1
            if correct:
                self.session_stats["review_correct"] += 1

        # Update progress
        self.update_progress(word, correct)

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

        # Show result
        result_msg = "¡Correcto! (Correct!)" if correct else f"Incorrecto. The correct answer is '{self.correct_answer}'"
        result_color = "green" if correct else "red"
        result_label = ttk.Label(self.content_frame, text=result_msg,
                           font=('Arial', 14, 'bold'), foreground=result_color)
        result_label.grid(row=7, column=0, pady=20)

        # Next button
        next_btn = ttk.Button(self.content_frame, text="Next", command=self.next_word)
        next_btn.grid(row=8, column=0, pady=10)
        next_btn.focus()

    def update_progress(self, word, correct):
        """Update progress for a word with Leitner system"""
        entry = self.progress[word]
        entry["attempts"] += 1
        entry["last_reviewed_session"] = self.session_counter
        
        if correct:
            entry["correct"] += 1
            entry["mastery"] = min(10, entry["mastery"] + 1)
            # Move to next Leitner box (max 5)
            entry["box"] = min(5, entry["box"] + 1)
        else:
            entry["mastery"] = max(0, entry["mastery"] - 1)
            # Move back to box 1 on incorrect answer
            entry["box"] = max(1, entry["box"] - 1) if entry["box"] > 0 else 1

    def next_word(self):
        """Move to the next word or end session"""
        self.current_word_index += 1
        if self.current_word_index < len(self.session_words):
            self.show_flashcard()
        else:
            self.show_session_summary()

    def show_session_summary(self):
        """Show session summary with results"""
        self.clear_content()
        self.save_progress()

        # Title
        ttk.Label(self.content_frame, text=f"Session #{self.session_counter} Complete!",
                  font=('Arial', 24, 'bold')).grid(row=0, column=0, pady=20)

        # Results frame
        results_frame = ttk.Frame(self.content_frame)
        results_frame.grid(row=1, column=0, pady=10)

        row = 0
        # New words results
        if self.session_stats["new_total"]:
            acc = self.session_stats["new_correct"] / self.session_stats["new_total"] * 100
            ttk.Label(results_frame,
                      text=f"New Words: {self.session_stats['new_correct']}/{self.session_stats['new_total']} ({acc:.1f}%)",
                      font=('Arial', 14)).grid(row=row, column=0, pady=5)
            row += 1

        # Review words results
        if self.session_stats["review_total"]:
            acc = self.session_stats["review_correct"] / self.session_stats["review_total"] * 100
            ttk.Label(results_frame,
                      text=f"Review Words: {self.session_stats['review_correct']}/{self.session_stats['review_total']} ({acc:.1f}%)",
                      font=('Arial', 14)).grid(row=row, column=0, pady=5)
            row += 1

        # Show new words introduced
        if self.session_stats["new_words"]:
            row += 1
            ttk.Label(results_frame, text="New Words Introduced:",
                      font=('Arial', 13, 'bold')).grid(row=row, column=0, pady=(15, 5))
            for idx, word in enumerate(self.session_stats["new_words"], start=1):
                ttk.Label(results_frame,
                          text=f"{idx}. {word['english'].title()} → {word['spanish'].title()}",
                          font=('Arial', 12)).grid(row=row + idx, column=0, sticky=tk.W)

        # Action buttons
        button_frame = ttk.Frame(self.content_frame)
        button_frame.grid(row=2, column=0, pady=30)
        
        ttk.Button(button_frame, text="New Session", 
                  command=self.restart_session).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Quit", 
                  command=self.root.quit).grid(row=0, column=1, padx=10)

    def restart_session(self):
        """Restart with a new session"""
        # Reset session stats
        self.session_stats = {
            "new_correct": 0,
            "new_total": 0,
            "review_correct": 0,
            "review_total": 0,
            "new_words": []
        }
        self.current_word_index = 0
        self.show_welcome_page()

    def show_no_words_message(self):
        """Show message when no words are available"""
        self.clear_content()
        ttk.Label(self.content_frame, text="No words available for learning or review.",
                  font=('Arial', 16)).grid(row=0, column=0, pady=50)
        ttk.Button(self.content_frame, text="Quit", 
                  command=self.root.quit).grid(row=1, column=0, pady=20)

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