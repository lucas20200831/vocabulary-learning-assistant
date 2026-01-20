from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from urllib.parse import unquote
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Session configuration for better browser compatibility
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

DATA_FILE = 'vocabulary_data.json'

def load_data():
    """載入詞彙數據"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """保存詞彙數據到文件"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vocab_list')
def vocab_list():
    data = load_data()
    # Transform data for template: organize by language and lesson
    contents = []
    for language, lessons in data.items():
        for lesson_num, lesson_content in lessons.items():
            # Check if this is new structure (has '詞語' and '段落' keys)
            if isinstance(lesson_content, dict) and ('詞語' in lesson_content or '段落' in lesson_content):
                word_count = len(lesson_content.get('詞語', []))
                para_count = len(lesson_content.get('段落', []))
                contents.append({
                    'language': language,
                    'lesson_number': lesson_num,
                    'word_count': word_count,
                    'para_count': para_count,
                    'content': lesson_content
                })
            # Handle old structure for backward compatibility
            else:
                word_count = len(lesson_content) if isinstance(lesson_content, dict) else 0
                contents.append({
                    'language': language,
                    'lesson_number': lesson_num,
                    'word_count': word_count,
                    'para_count': 0,
                    'content': lesson_content
                })
    
    return render_template('vocab_list.html', contents=contents)

@app.route('/create_lesson', methods=['GET', 'POST'])
def create_lesson():
    """Create new lesson with new data structure"""
    if request.method == 'POST':
        language = request.form.get('language', '').strip()
        lesson_name = request.form.get('lesson_name', '').strip()
        words_input = request.form.get('words_input', '').strip()
        
        if language and lesson_name and words_input:
            data = load_data()
            
            if language not in data:
                data[language] = {}
            
            # Parse words and create new data structure
            words_list = []
            for line in words_input.split('\n'):
                word = line.strip()
                if word:
                    words_list.append({
                        'word': word,
                        'meaning': '',
                        'attempts': 0,
                        'correct': 0,
                        'incorrect': 0,
                        'history': []
                    })
            
            data[language][lesson_name] = {
                '詞語': words_list,
                '段落': []
            }
            save_data(data)
            
            return redirect(url_for('vocab_list'))
    
    return render_template('create_lesson.html')

