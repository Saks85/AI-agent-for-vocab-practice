import json
import random
import os
import csv

PROGRESS_FILE = "vocab_progress.json"
DATASET_FILE = "english_spanish.csv"


class VocabularyAgent:
    def __init__(self):
        self.vocab = self.load_dataset()
        self.progress = self.load_progress()

    def load_dataset(self):
        vocab = []
        if not os.path.exists(DATASET_FILE):
            raise FileNotFoundError(f"Dataset file '{DATASET_FILE}' not found. Please download it from Kaggle.")
        
        try:
            with open(DATASET_FILE, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Try multiple possible column names
                    english_word = (row.get("english") or row.get("English") or 
                                  row.get("ENG") or row.get("en") or row.get("EN"))
                    spanish_word = (row.get("spanish") or row.get("Spanish") or 
                                  row.get("ESP") or row.get("es") or row.get("ES"))
                    
                    if english_word and spanish_word:
                        english_word = english_word.strip().lower()
                        spanish_word = spanish_word.strip().lower()
                        if english_word and spanish_word:  # Check not empty after strip
                            vocab.append({"english": english_word, "spanish": spanish_word})
            
            if not vocab:
                raise ValueError("No valid vocabulary pairs found in the dataset.")
            
            print(f"Loaded {len(vocab)} vocabulary pairs.")
            return vocab
            
        except Exception as e:
            raise Exception(f"Error loading dataset: {str(e)}")

    def load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding='utf-8') as f:
                    loaded_progress = json.load(f)
                    # Ensure all vocab words have progress entries
                    progress = {}
                    for item in self.vocab:
                        english_word = item["english"]
                        if english_word in loaded_progress:
                            progress[english_word] = loaded_progress[english_word]
                        else:
                            progress[english_word] = {"mastery": 0, "attempts": 0, "correct": 0}
                    return progress
            except Exception as e:
                print(f"Error loading progress file: {e}. Starting fresh.")
        
        # Create new progress for all words
        progress = {item["english"]: {"mastery": 0, "attempts": 0, "correct": 0} for item in self.vocab}
        return progress

    def save_progress(self):
        try:
            with open(PROGRESS_FILE, "w", encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving progress: {e}")

    def select_words_for_session(self, num_words=5):
        # Ensure we don't request more words than available
        num_words = min(num_words, len(self.vocab))
        
        # Sort by mastery (lowest first) and then by attempts (fewer attempts first for tiebreaking)
        sorted_words = sorted(self.progress.items(), 
                            key=lambda x: (x[1]["mastery"], x[1]["attempts"]))
        
        selected_english_words = [word for word, _ in sorted_words[:num_words]]
        selected = [item for item in self.vocab if item["english"] in selected_english_words]
        return selected

    def flashcard_practice(self, word_data):
        print(f"\n{'='*50}")
        print(f"FLASHCARD PRACTICE")
        print(f"{'='*50}")
        print(f"English: {word_data['english'].title()}")
        input("Try to recall the Spanish translation and press Enter...")
        print(f"Spanish: {word_data['spanish']}")
        print("Take a moment to memorize this translation.")
        input("Press Enter when ready to continue...")

    def quiz(self, word_data):
        correct_answer = word_data["spanish"]
        
        # Ensure we have enough vocabulary for multiple choice
        if len(self.vocab) < 4:
            print("Not enough vocabulary for multiple choice quiz. Skipping quiz.")
            return
            
        options = [correct_answer]
        
        # Pick 3 other random Spanish words for options
        attempts = 0
        while len(options) < 4 and attempts < 20:  # Prevent infinite loop
            option = random.choice(self.vocab)["spanish"]
            if option not in options:
                options.append(option)
            attempts += 1
        
        # If we couldn't get 4 unique options, just proceed with what we have
        random.shuffle(options)

        print(f"\n{'='*50}")
        print(f"QUIZ TIME")
        print(f"{'='*50}")
        print(f"What is the Spanish translation of '{word_data['english'].title()}'?")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        while True:
            try:
                answer = input("Your answer (choose number): ").strip()
                answer_idx = int(answer) - 1
                
                if 0 <= answer_idx < len(options):
                    if options[answer_idx] == correct_answer:
                        print("¡Correcto! (Correct!)")
                        self.update_progress(word_data["english"], True)
                        break
                    else:
                        print(f"Incorrecto. The correct answer is '{correct_answer}'.")
                        self.update_progress(word_data["english"], False)
                        break
                else:
                    print(f"Please enter a number between 1 and {len(options)}.")
                    
            except ValueError:
                print("Please enter a valid number.")

    def update_progress(self, word, correct):
        if word not in self.progress:
            self.progress[word] = {"mastery": 0, "attempts": 0, "correct": 0}
            
        self.progress[word]["attempts"] += 1
        if correct:
            self.progress[word]["correct"] += 1
            self.progress[word]["mastery"] = min(self.progress[word]["mastery"] + 1, 10)
        else:
            self.progress[word]["mastery"] = max(self.progress[word]["mastery"] - 1, 0)

    def show_progress_summary(self):
        print(f"\n{'='*50}")
        print("PROGRESS SUMMARY")
        print(f"{'='*50}")
        
        total_words = len(self.progress)
        mastered_words = sum(1 for stats in self.progress.values() if stats["mastery"] >= 8)
        
        print(f"Total vocabulary: {total_words}")
        print(f"Well-learned words (mastery ≥ 8): {mastered_words}")
        print(f"Progress: {mastered_words/total_words*100:.1f}%")
        
        print(f"\nTop 10 best-learned words:")
        sorted_progress = sorted(self.progress.items(), key=lambda x: -x[1]["mastery"])
        for word, stats in sorted_progress[:10]:
            correct = stats["correct"]
            attempts = stats["attempts"]
            mastery = stats["mastery"]
            accuracy = f"{correct}/{attempts}" if attempts > 0 else "0/0"
            print(f"  {word.title()}: Mastery={mastery}/10, Accuracy={accuracy}")

    def run_session(self):
        print("¡Bienvenido! Welcome to your English-Spanish vocabulary practice session!")
        
        try:
            words = self.select_words_for_session()
            print(f"\nToday's focus words: {[w['english'].title() for w in words]}")
            input("\nPress Enter to begin your session...")

            for i, word_data in enumerate(words, 1):
                print(f"\n📚 Word {i} of {len(words)}")
                self.flashcard_practice(word_data)
                self.quiz(word_data)

            self.save_progress()
            self.show_progress_summary()
            print(f"\n{'='*50}")
            print("¡Excelente! Session complete. ¡Hasta la vista!")
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"An error occurred during the session: {e}")
            self.save_progress()  # Save any progress made before the error


if __name__ == "__main__":
    try:
        agent = VocabularyAgent()
        agent.run_session()
    except Exception as e:
        print(f"Failed to start vocabulary agent: {e}")
        print("Please ensure the dataset file exists and is properly formatted.")