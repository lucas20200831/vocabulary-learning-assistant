"""
Vocabulary Trainer - A program to help students consolidate new words through practice
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List


class VocabularyTrainer:
    """
    A class to manage vocabulary learning and consolidation
    """
    
    def __init__(self, data_file="vocabulary_data.json"):
        self.data_file = data_file
        self.vocabulary = self.load_data()
        
    def load_data(self) -> Dict:
        """Load vocabulary data from file or create an empty dictionary"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Initialize with empty vocabulary data
            return {}
    
    def save_data(self):
        """Save vocabulary data to file"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary, f, ensure_ascii=False, indent=2)
    
    def add_word(self, word: str, meaning: str):
        """Add a new word to the vocabulary"""
        if word.lower() not in self.vocabulary:
            self.vocabulary[word.lower()] = {
                "meaning": meaning,
                "attempts": 0,
                "correct": 0,
                "incorrect": 0,
                "history": []
            }
            self.save_data()
            print(f"Added word: {word}")
        else:
            print(f"Word '{word}' already exists in the vocabulary.")
    
    def record_attempt(self, word: str, correct: bool):
        """Record an attempt at spelling/recalling a word"""
        word_lower = word.lower()
        if word_lower in self.vocabulary:
            self.vocabulary[word_lower]['attempts'] += 1
            
            if correct:
                self.vocabulary[word_lower]['correct'] += 1
            else:
                self.vocabulary[word_lower]['incorrect'] += 1
                
            # Record the attempt in history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.vocabulary[word_lower]['history'].append({
                "timestamp": timestamp,
                "correct": correct
            })
            
            self.save_data()
        else:
            print(f"Word '{word}' not found in vocabulary!")
    
    def get_word_status(self, word: str) -> str:
        """Get the status of a word based on performance"""
        word_lower = word.lower()
        if word_lower not in self.vocabulary:
            return "Not in vocabulary"
            
        data = self.vocabulary[word_lower]
        if data['attempts'] == 0:
            return "New word"
        
        accuracy = data['correct'] / data['attempts']
        
        if accuracy >= 0.8:
            return "Mastered"
        elif accuracy >= 0.5:
            return "Learning"
        else:
            return "Needs practice"
    
    def get_words_needing_practice(self, limit: int = 10) -> List[str]:
        """Get words that need more practice (accuracy < 0.8 or low attempts)"""
        words_to_practice = []
        
        for word, data in self.vocabulary.items():
            if data['attempts'] == 0:
                # New words need practice
                words_to_practice.append(word)
            else:
                accuracy = data['correct'] / data['attempts']
                if accuracy < 0.8:
                    # Words with accuracy less than 80% need practice
                    words_to_practice.append(word)
        
        # Randomly select up to 'limit' words that need practice
        if len(words_to_practice) > limit:
            return random.sample(words_to_practice, limit)
        return words_to_practice
    
    def quiz_user(self, count: int = 5):
        """Quiz the user with words that need practice"""
        words_to_test = self.get_words_needing_practice(count)
        
        if not words_to_test:
            print("No words to practice right now!")
            return
        
        print(f"\nStarting quiz with {len(words_to_test)} words that need practice...")
        print("Type the meaning of each word:")
        print("-" * 40)
        
        score = 0
        total = len(words_to_test)
        
        for i, word in enumerate(words_to_test):
            print(f"\n{i+1}. Word: {word}")
            input("Press Enter when ready to see the meaning...")
            print(f"Meaning: {self.vocabulary[word]['meaning']}")
            
            response = input("\nDid you recall this word correctly? (y/n): ").lower()
            correct = response in ['y', 'yes', '1', 'true', 'right', 'correct']
            
            self.record_attempt(word, correct)
            
            if correct:
                score += 1
                print("Great job!")
            else:
                print("Keep practicing this word!")
                
        print(f"\nQuiz completed! Your accuracy: {score}/{total} ({(score/total)*100:.1f}%)")
    
    def show_progress(self):
        """Show overall progress statistics"""
        if not self.vocabulary:
            print("No words in vocabulary yet!")
            return
        
        mastered = 0
        learning = 0
        needs_practice = 0
        new_words = 0
        
        for word, data in self.vocabulary.items():
            status = self.get_word_status(word)
            if status == "Mastered":
                mastered += 1
            elif status == "Learning":
                learning += 1
            elif status == "Needs practice":
                needs_practice += 1
            else:
                new_words += 1
        
        print("\n--- Progress Report ---")
        print(f"Total words: {len(self.vocabulary)}")
        print(f"Mastered: {mastered}")
        print(f"Learning: {learning}")
        print(f"Needs practice: {needs_practice}")
        print(f"New words: {new_words}")
        print("-----------------------")


def main():
    trainer = VocabularyTrainer()
    
    while True:
        print("\n=== Vocabulary Trainer ===")
        print("1. Add a new word")
        print("2. Quiz me on words that need practice")
        print("3. Check my progress")
        print("4. View a word's status")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            word = input("Enter the new word: ")
            meaning = input("Enter the meaning: ")
            trainer.add_word(word, meaning)
            
        elif choice == '2':
            count = input("How many words would you like to test? (default 5): ")
            try:
                count = int(count) if count.strip() else 5
            except ValueError:
                count = 5
            trainer.quiz_user(count)
            
        elif choice == '3':
            trainer.show_progress()
            
        elif choice == '4':
            word = input("Enter the word to check: ")
            status = trainer.get_word_status(word)
            if status != "Not in vocabulary":
                data = trainer.vocabulary.get(word.lower(), {})
                print(f"\nWord: {word}")
                print(f"Meaning: {data.get('meaning', '')}")
                print(f"Status: {status}")
                print(f"Attempts: {data.get('attempts', 0)}")
                print(f"Correct: {data.get('correct', 0)}")
                print(f"Incorrect: {data.get('incorrect', 0)}")
                if data.get('attempts', 0) > 0:
                    accuracy = data['correct'] / data['attempts'] * 100
                    print(f"Accuracy: {accuracy:.1f}%")
            else:
                print(f"'{word}' is not in the vocabulary.")
                
        elif choice == '5':
            print("Thank you for using Vocabulary Trainer. Keep practicing!")
            break
            
        else:
            print("Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main()