@app.route('/add_content', methods=['POST'])
def add_content():
    """處理新的聽寫內容提交（支持新的數據結構）"""
    try:
        req_data = request.get_json()
        
        language = req_data.get('language')
        lesson_number = req_data.get('lesson_number')
        content_type = req_data.get('content_type')
        
        if not all([language, lesson_number, content_type]):
            return jsonify({'error': '缺少必要參數'}), 400
        
        data = load_data()
        
        # 確保語言分類存在
        if language not in data:
            data[language] = {}
        
        # 檢查課程是否已存在
        if lesson_number in data[language]:
            return jsonify({'error': '該課程已存在'}), 400
        
        # 初始化課程結構
        lesson_data = {
            '詞語': [],
            '段落': []
        }
        
        # 處理詞語內容
        if content_type == '詞語':
            words = req_data.get('words', [])
            for word in words:
                lesson_data['詞語'].append({
                    'word': word,
                    'meaning': '',
                    'attempts': 0,
                    'correct': 0,
                    'incorrect': 0,
                    'history': []
                })
        
        # 處理段落內容
        elif content_type == '段落':
            paragraphs = req_data.get('paragraphs', [])
            for para in paragraphs:
                para_obj = {
                    'title': para.get('title', ''),
                    'sentences': []
                }
                for sentence in para.get('sentences', []):
                    para_obj['sentences'].append({
                        'sentence': sentence,
                        'attempts': 0,
                        'correct': 0,
                        'incorrect': 0,
                        'history': []
                    })
                lesson_data['段落'].append(para_obj)
        
        # 保存到數據文件
        data[language][lesson_number] = lesson_data
        save_data(data)
        
        return jsonify({'status': 'success', 'message': '內容已成功添加'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/edit_content/<language>/<lesson_num>', methods=['GET'])
def edit_content(language, lesson_num):
    """顯示編輯頁面"""
    # 解碼 URL 參數
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return "聽寫內容未找到", 404
    
    lesson_content = data[language][lesson_num]
    
    return render_template('edit_content.html',
                          language=language,
                          lesson_number=lesson_num,
                          content=lesson_content)

@app.route('/update_content', methods=['POST'])
def update_content():
    """更新聽寫內容"""
    try:
        req_data = request.get_json()
        
        language = req_data.get('language')
        lesson_number = req_data.get('lesson_number')
        words = req_data.get('words', [])
        paragraphs = req_data.get('paragraphs', [])
        
        if not all([language, lesson_number]):
            return jsonify({'error': '缺少必要參數'}), 400
        
        data = load_data()
        
        if language not in data or lesson_number not in data[language]:
            return jsonify({'error': '內容未找到'}), 404
        
        lesson_content = data[language][lesson_number]
        
        # 更新詞語
        updated_words = []
        for word_data in words:
            # 查找原有的詞語記錄（保留統計數據）
            original = None
            for old_word in lesson_content.get('詞語', []):
                if old_word['word'] == word_data['original_word']:
                    original = old_word
                    break
            
            if original:
                # 保留原有的統計數據
                updated_words.append({
                    'word': word_data['word'],
                    'meaning': word_data.get('meaning', ''),
                    'attempts': original.get('attempts', 0),
                    'correct': original.get('correct', 0),
                    'incorrect': original.get('incorrect', 0),
                    'history': original.get('history', [])
                })
            else:
                # 新詞語
                updated_words.append({
                    'word': word_data['word'],
                    'meaning': word_data.get('meaning', ''),
                    'attempts': 0,
                    'correct': 0,
                    'incorrect': 0,
                    'history': []
                })
        
        # 更新段落
        updated_paragraphs = []
        for para_data in paragraphs:
            updated_sentences = []
            for sent_data in para_data.get('sentences', []):
                # 查找原有的句子記錄
                original = None
                for old_para in lesson_content.get('段落', []):
                    if old_para['title'] == para_data['original_title']:
                        for old_sent in old_para['sentences']:
                            if old_sent['sentence'] == sent_data['original_sentence']:
                                original = old_sent
                                break
                
                if original:
                    updated_sentences.append({
                        'sentence': sent_data['sentence'],
                        'attempts': original.get('attempts', 0),
                        'correct': original.get('correct', 0),
                        'incorrect': original.get('incorrect', 0),
                        'history': original.get('history', [])
                    })
                else:
                    updated_sentences.append({
                        'sentence': sent_data['sentence'],
                        'attempts': 0,
                        'correct': 0,
                        'incorrect': 0,
                        'history': []
                    })
            
            updated_paragraphs.append({
                'title': para_data['title'],
                'sentences': updated_sentences
            })
        
        # 更新數據
        lesson_content['詞語'] = updated_words
        lesson_content['段落'] = updated_paragraphs
        
        save_data(data)
        
        return jsonify({'status': 'success', 'message': '內容已成功更新'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_content/<language>/<lesson_num>', methods=['POST'])
def delete_content(language, lesson_num):
    """刪除聽寫內容"""
    try:
        # 解碼 URL 參數
        language = unquote(language)
        lesson_num = unquote(lesson_num)
        
        data = load_data()
        
        if language not in data or lesson_num not in data[language]:
            # 即使未找到，也重定向回列表頁面
            return redirect(url_for('vocab_list'))
        
        del data[language][lesson_num]
        
        # 如果語言下沒有課程了，刪除語言
        if not data[language]:
            del data[language]
        
        save_data(data)
        
        # 成功刪除後重定向回列表頁面
        return redirect(url_for('vocab_list'))
    
    except Exception as e:
        # 發生錯誤時也重定向回列表頁面
        return redirect(url_for('vocab_list'))

@app.route('/quiz/<language>/<lesson_num>')
def quiz_new(language, lesson_num):
    """聽寫練習路由"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    content_type = request.args.get('content_type', '詞語').strip()
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return "聽寫內容未找到", 404
    
    lesson_content = data[language][lesson_num]
    
    words_to_practice = []
    if content_type == '詞語' and '詞語' in lesson_content:
        words_to_practice = [item['word'] for item in lesson_content['詞語']]
    elif content_type == '段落' and '段落' in lesson_content:
        for para in lesson_content['段落']:
            for sent_item in para.get('sentences', []):
                words_to_practice.append(sent_item['sentence'])
    
    if not words_to_practice:
        return f"沒有{content_type}可以聽寫", 404
    
    session.permanent = True
    session['current_quiz'] = {
        'language': language,
        'lesson': lesson_num,
        'content_type': content_type,
        'words': words_to_practice,
        'current_index': 0,
        'results': []
    }
    
    import json as json_module
    words_json = json_module.dumps(words_to_practice, ensure_ascii=False)
    
    display_name = f"{language} - {lesson_num}"
    return render_template('quiz.html', 
                          lesson_name=display_name, 
                          word_count=len(words_to_practice),
                          current_word=words_to_practice[0] if words_to_practice else None,
                          words_json=words_json,
                          content_type=content_type)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Handle quiz answer submission - works with or without session"""
    data = load_data()
    
    # Get parameters from request - these are sent from JavaScript
    word = request.form.get('word', '').strip()
    language = request.form.get('language', '').strip()
    lesson = request.form.get('lesson', '').strip()
    content_type = request.form.get('content_type', '詞語').strip()
    is_known_str = request.form.get('is_known', 'false')
    is_known = is_known_str.lower() == 'true'
    
    if not word or not language or not lesson:
        return jsonify({'error': '缺少必要參數'}), 400
    
    # Validate data structure
    try:
        lesson_data = data[language][lesson]
    except KeyError:
        return jsonify({'error': f'找不到課程: {language}/{lesson}'}), 400
    
    # Find and update the record based on content type
    word_found = False
    
    if content_type == '詞語' and '詞語' in lesson_data:
        # Handle word entries
        for word_item in lesson_data['詞語']:
            if word_item['word'] == word:
                word_item['attempts'] += 1
                if is_known:
                    word_item['correct'] += 1
                else:
                    word_item['incorrect'] += 1
                
                # Record history
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                word_item['history'].append({
                    "timestamp": timestamp,
                    "known": is_known
                })
                word_found = True
                break
    
    elif content_type == '段落' and '段落' in lesson_data:
        # Handle paragraph/sentence entries
        for para in lesson_data['段落']:
            for sent_item in para.get('sentences', []):
                if sent_item['sentence'] == word:
                    sent_item['attempts'] += 1
                    if is_known:
                        sent_item['correct'] += 1
                    else:
                        sent_item['incorrect'] += 1
                    
                    # Record history
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sent_item['history'].append({
                        "timestamp": timestamp,
                        "known": is_known
                    })
                    word_found = True
                    break
            if word_found:
                break
    
    if not word_found:
        return jsonify({'error': f'找不到內容: {word}'}), 400
    
    # Save data
    save_data(data)
    
    return jsonify({'status': 'success', 'message': f'已保存 {word} 的答題結果'})


@app.route('/review/<language>/<lesson_num>')
def review_new(language, lesson_num):
    """複習路由"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return "聽寫內容未找到", 404
    
    lesson_content = data[language][lesson_num]
    
    review_words = []
    if '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            accuracy = item['attempts'] > 0 and item['correct'] / item['attempts'] or 0
            if accuracy < 0.8:
                review_words.append({
                    'word': item['word'],
                    'meaning': item['meaning'],
                    'attempts': item['attempts'],
                    'correct': item['correct'],
                    'incorrect': item['incorrect'],
                    'accuracy': round(accuracy * 100, 1)
                })
    
    review_words.sort(key=lambda x: x['accuracy'])
    
    display_name = f"{language} - {lesson_num}"
    return render_template('review.html', 
                          lesson_name=display_name, 
                          review_words=review_words)

@app.route('/api/lesson/<language>/<lesson_num>/stats')
def lesson_stats_new(language, lesson_num):
    """統計路由"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return jsonify({'error': '聽寫內容未找到'}), 404
    
    lesson_content = data[language][lesson_num]
    
    total_items = 0
    mastered = 0
    needs_review = 0
    
    if '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            total_items += 1
            accuracy = item['attempts'] > 0 and item['correct'] / item['attempts'] or 0
            if accuracy >= 0.8 and item['attempts'] > 0:
                mastered += 1
            else:
                needs_review += 1
    
    return jsonify({
        'total_words': total_items,
        'mastered': mastered,
        'needs_review': needs_review,
        'mastered_percentage': round((mastered / total_items) * 100, 1) if total_items > 0 else 0
    })

@app.route('/save_content', methods=['POST'])
def save_content():
    """Save edited content from textarea format"""
    try:
        req_data = request.get_json()
        
        language = req_data.get('language')
        lesson = req_data.get('lesson')
        words = req_data.get('words', [])
        paragraphs = req_data.get('paragraphs', [])
        
        if not all([language, lesson]):
            return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
        
        data = load_data()
        
        if language not in data or lesson not in data[language]:
            return jsonify({'status': 'error', 'message': '內容未找到'}), 404
        
        lesson_content = data[language][lesson]
        
        # Update words (preserve statistics from existing words)
        if words:
            updated_words = []
            existing_words = {w['word']: w for w in lesson_content.get('詞語', [])}
            
            for word_text in words:
                if word_text in existing_words:
                    # Keep existing word with its statistics
                    updated_words.append(existing_words[word_text])
                else:
                    # Create new word entry with empty statistics
                    updated_words.append({
                        'word': word_text,
                        'meaning': '',
                        'attempts': 0,
                        'correct': 0,
                        'incorrect': 0,
                        'history': []
                    })
            
            lesson_content['詞語'] = updated_words
        
        # Update paragraphs (preserve statistics from existing sentences)
        if paragraphs:
            updated_paragraphs = []
            existing_paras = {p['title']: p for p in lesson_content.get('段落', [])}
            
            for para_data in paragraphs:
                title = para_data.get('title')
                sentences_text = para_data.get('sentences', [])
                
                # Create sentence objects
                updated_sentences = []
                existing_para = existing_paras.get(title)
                existing_sentences = {}
                
                if existing_para:
                    # Build map of existing sentences
                    existing_sentences = {s['sentence']: s for s in existing_para.get('sentences', [])}
                
                for sent_text in sentences_text:
                    if sent_text in existing_sentences:
                        # Keep existing sentence with statistics
                        updated_sentences.append(existing_sentences[sent_text])
                    else:
                        # Create new sentence entry with empty statistics
                        updated_sentences.append({
                            'sentence': sent_text,
                            'attempts': 0,
                            'correct': 0,
                            'incorrect': 0,
                            'history': []
                        })
                
                updated_paragraphs.append({
                    'title': title,
                    'sentences': updated_sentences
                })
            
            lesson_content['段落'] = updated_paragraphs
        
        # Save the updated data
        save_data(data)
        
        return jsonify({'status': 'success', 'message': '內容已保存'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True, host='127.0.0.1', port=5002)  # Changed to port 5002 to avoid conflicts