from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import os
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DATA_FILE = 'vocabulary_data.json'

def load_data():
    """Load vocabulary data from file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """Save vocabulary data to file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vocab_list')
def vocab_list():
    data = load_data()
    lessons = list(data.keys())
    return render_template('vocab_list.html', lessons=lessons, data=data)

@app.route('/create_lesson', methods=['GET', 'POST'])
def create_lesson():
    if request.method == 'POST':
        lesson_name = request.form.get('lesson_name')
        words_input = request.form.get('words_input')
        
        if lesson_name and words_input:
            data = load_data()
            
            # Parse words input (expected format: one word per line)
            lesson_vocab = {}
            for line in words_input.strip().split('\n'):
                word = line.strip()
                if word:  # If line has content
                    lesson_vocab[word] = {
                        "meaning": word,  # Use the word itself as meaning
                        "attempts": 0,
                        "correct": 0,
                        "incorrect": 0,
                        "history": []
                    }
            
            data[lesson_name] = lesson_vocab
            save_data(data)
            
            return redirect(url_for('vocab_list'))
    
    return render_template('create_lesson.html')

@app.route('/quiz/<lesson_name>')
def quiz(lesson_name):
    data = load_data()
    
    if lesson_name not in data:
        return "Lesson not found", 404
    
    lesson_vocab = data[lesson_name]
    
    # Get all words in the lesson for quiz - preserve original order
    all_words = list(lesson_vocab.keys())
    
    # Get words that need practice (accuracy < 0.8 or haven't been attempted)
    words_to_practice = []
    for word in all_words:
        info = lesson_vocab[word]
        if info['attempts'] == 0 or (info['attempts'] > 0 and info['correct'] / info['attempts'] < 0.8):
            words_to_practice.append(word)
    
    # If no words need practice, use all words in original order
    if not words_to_practice:
        words_to_practice = all_words
    
    # Limit to 10 words max for quiz, preserving order
    if len(words_to_practice) > 10:
        # Take the first 10 words to maintain order
        words_to_practice = words_to_practice[:10]
    
    # Store quiz state in session
    session['current_quiz'] = {
        'lesson': lesson_name,
        'words': words_to_practice,
        'current_index': 0,
        'results': []
    }
    
    return render_template('quiz.html', 
                          lesson_name=lesson_name, 
                          word_count=len(words_to_practice),
                          current_word=words_to_practice[0] if words_to_practice else None)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = load_data()
    
    if 'current_quiz' not in session:
        return jsonify({'error': 'No active quiz'}), 400
    
    quiz_state = session['current_quiz']
    lesson_name = quiz_state['lesson']
    word_index = quiz_state['current_index']
    words = quiz_state['words']
    
    if word_index >= len(words):
        return jsonify({'error': 'Quiz finished'}), 400
    
    word = words[word_index]
    is_known_str = request.form.get('is_known', 'false')
    is_known = is_known_str.lower() == 'true'
    
    # Record the attempt
    word_data = data[lesson_name][word]
    word_data['attempts'] += 1
    
    # We don't track correct/incorrect here since we're doing dictation
    # Instead, we'll track if the word was known or unknown during dictation
    if is_known:
        word_data['correct'] += 1
        quiz_state['results'].append({'word': word, 'known': True})
    else:
        word_data['incorrect'] += 1
        quiz_state['results'].append({'word': word, 'known': False})
    
    # Record history
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    word_data['history'].append({
        "timestamp": timestamp,
        "known": is_known
    })
    
    # Save data
    save_data(data)
    
    # Update session
    quiz_state['current_index'] += 1
    session['current_quiz'] = quiz_state
    
    # Return next word or finish
    if quiz_state['current_index'] >= len(words):
        return jsonify({'status': 'finished', 'results': quiz_state['results']})
    else:
        next_word = words[quiz_state['current_index']]
        return jsonify({
            'status': 'continue',
            'current_index': quiz_state['current_index'],
            'total_words': len(words),
            'next_word': next_word
        })

@app.route('/review/<lesson_name>')
def review(lesson_name):
    data = load_data()
    
    if lesson_name not in data:
        return "Lesson not found", 404
    
    lesson_vocab = data[lesson_name]
    
    # Get words that need review (accuracy < 0.8 or haven't been attempted)
    review_words = []
    for word, info in lesson_vocab.items():
        accuracy = info['attempts'] > 0 and info['correct'] / info['attempts'] or 0
        if accuracy < 0.8:
            review_words.append({
                'word': word,
                'meaning': info['meaning'],
                'attempts': info['attempts'],
                'correct': info['correct'],
                'incorrect': info['incorrect'],
                'accuracy': round(accuracy * 100, 1)
            })
    
    # Sort by accuracy (lowest first)
    review_words.sort(key=lambda x: x['accuracy'])
    
    return render_template('review.html', 
                          lesson_name=lesson_name, 
                          review_words=review_words)

@app.route('/api/lesson/<lesson_name>/stats')
def lesson_stats(lesson_name):
    data = load_data()
    
    if lesson_name not in data:
        return jsonify({'error': 'Lesson not found'}), 404
    
    lesson_vocab = data[lesson_name]
    
    total_words = len(lesson_vocab)
    mastered = 0
    needs_review = 0
    
    for word, info in lesson_vocab.items():
        accuracy = info['attempts'] > 0 and info['correct'] / info['attempts'] or 0
        if accuracy >= 0.8 and info['attempts'] > 0:
            mastered += 1
        else:
            needs_review += 1
    
    return jsonify({
        'total_words': total_words,
        'mastered': mastered,
        'needs_review': needs_review,
        'mastered_percentage': round((mastered / total_words) * 100, 1) if total_words > 0 else 0
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True, host='127.0.0.1', port=5002)  # Changed to port 5002 to avoid conflicts