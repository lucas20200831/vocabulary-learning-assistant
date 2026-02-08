from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_file
from flask_cors import CORS
from urllib.parse import unquote
import json
import os
from datetime import datetime, timedelta
import hashlib
import threading
from queue import Queue
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# 启用 CORS 支持（生产环境需要）
CORS(app, resources={
    r"/tts/*": {"origins": "*"},
    r"/static/*": {"origins": "*"}
})

# Session configuration for better browser compatibility
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Disable Jinja2 caching
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.jinja_env.cache = None

# Disable auto-reload to prevent duplicate TTS threads
app.config['ENV'] = 'production'

# 配置静态文件路径
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'static', 'audio')
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# 初始化文字转语音引擎和后台线程
tts_engine = True  # gTTS 总是可用的（无需初始化）
tts_queue = Queue()
tts_thread = None
gTTS_lib = None  # 全局 gTTS 引用

def init_tts():
    """初始化 TTS 后台线程"""
    global tts_thread, tts_engine, gTTS_lib
    try:
        from gtts import gTTS
        gTTS_lib = gTTS
        print("[TTS] gTTS library imported successfully")
        
        # 启动多个后台 TTS 线程以加速处理
        def tts_worker():
            """后台处理 TTS 任务"""
            while True:
                try:
                    word, audio_file = tts_queue.get()
                    if word is None:  # 停止信号
                        break
                    # 检查文件是否已存在
                    if not os.path.exists(audio_file):
                        max_retries = 5  # 增加到 5 次重试
                        retry_count = 0
                        success = False
                        
                        while retry_count < max_retries and not success:
                            try:
                                print(f"[TTS] Generating: {word} (attempt {retry_count + 1}/{max_retries})")
                                tts = gTTS_lib(text=word, lang='zh-CN', slow=False)
                                tts.save(audio_file)
                                
                                # 验证文件是否真的被创建了
                                if os.path.exists(audio_file):
                                    file_size = os.path.getsize(audio_file)
                                    if file_size > 0:  # 确保不是空文件
                                        # 确保文件权限正确
                                        os.chmod(audio_file, 0o644)
                                        print(f"[TTS] ✓ Generated successfully: {word} -> {audio_file} ({file_size} bytes)")
                                        success = True
                                    else:
                                        print(f"[TTS] ✗ Generated empty file for: {word}")
                                        retry_count += 1
                                        if retry_count < max_retries:
                                            wait_time = 1 + (retry_count * 0.5)  # 1s, 1.5s, 2s, 2.5s, 3s
                                            print(f"[TTS] Retrying in {wait_time}s...")
                                            time.sleep(wait_time)
                                else:
                                    print(f"[TTS] ✗ File was not created after save() call for: {word}")
                                    retry_count += 1
                                    if retry_count < max_retries:
                                        wait_time = 1 + (retry_count * 0.5)
                                        print(f"[TTS] Retrying in {wait_time}s...")
                                        time.sleep(wait_time)
                                    
                            except Exception as gen_err:
                                retry_count += 1
                                error_type = type(gen_err).__name__
                                if retry_count < max_retries:
                                    wait_time = 1 + (retry_count * 0.5)  # 更短的延迟
                                    print(f"[TTS] ✗ {error_type} for '{word}': {str(gen_err)[:100]}")
                                    print(f"[TTS] Retrying in {wait_time}s (attempt {retry_count}/{max_retries})...")
                                    time.sleep(wait_time)
                                else:
                                    print(f"[TTS] ✗ Final failure for '{word}' after {max_retries} attempts: {error_type}")
                        
                        if not success:
                            print(f"[TTS] ✗ FAILED to generate audio for: {word}")
                    else:
                        file_size = os.path.getsize(audio_file)
                        print(f"[TTS] ✓ Already cached: {word} ({file_size} bytes)")
                    
                    # 在两个请求之间添加短延迟（0.5s）以避免 API 限制
                    time.sleep(0.5)
                    tts_queue.task_done()
                except Exception as e:
                    print(f"[TTS] ✗ Worker Error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(0.5)
                    tts_queue.task_done()
        
        # 启动 1 个后台线程处理 TTS（避免 API 限制导致请求失败）
        for i in range(1):
            tts_thread = threading.Thread(target=tts_worker, daemon=True)
            tts_thread.start()
        print("[TTS] Engine initialized with gTTS (1 worker thread)")
        
    except ImportError as e:
        tts_engine = False
        gTTS_lib = None
        print(f"Warning: gTTS not installed - {str(e)}, TTS will be disabled")

# 初始化 TTS
init_tts()

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
    # 直接重定向到课程列表，无需首页
    return redirect(url_for('vocab_list'))

@app.route('/vocab_list')
def vocab_list():
    data = load_data()
    # Transform data for template: organize by language and lesson
    # Support both old structure (language -> lessons) and new structure (direct lessons)
    contents = []
    
    for key, value in data.items():
        # Determine if this is a language key (with nested lessons) or a lesson key (with content)
        if isinstance(value, dict):
            # Check if it looks like a lesson (has '詞語' and/or '段落' keys)
            if ('詞語' in value or '段落' in value):
                # This is a new-format lesson (no language hierarchy)
                # Ensure all paragraphs have IDs
                paragraphs = value.get('段落', [])
                for idx, para in enumerate(paragraphs):
                    if 'id' not in para:
                        para['id'] = str(idx)
                
                word_count = len(value.get('詞語', []))
                para_count = len(paragraphs)
                contents.append({
                    'language': '',  # Empty for new format
                    'lesson_number': key,
                    'word_count': word_count,
                    'para_count': para_count,
                    'content': value,
                    'is_simple': True
                })
            else:
                # This looks like a language key with nested lessons (old format)
                for lesson_num, lesson_content in value.items():
                    if isinstance(lesson_content, dict) and ('詞語' in lesson_content or '段落' in lesson_content):
                        # Ensure all paragraphs have IDs
                        paragraphs = lesson_content.get('段落', [])
                        for idx, para in enumerate(paragraphs):
                            if 'id' not in para:
                                para['id'] = str(idx)
                        
                        word_count = len(lesson_content.get('詞語', []))
                        para_count = len(paragraphs)
                        contents.append({
                            'language': key,
                            'lesson_number': lesson_num,
                            'word_count': word_count,
                            'para_count': para_count,
                            'content': lesson_content,
                            'is_simple': False
                        })
                    else:
                        word_count = len(lesson_content) if isinstance(lesson_content, dict) else 0
                        contents.append({
                            'language': key,
                            'lesson_number': lesson_num,
                            'word_count': word_count,
                            'para_count': 0,
                            'content': lesson_content,
                            'is_simple': False
                        })
    
    return render_template('vocab_list.html', contents=contents)

@app.route('/unmastered_words')
def unmastered_words():
    """显示所有未掌握单词的页面"""
    return render_template('unmastered_words.html')

@app.route('/api/search_lessons')
def search_lessons():
    """搜索課程 - 支持按標題和內容搜索"""
    keyword = request.args.get('keyword', '').strip().lower()
    
    if not keyword:
        return jsonify([])
    
    data = load_data()
    results = []
    
    for key, value in data.items():
        if isinstance(value, dict):
            if ('詞語' in value or '段落' in value):
                # 新格式課程
                lesson_number = key
                language = ''
                is_simple = True
                lesson_content = value
            else:
                # 舊格式課程，需要檢查每個lesson
                for lesson_num, lesson_content in value.items():
                    if isinstance(lesson_content, dict) and ('詞語' in lesson_content or '段落' in lesson_content):
                        lesson_number = lesson_num
                        language = key
                        is_simple = False
                        
                        # 檢查是否匹配
                        match = False
                        
                        # 1. 匹配課程標題
                        if keyword in lesson_number.lower():
                            match = True
                        
                        # 2. 匹配詞語
                        if not match:
                            for word_item in lesson_content.get('詞語', []):
                                word_text = word_item.get('word', '').lower()
                                meaning_text = word_item.get('meaning', '').lower()
                                if keyword in word_text or keyword in meaning_text:
                                    match = True
                                    break
                        
                        # 3. 匹配段落
                        if not match:
                            for para in lesson_content.get('段落', []):
                                para_title = para.get('title', '').lower()
                                if keyword in para_title:
                                    match = True
                                    break
                                
                                for sent in para.get('sentences', []):
                                    sent_text = sent.get('sentence', '') if isinstance(sent, dict) else sent
                                    if keyword in sent_text.lower():
                                        match = True
                                        break
                                
                                if match:
                                    break
                        
                        if match:
                            word_count = len(lesson_content.get('詞語', []))
                            para_count = len(lesson_content.get('段落', []))
                            results.append({
                                'language': language,
                                'lesson_number': lesson_number,
                                'word_count': word_count,
                                'para_count': para_count,
                                'is_simple': is_simple
                            })
                continue
            
            # 新格式課程處理
            lesson_number = key
            language = ''
            is_simple = True
            
            # 檢查是否匹配
            match = False
            
            # 1. 匹配課程標題
            if keyword in lesson_number.lower():
                match = True
            
            # 2. 匹配詞語
            if not match:
                for word_item in lesson_content.get('詞語', []):
                    word_text = word_item.get('word', '').lower()
                    meaning_text = word_item.get('meaning', '').lower()
                    if keyword in word_text or keyword in meaning_text:
                        match = True
                        break
            
            # 3. 匹配段落
            if not match:
                for para in lesson_content.get('段落', []):
                    para_title = para.get('title', '').lower()
                    if keyword in para_title:
                        match = True
                        break
                    
                    for sent in para.get('sentences', []):
                        sent_text = sent.get('sentence', '') if isinstance(sent, dict) else sent
                        if keyword in sent_text.lower():
                            match = True
                            break
                    
                    if match:
                        break
            
            if match:
                word_count = len(lesson_content.get('詞語', []))
                para_count = len(lesson_content.get('段落', []))
                results.append({
                    'language': language,
                    'lesson_number': lesson_number,
                    'word_count': word_count,
                    'para_count': para_count,
                    'is_simple': is_simple
                })
    
    return jsonify(results)

@app.route('/api/get_unmastered_words')
def get_unmastered_words():
    """获取所有未掌握的单词"""
    data = load_data()
    unmastered_words = []
    
    # 遍历所有课程
    for key, value in data.items():
        if isinstance(value, dict):
            # 检查是否为新格式课程（直接包含詞語和段落）
            if '詞語' in value or '段落' in value:
                # 新格式：课程名为key
                lesson_name = key
                language = ''
                is_simple = True
                
                # 提取未掌握的词语
                if '詞語' in value:
                    for word_item in value['詞語']:
                        word = word_item.get('word', '')
                        attempts = word_item.get('attempts', 0)
                        correct = word_item.get('correct', 0)
                        
                        # 未掌握的标准：尝试次数为0，或正确率低于75%
                        if attempts == 0 or (attempts > 0 and correct / attempts < 0.75):
                            unmastered_words.append({
                                'word': word,
                                'lesson': lesson_name,
                                'language': language,
                                'is_simple': True,
                                'attempts': attempts,
                                'accuracy': (correct / attempts * 100) if attempts > 0 else 0
                            })
            else:
                # 旧格式：按语言分类
                for lesson_num, lesson_content in value.items():
                    if isinstance(lesson_content, dict) and ('詞語' in lesson_content or '段落' in lesson_content):
                        language = key
                        is_simple = False
                        
                        # 提取未掌握的词语
                        if '詞語' in lesson_content:
                            for word_item in lesson_content['詞語']:
                                word = word_item.get('word', '')
                                attempts = word_item.get('attempts', 0)
                                correct = word_item.get('correct', 0)
                                
                                # 未掌握的标准：尝试次数为0，或正确率低于75%
                                if attempts == 0 or (attempts > 0 and correct / attempts < 0.75):
                                    unmastered_words.append({
                                        'word': word,
                                        'lesson': lesson_num,
                                        'language': language,
                                        'is_simple': False,
                                        'attempts': attempts,
                                        'accuracy': (correct / attempts * 100) if attempts > 0 else 0
                                    })
    
    # 按准确率排序（准确率低的优先）
    unmastered_words.sort(key=lambda x: x['accuracy'])
    
    return jsonify(unmastered_words)

@app.route('/api/get_all_words')
def get_all_words():
    """获取所有词语的统计信息"""
    data = load_data()
    total_words = 0
    mastered_words = 0
    
    # 遍历所有课程
    for key, value in data.items():
        if isinstance(value, dict):
            # 检查是否为新格式课程（直接包含詞語和段落）
            if '詞語' in value:
                # 新格式：课程名为key
                for word_item in value['詞語']:
                    total_words += 1
                    attempts = word_item.get('attempts', 0)
                    correct = word_item.get('correct', 0)
                    
                    # 已掌握的标准：正确率≥75%
                    if attempts > 0 and correct / attempts >= 0.75:
                        mastered_words += 1
            else:
                # 旧格式：按语言分类
                for lesson_num, lesson_content in value.items():
                    if isinstance(lesson_content, dict) and '詞語' in lesson_content:
                        for word_item in lesson_content['詞語']:
                            total_words += 1
                            attempts = word_item.get('attempts', 0)
                            correct = word_item.get('correct', 0)
                            
                            # 已掌握的标准：正确率≥75%
                            if attempts > 0 and correct / attempts >= 0.75:
                                mastered_words += 1
    
    return jsonify({
        'total': total_words,
        'mastered': mastered_words,
        'unmastered': total_words - mastered_words
    })

@app.route('/api/get_lessons_unmastered_counts')
def get_lessons_unmastered_counts():
    """获取每个课程的未掌握单词数量"""
    data = load_data()
    lesson_counts = {}
    
    # 遍历所有课程
    for key, value in data.items():
        if isinstance(value, dict):
            # 检查是否为新格式课程（直接包含詞語和段落）
            if '詞語' in value:
                # 新格式：课程名为key
                unmastered_count = 0
                for word_item in value['詞語']:
                    attempts = word_item.get('attempts', 0)
                    correct = word_item.get('correct', 0)
                    
                    # 未掌握的标准：尝试次数为0，或正确率低于75%
                    if attempts == 0 or (attempts > 0 and correct / attempts < 0.75):
                        unmastered_count += 1
                
                lesson_counts[key] = unmastered_count
            else:
                # 旧格式：按语言分类
                for lesson_num, lesson_content in value.items():
                    if isinstance(lesson_content, dict) and '詞語' in lesson_content:
                        unmastered_count = 0
                        for word_item in lesson_content['詞語']:
                            attempts = word_item.get('attempts', 0)
                            correct = word_item.get('correct', 0)
                            
                            # 未掌握的标准：尝试次数为0，或正确率低于75%
                            if attempts == 0 or (attempts > 0 and correct / attempts < 0.75):
                                unmastered_count += 1
                        
                        lesson_key = key + '|' + lesson_num
                        lesson_counts[lesson_key] = unmastered_count
    
    return jsonify(lesson_counts)

@app.route('/api/split_sentences', methods=['POST'])
def api_split_sentences():
    """API: 使用jieba进行智能拆分（在词语边界处拆分）"""
    try:
        req_data = request.get_json()
        text = req_data.get('text', '').strip()
        
        if not text:
            return jsonify({'status': 'error', 'message': '文本为空'}), 400
        
        # 调用拆分函数
        sentences_by_punct = split_by_punctuation(text)
        final_sentences = split_long_sentences(sentences_by_punct)
        
        return jsonify({
            'status': 'success',
            'sentences': final_sentences
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/quiz_all_unmastered')
def quiz_all_unmastered():
    """聽寫所有未掌握的單詞"""
    data = load_data()
    
    # 获取所有未掌握的词语
    unmastered_words = []
    for key, value in data.items():
        if isinstance(value, dict):
            if '詞語' in value or '段落' in value:
                # 新格式课程
                if '詞語' in value:
                    for word_item in value['詞語']:
                        word = word_item.get('word', '')
                        attempts = word_item.get('attempts', 0)
                        correct = word_item.get('correct', 0)
                        if attempts == 0 or (attempts > 0 and correct / attempts < 0.75):
                            unmastered_words.append(word)
            else:
                # 旧格式课程
                for lesson_num, lesson_content in value.items():
                    if isinstance(lesson_content, dict) and '詞語' in lesson_content:
                        for word_item in lesson_content['詞語']:
                            word = word_item.get('word', '')
                            attempts = word_item.get('attempts', 0)
                            correct = word_item.get('correct', 0)
                            if attempts == 0 or (attempts > 0 and correct / attempts < 0.75):
                                unmastered_words.append(word)
    
    if not unmastered_words:
        return "沒有未掌握的單詞", 404
    
    # 预加载TTS
    print(f"[ALL_UNMASTERED] Preloading {len(unmastered_words)} words for TTS")
    for i, word in enumerate(unmastered_words):
        word_hash = hashlib.md5(word.encode('utf-8')).hexdigest()
        audio_file = os.path.join(AUDIO_DIR, f'{word_hash}.mp3')
        if not os.path.exists(audio_file):
            print(f"[ALL_UNMASTERED] Queuing word {i+1}/{len(unmastered_words)}: {word}")
            tts_queue.put((word, audio_file))
        else:
            print(f"[ALL_UNMASTERED] Already cached: {word}")
    
    session.permanent = True
    session['current_quiz'] = {
        'language': '',
        'lesson': '所有未掌握單詞',
        'content_type': '詞語',
        'words': unmastered_words,
        'is_all_unmastered': True
    }
    
    import json as json_module
    words_json = json_module.dumps(unmastered_words, ensure_ascii=False)
    
    return render_template('quiz.html', 
                         lesson_name='所有未掌握單詞',
                         language='',
                         lesson_num='所有未掌握單詞',
                         word_count=len(unmastered_words),
                         current_word=unmastered_words[0] if unmastered_words else None,
                         words_json=words_json,
                         content_type='詞語',
                         return_to='/unmastered_words')

@app.route('/tts/<word>')
def generate_tts(word):
    """获取已生成的音频文件 URL（只读取不生成）"""
    if not tts_engine:
        print("[TTS] TTS engine not available")
        return jsonify({'error': 'TTS engine not available'}), 500
    
    try:
        # 解码 URL 编码的词语
        word = unquote(word)
        print(f"[TTS] Request for: {word}")
        
        # 生成文件名（使用MD5哈希）
        word_hash = hashlib.md5(word.encode('utf-8')).hexdigest()
        audio_file = os.path.join(AUDIO_DIR, f'{word_hash}.mp3')
        
        # 检查文件是否存在（不再尝试生成）
        if os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            audio_url = f'/static/audio/{word_hash}.mp3?v={int(time.time())}'
            print(f"[TTS] ✓ Found: '{word}' ({file_size} bytes)")
            return jsonify({
                'success': True,
                'url': audio_url,
                'cached': True,
                'ready': True,
                'word': word,
                'hash': word_hash
            })
        else:
            # 文件不存在 - 返回错误，不尝试生成
            print(f"[TTS] ✗ Not found: '{word}' - file was not pre-generated during save")
            return jsonify({
                'success': False,
                'error': f'Audio file not found for: {word}. Please re-save the lesson to generate audio.',
                'word': word,
                'hash': word_hash
            }), 404
            
    except Exception as e:
        print(f"[TTS] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/create_lesson', methods=['GET', 'POST'])
def create_lesson():
    """顯示簡化的課程創建頁面"""
    return render_template('create_lesson_new.html')

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
        
        # 處理段落內容 (新結構：每個段落是獨立項)
        elif content_type == '段落':
            paragraphs = req_data.get('paragraphs', [])
            for idx, para in enumerate(paragraphs):
                para_obj = {
                    'id': f"para_{idx+1}",
                    'title': para.get('title', f'段落{idx+1}'),
                    'sentences': para.get('sentences', []),
                    'attempts': 0,
                    'correct': 0,
                    'incorrect': 0,
                    'history': []
                }
                lesson_data['段落'].append(para_obj)
        
        # 保存到數據文件
        data[language][lesson_number] = lesson_data
        save_data(data)
        
        # 計算詞語和段落的數量用於前端記錄
        word_count = len(lesson_data.get('詞語', []))
        para_count = len(lesson_data.get('段落', []))
        
        # 添加新課程後，立即預生成所有音頻
        print(f"[ADD_CONTENT] Triggering TTS generation for new lesson: {language}/{lesson_number}")
        
        texts_to_generate = []
        
        # 收集詞語文本
        for word_obj in lesson_data.get('詞語', []):
            text = word_obj.get('word', '')
            if text:
                texts_to_generate.append(text)
        
        # 收集段落句子文本
        for para_obj in lesson_data.get('段落', []):
            for sent_obj in para_obj.get('sentences', []):
                text = sent_obj.get('sentence', '')
                if text:
                    texts_to_generate.append(text)
        
        # 將所有文本加入 TTS 生成隊列
        print(f"[ADD_CONTENT] Queueing {len(texts_to_generate)} texts for TTS generation")
        for text in texts_to_generate:
            word_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            audio_file = os.path.join(AUDIO_DIR, f'{word_hash}.mp3')
            tts_queue.put((text, audio_file))
            print(f"[ADD_CONTENT] Queued: {text}")
        
        return jsonify({
            'status': 'success',
            'message': '內容已成功添加，正在生成音頻...',
            'lesson': {
                'language': language,
                'lesson_number': lesson_number,
                'word_count': word_count,
                'para_count': para_count,
                'is_simple': False
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_lesson_simple', methods=['POST'])
def create_lesson_simple():
    """簡化的課程創建 - 只需要課程名稱，無需語言和內容類型選擇"""
    try:
        req_data = request.get_json()
        lesson_name = req_data.get('lesson_name', '').strip()
        
        if not lesson_name:
            return jsonify({'error': '課程名稱不能為空'}), 400
        
        data = load_data()
        
        # 確保根層級存在（不再按語言分類）
        if not isinstance(data, dict):
            data = {}
        
        # 檢查課程是否已存在
        if lesson_name in data:
            return jsonify({'error': '該課程已存在'}), 400
        
        # 創建空課程結構
        lesson_data = {
            '詞語': [],
            '段落': []
        }
        
        # 保存到數據文件
        data[lesson_name] = lesson_data
        save_data(data)
        
        return jsonify({
            'status': 'success', 
            'message': '課程已成功創建',
            'lesson': {
                'language': '',
                'lesson_number': lesson_name,
                'word_count': 0,
                'para_count': 0,
                'is_simple': True
            }
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/edit_content/<lesson_name>', methods=['GET'])
def edit_content_simple(lesson_name):
    """顯示編輯頁面 - 簡化版（新流程）"""
    # 解碼 URL 參數
    lesson_name = unquote(lesson_name)
    
    data = load_data()
    
    if lesson_name not in data:
        return "課程未找到", 404
    
    lesson_content = data[lesson_name]
    
    # 使用 edit_content_new.html 模板（如果存在），否則使用改進版的 edit_content.html
    return render_template('edit_content.html',
                          language='',  # 新流程不需要語言
                          lesson_number=lesson_name,
                          content=lesson_content,
                          is_simple=True)

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
        
        # 更新段落 (新結構)
        updated_paragraphs = []
        para_id_counter = 1
        for para_data in paragraphs:
            # 查找原有的段落記錄（保留統計數據）
            original = None
            original_para_id = para_data.get('id')
            if original_para_id:
                for old_para in lesson_content.get('段落', []):
                    if old_para.get('id') == original_para_id:
                        original = old_para
                        break
            
            if original:
                # 保留原有的統計數據
                updated_para = {
                    'id': original.get('id'),
                    'title': para_data.get('title', original.get('title', '')),
                    'sentences': para_data.get('sentences', []),
                    'attempts': original.get('attempts', 0),
                    'correct': original.get('correct', 0),
                    'incorrect': original.get('incorrect', 0),
                    'history': original.get('history', [])
                }
            else:
                # 新段落
                updated_para = {
                    'id': f"para_{para_id_counter}",
                    'title': para_data.get('title', f'段落{para_id_counter}'),
                    'sentences': para_data.get('sentences', []),
                    'attempts': 0,
                    'correct': 0,
                    'incorrect': 0,
                    'history': []
                }
                para_id_counter += 1
            
            updated_paragraphs.append(updated_para)
        
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
        
        # 支持新流程：language 為 'simple' 或空字符串
        if language == 'simple' or language == '':
            # 新格式：課程直接存储在數据根級別
            if lesson_num in data:
                del data[lesson_num]
                save_data(data)
        else:
            # 舊格式：按语言分类
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

@app.route('/quiz_simple/<lesson_name>')
def quiz_simple(lesson_name):
    """聽寫練習路由 - 新簡化流程，不需要語言參數"""
    lesson_name = unquote(lesson_name)
    
    content_type = request.args.get('content_type', '詞語').strip()
    paragraph_id = request.args.get('paragraph_id', '').strip()
    
    data = load_data()
    
    # 查找簡化格式的課程
    print(f"DEBUG: Looking for lesson_name: {repr(lesson_name)}")
    print(f"DEBUG: Available keys: {[repr(k) for k in data.keys() if '17' in k]}")
    
    if lesson_name not in data:
        return "聽寫內容未找到", 404
    
    lesson_content = data[lesson_name]
    
    # 驗證是否為簡化格式（包含詞語或段落）
    if not isinstance(lesson_content, dict) or ('詞語' not in lesson_content and '段落' not in lesson_content):
        return "聽寫內容未找到", 404
    
    words_to_practice = []
    if content_type == '詞語' and '詞語' in lesson_content:
        # 詞語作為整體框，總是聽寫所有詞語
        words_to_practice = [item['word'] for item in lesson_content['詞語']]
    elif content_type == '段落' and '段落' in lesson_content:
        # 段落必須指定ID，不允許一次聽寫所有段落
        if not paragraph_id:
            return "❌ 錯誤：請選擇要聽寫的特定段落", 400
        
        # 查找指定的段落（支持 id 字段或使用索引）
        paragraphs = lesson_content.get('段落', [])
        for idx, para in enumerate(paragraphs):
            # 支持兩種方式比對：para.id 或用索引作為備選
            para_id = para.get('id') or str(idx)
            if para_id == paragraph_id:
                for sent_item in para.get('sentences', []):
                    words_to_practice.append(sent_item.get('sentence') if isinstance(sent_item, dict) else sent_item)
                break
    
    if not words_to_practice:
        return f"❌ 沒有{content_type}可以聽寫。請選擇正確的段落或課程。", 404
    
    # 預先將所有詞語/句子加入 TTS 生成隊列，避免延遲
    print(f"[QUIZ_SIMPLE] Preloading {len(words_to_practice)} items for TTS (content_type={content_type})")
    for i, word in enumerate(words_to_practice):
        word_hash = hashlib.md5(word.encode('utf-8')).hexdigest()
        audio_file = os.path.join(AUDIO_DIR, f'{word_hash}.mp3')
        if not os.path.exists(audio_file):
            print(f"[QUIZ] Queuing word {i+1}/{len(words_to_practice)}: {word}")
            tts_queue.put((word, audio_file))
        else:
            print(f"[QUIZ] Already cached: {word}")
    
    session.permanent = True
    session['current_quiz'] = {
        'language': '',
        'lesson': lesson_name,
        'content_type': content_type,
        'words': words_to_practice,
        'current_index': 0,
        'results': [],
        'is_simple': True
    }
    
    import json as json_module
    words_json = json_module.dumps(words_to_practice, ensure_ascii=False)
    
    return render_template('quiz.html', 
                          lesson_name=lesson_name, 
                          language='',
                          lesson_num=lesson_name,
                          word_count=len(words_to_practice),
                          current_word=words_to_practice[0] if words_to_practice else None,
                          words_json=words_json,
                          content_type=content_type)
@app.route('/quiz/<language>/<lesson_num>')
def quiz_new(language, lesson_num):
    """聽寫練習路由 - 支持選擇特定段落"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    content_type = request.args.get('content_type', '詞語').strip()
    paragraph_id = request.args.get('paragraph_id', '').strip()  # 特定段落ID
    print(f"[QUIZ] content_type={content_type}, paragraph_id={paragraph_id}")
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return "聽寫內容未找到", 404
    
    lesson_content = data[language][lesson_num]
    
    words_to_practice = []
    if content_type == '詞語' and '詞語' in lesson_content:
        # 詞語作為整體框，總是聽寫所有詞語
        words_to_practice = [item['word'] for item in lesson_content['詞語']]
    elif content_type == '段落' and '段落' in lesson_content:
        # 段落必須指定ID，不允許一次聽寫所有段落
        if not paragraph_id:
            return "❌ 錯誤：請選擇要聽寫的特定段落", 400
        
        # 查找指定的段落（支持 id 字段或使用索引）
        paragraphs = lesson_content.get('段落', [])
        for idx, para in enumerate(paragraphs):
            # 支持兩種方式比對：para.id 或用索引作為備選
            para_id = para.get('id') or str(idx)
            if para_id == paragraph_id:
                for sent_item in para.get('sentences', []):
                    words_to_practice.append(sent_item.get('sentence') if isinstance(sent_item, dict) else sent_item)
                break
    
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
                          language=language,
                          lesson_num=lesson_num,
                          word_count=len(words_to_practice),
                          current_word=words_to_practice[0] if words_to_practice else None,
                          words_json=words_json,
                          content_type=content_type)

def normalize_text(text):
    """Normalize text for comparison - removes extra whitespace and normalizes newlines"""
    if not isinstance(text, str):
        return ""
    # Convert all types of newlines and extra whitespace to single spaces
    normalized = ' '.join(text.split())
    return normalized

def get_chinese_char_count(text):
    """计算仅汉字的字数（不计标点、数字、英文）"""
    if not text:
        return 0
    # 统计汉字 \u4e00-\u9fff
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count

def split_by_punctuation(text):
    """第一步：按指定标点分割。分割标点：。？；：，"""
    import re
    if not text or not text.strip():
        return []
    
    # 按分割标点 。？；：， 进行分割（保留标点）
    # 使用正向后瞻保留标点在前一句末尾
    parts = re.split(r'(?<=[。？；：，])', text)
    
    # 清理空白
    sentences = [s.strip() for s in parts if s.strip()]
    return sentences

def get_target_split_count(total_chinese_count):
    """根据总字符数计算目标拆分字符数（平衡分割）"""
    if total_chinese_count <= 15:
        return -1  # 不需要分割
    
    # 根据总长度计算目标拆分字符数
    # 策略：使用较高的阈值让分割尽量不超过2段
    if total_chinese_count <= 20:
        # 15-20字的句子：使用14字的阈值，保证最多分2段且接近平衡
        target_count = 14
    elif total_chinese_count <= 25:
        # 20-25字的句子：12字的阈值
        target_count = 12
    else:
        # 超过25字的句子：使用15字的限制
        target_count = 15
    
    # 确保target_count不超过15
    return min(target_count, 15)

def split_long_sentence_by_words(sentence):
    """使用jieba分词后在词语边界处拆分长句子，优先按标点符号分割"""
    try:
        import jieba
    except ImportError:
        # 如果jieba未安装，回退到原始拆分方法
        return split_long_sentence_fallback(sentence)
    
    chinese_count = get_chinese_char_count(sentence)
    print(f"[SPLIT_BY_WORDS] Processing: '{sentence[:30]}...' ({chinese_count}字)")
    
    if chinese_count <= 15:
        return [sentence]
    
    # 第一步：尝试按标点符号分割（逗号、句号等）
    # 这是"天然"的分割点，应该优先使用
    split_punctuations = ['，', '。', '？', '！', '；', '：', '、']
    
    # 找出所有标点符号的位置
    punctuation_positions = []
    for i, char in enumerate(sentence):
        if char in split_punctuations:
            punctuation_positions.append(i)
    
    # 如果有标点符号，按标点分割
    if punctuation_positions:
        print(f"[SPLIT_BY_WORDS] Found punctuation marks at positions: {punctuation_positions}")
        result = []
        start = 0
        for pos in punctuation_positions:
            # 包括标点符号
            segment = sentence[start:pos+1]
            if segment:
                result.append(segment)
            start = pos + 1
        
        # 添加最后一部分（如果有的话）
        if start < len(sentence):
            result.append(sentence[start:])
        
        # 对每个部分再进行递归检查，如果某部分太长且没有标点，进行算法分割
        final_result = []
        for part in result:
            part_chinese_count = get_chinese_char_count(part)
            
            # 检查这个部分中是否有标点（除了已有的末尾标点）
            has_internal_punctuation = False
            for punct in split_punctuations:
                if punct in part[:-1]:  # 检查末尾标点之外的部分
                    has_internal_punctuation = True
                    break
            
            # 如果这个部分太长且没有内部标点，进行算法分割
            if part_chinese_count > 15 and not has_internal_punctuation:
                print(f"[SPLIT_BY_WORDS] Part '{part}' ({part_chinese_count}字) too long, applying algorithm...")
                sub_parts = _split_by_algorithm(part)
                final_result.extend(sub_parts)
            else:
                final_result.append(part)
        
        print(f"[SPLIT_BY_WORDS] Final result: {final_result}")
        return final_result
    
    # 第二步：如果没有标点符号，使用算法分割
    print(f"[SPLIT_BY_WORDS] No punctuation marks found, using algorithm splitting")
    result = _split_by_algorithm(sentence)
    print(f"[SPLIT_BY_WORDS] Final result: {result}")
    return result

def _split_by_algorithm(sentence):
    """使用算法分割没有标点的长句子（递归）"""
    try:
        import jieba
    except ImportError:
        return split_long_sentence_fallback(sentence)
    
    chinese_count = get_chinese_char_count(sentence)
    
    if chinese_count <= 15:
        return [sentence]
    
    # 提取末尾标点（如果有）
    final_punctuation = ''
    text_to_split = sentence
    
    for punct in ['。', '？', '；', '：', '，']:
        if sentence.endswith(punct):
            final_punctuation = punct
            text_to_split = sentence[:-1]
            break
    
    # 使用jieba进行分词
    tokens = list(jieba.cut(text_to_split))
    print(f"[SPLIT_BY_WORDS] Tokens: {tokens}")
    
    # 计算理想的分割点（总长度的一半）
    ideal_split_point = get_chinese_char_count(text_to_split) / 2
    print(f"[SPLIT_BY_WORDS] Ideal split point: {ideal_split_point} chars")
    
    # 累积tokens，找到最接近ideal_split_point的词边界
    accumulated = ''
    accumulated_count = 0
    closest_split_point = -1
    min_distance = float('inf')
    
    for token in tokens:
        token_count = get_chinese_char_count(token)
        
        # 检查这个token之前的累积是否最接近ideal_split_point
        distance = abs(accumulated_count - ideal_split_point)
        if distance < min_distance:
            min_distance = distance
            closest_split_point = accumulated_count
        
        accumulated += token
        accumulated_count += token_count
    
    # 检查最后的位置
    distance = abs(accumulated_count - ideal_split_point)
    if distance < min_distance:
        closest_split_point = accumulated_count
    
    # 如果找到了合理的分割点（不是开头也不是结尾），进行分割
    if closest_split_point > 0 and closest_split_point < accumulated_count:
        part1 = text_to_split[:closest_split_point]
        part2 = text_to_split[closest_split_point:] + final_punctuation
        
        print(f"[SPLIT_BY_WORDS] Split at {closest_split_point}: '{part1}' ({get_chinese_char_count(part1)}字)")
        print(f"[SPLIT_BY_WORDS] Remaining: '{part2}' ({get_chinese_char_count(part2)}字)")
        
        result = [part1]
        
        # 递归处理第二部分，如果它仍然太长
        if get_chinese_char_count(part2) > 15:
            print(f"[SPLIT_BY_WORDS] Part 2 still too long ({get_chinese_char_count(part2)}字), recursing...")
            sub_parts = _split_by_algorithm(part2)
            result.extend(sub_parts)
        else:
            result.append(part2)
    else:
        # 如果无法找到好的分割点，使用回退方法
        print(f"[SPLIT_BY_WORDS] Could not find good split point, using fallback method")
        result = split_long_sentence_fallback(sentence)
    
    return result


def split_long_sentence_fallback(sentence):
    """回退的递归拆分方法（当jieba无法处理时）"""
    chinese_count = get_chinese_char_count(sentence)
    
    if chinese_count <= 15:
        return [sentence]
    
    # 找到最后的标点符号（仅在末尾查找）
    final_punctuation = ''
    text_to_split = sentence
    
    # 只在句子末尾寻找标点
    for punct in ['。', '？', '；', '：', '，']:
        if sentence.endswith(punct):
            final_punctuation = punct
            text_to_split = sentence[:-1]
            break
    
    # 如果没有末尾标点，就用原句子
    if not final_punctuation:
        text_to_split = sentence
    
    # 寻找最优的拆分点
    # 优先在接近15个汉字处拆分
    split_point = find_best_split_point(text_to_split)
    
    if split_point <= 0 or split_point >= len(text_to_split):
        # 无法找到合适的拆分点，返回原句
        return [sentence]
    
    # 拆分为两部分
    part1 = text_to_split[:split_point]
    part2_body = text_to_split[split_point:]
    
    # 检查两部分的汉字数
    part1_chinese_count = get_chinese_char_count(part1)
    part2_chinese_count = get_chinese_char_count(part2_body)
    
    # 注意：不再强制要求Part2>=5字，允许任何长度的Part2
    # 这确保任何超过15字的句子都能被拆分
    
    # 如果part1仍然超过15字（这不应该发生，但防守性编程）
    # 或者part1太短（<1字），返回原句
    if part1_chinese_count < 1 or part1_chinese_count > 15:
        # 拆分失败，返回原句
        return [sentence]
    
    # 如果part2为空，返回原句
    if part2_chinese_count < 1:
        return [sentence]
    
    # 第二部分：只在最后一部分添加标点
    part2_with_punct = part2_body + final_punctuation
    
    # 递归处理第二部分（如果仍 > 15 字）
    if part2_chinese_count > 15:
        part2_splits = split_long_sentence_fallback(part2_with_punct)
        return [part1] + part2_splits
    else:
        return [part1, part2_with_punct]

def find_best_split_point(text):
    """寻找最佳拆分点（平衡分割）"""
    # 首先计算总的汉字数
    total_chinese_count = get_chinese_char_count(text)
    
    # 获取目标拆分字符数
    target_count = get_target_split_count(total_chinese_count)
    if target_count == -1:
        return -1  # 不需要分割
    
    # 寻找在目标字符数处的拆分点
    current_chinese_count = 0
    
    for i, char in enumerate(text):
        # 检查是否为汉字
        if '\u4e00' <= char <= '\u9fff':
            current_chinese_count += 1
            # 当达到目标字符数时，返回当前位置后面的位置
            if current_chinese_count == target_count:
                return i + 1
        
        # 如果已经超过目标，返回当前位置
        if current_chinese_count > target_count:
            return i
    
    # 如果文本中汉字数少于目标，返回中点
    return len(text) // 2
    
    # 如果文本中汉字数少于等于15，返回中点
    return len(text) // 2


def split_long_sentences(sentences):
    """第二步：对所有句子进行长度检查与拆分"""
    result = []
    for sentence in sentences:
        chinese_count = get_chinese_char_count(sentence)
        if chinese_count <= 15:
            # 汉字数 ≤ 15：直接采用
            result.append(sentence)
        else:
            # 汉字数 > 15：进入拆分流程
            # 优先使用基于词语的拆分
            splits = split_long_sentence_by_words(sentence)
            result.extend(splits)
    
    return result

def format_sentences_new(text):
    """新的段落格式化函数"""
    # 第一步：按指定标点分割
    sentences_by_punct = split_by_punctuation(text)
    
    # 第二步：处理长句拆分
    final_sentences = split_long_sentences(sentences_by_punct)
    
    return final_sentences

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
    
    if not word or not lesson:
        return jsonify({'error': '缺少必要參數'}), 400
    
    # Normalize word for comparison (especially for paragraphs with newlines)
    word_normalized = normalize_text(word)
    
    # 特殊处理：所有未掌握单词
    if lesson == '所有未掌握單詞':
        # 遍历所有课程查找并更新单词
        word_found = False
        for key, value in data.items():
            if isinstance(value, dict):
                # 新格式课程
                if '詞語' in value:
                    for word_item in value['詞語']:
                        if word_item['word'] == word:
                            word_item['attempts'] += 1
                            if is_known:
                                word_item['correct'] += 1
                            else:
                                word_item['incorrect'] += 1
                            
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            word_item['history'].append({
                                "timestamp": timestamp,
                                "known": is_known
                            })
                            word_found = True
                            break
                    if word_found:
                        break
                else:
                    # 旧格式课程
                    for lesson_num, lesson_content in value.items():
                        if isinstance(lesson_content, dict) and '詞語' in lesson_content:
                            for word_item in lesson_content['詞語']:
                                if word_item['word'] == word:
                                    word_item['attempts'] += 1
                                    if is_known:
                                        word_item['correct'] += 1
                                    else:
                                        word_item['incorrect'] += 1
                                    
                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    word_item['history'].append({
                                        "timestamp": timestamp,
                                        "known": is_known
                                    })
                                    word_found = True
                                    break
                            if word_found:
                                break
                if word_found:
                    break
        
        if not word_found:
            return jsonify({'error': f'找不到單詞: {word}'}), 400
    else:
        # 普通课程处理
        # Validate data structure
        try:
            # Support both old format (language/lesson) and new format (direct lesson)
            if language and language in data and lesson in data[language]:
                # Old format: language/lesson
                lesson_data = data[language][lesson]
            elif not language and lesson in data:
                # New format: direct lesson
                lesson_data = data[lesson]
            else:
                return jsonify({'error': f'找不到課程: {language or ""}/{lesson}'}), 400
        except KeyError:
            return jsonify({'error': f'找不到課程: {language or ""}/{lesson}'}), 400
        
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
            # Handle paragraph/sentence entries (新結構：同時更新段落和句子的統計)
            for para in lesson_data['段落']:
                for sent_item in para.get('sentences', []):
                    sent_text = sent_item.get('sentence') if isinstance(sent_item, dict) else sent_item
                    # Normalize both texts for comparison (handles newlines and whitespace differences)
                    sent_text_normalized = normalize_text(sent_text)
                    if sent_text_normalized == word_normalized or sent_text == word:
                        # 更新句子統計
                        if isinstance(sent_item, dict):
                            sent_item['attempts'] = sent_item.get('attempts', 0) + 1
                            if is_known:
                                sent_item['correct'] = sent_item.get('correct', 0) + 1
                            else:
                                sent_item['incorrect'] = sent_item.get('incorrect', 0) + 1
                            
                            # Record history for sentence
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if 'history' not in sent_item:
                                sent_item['history'] = []
                            sent_item['history'].append({
                                "timestamp": timestamp,
                                "known": is_known
                            })
                        
                        # 同時更新段落統計 (新結構)
                        para['attempts'] = para.get('attempts', 0) + 1
                        if is_known:
                            para['correct'] = para.get('correct', 0) + 1
                        else:
                            para['incorrect'] = para.get('incorrect', 0) + 1
                        
                        # Record history for paragraph
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if 'history' not in para:
                            para['history'] = []
                        para['history'].append({
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


@app.route('/review_simple/<lesson_name>')
def review_simple(lesson_name):
    """複習路由 - 新簡化流程，不需要語言參數"""
    lesson_name = unquote(lesson_name)
    
    data = load_data()
    
    if lesson_name not in data:
        return "聽寫內容未找到", 404
    
    lesson_content = data[lesson_name]
    
    # Collect words needing review
    review_words = []
    if '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            if item['attempts'] == 0:
                accuracy = 0
                accuracy_display = "未測試"
            else:
                accuracy = item['correct'] / item['attempts']
                accuracy_display = round(accuracy * 100, 1)
            
            if accuracy < 0.75:
                review_words.append({
                    'word': item['word'],
                    'meaning': item['meaning'],
                    'attempts': item['attempts'],
                    'correct': item['correct'],
                    'incorrect': item['incorrect'],
                    'accuracy': accuracy,
                    'accuracy_display': accuracy_display
                })
    
    # Sort
    review_words.sort(key=lambda x: (x['attempts'] > 0, x['accuracy']))
    
    return render_template('review.html', 
                          lesson_name=lesson_name, 
                          language='',
                          lesson_num=lesson_name,
                          review_words=review_words,
                          review_paragraphs=[])

@app.route('/review/<language>/<lesson_num>')
def review_new(language, lesson_num):
    """複習路由 - 显示词语和段落的复习选项"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return "聽寫內容未找到", 404
    
    lesson_content = data[language][lesson_num]
    
    # Collect words needing review
    review_words = []
    if '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            if item['attempts'] == 0:
                accuracy = 0
                accuracy_display = "未測試"
            else:
                accuracy = item['correct'] / item['attempts']
                accuracy_display = round(accuracy * 100, 1)
            
            if accuracy < 0.75:
                review_words.append({
                    'word': item['word'],
                    'meaning': item['meaning'],
                    'attempts': item['attempts'],
                    'correct': item['correct'],
                    'incorrect': item['incorrect'],
                    'accuracy': accuracy,
                    'accuracy_display': accuracy_display
                })
    
    # Collect paragraphs/sentences needing review
    review_paragraphs = []
    if '段落' in lesson_content:
        for para in lesson_content['段落']:
            para_info = {
                'title': para.get('title', ''),
                'sentences': []
            }
            for sent_item in para.get('sentences', []):
                if sent_item['attempts'] == 0:
                    accuracy = 0
                    accuracy_display = "未測試"
                else:
                    accuracy = sent_item['correct'] / sent_item['attempts']
                    accuracy_display = round(accuracy * 100, 1)
                
                if accuracy < 0.75:
                    para_info['sentences'].append({
                        'sentence': sent_item['sentence'],
                        'attempts': sent_item['attempts'],
                        'correct': sent_item['correct'],
                        'incorrect': sent_item['incorrect'],
                        'accuracy': accuracy,
                        'accuracy_display': accuracy_display
                    })
            
            if para_info['sentences']:
                review_paragraphs.append(para_info)
    
    # Sort
    review_words.sort(key=lambda x: (x['attempts'] > 0, x['accuracy']))
    
    display_name = f"{language} - {lesson_num}"
    return render_template('review.html', 
                          lesson_name=display_name, 
                          language=language,
                          lesson_num=lesson_num,
                          review_words=review_words,
                          review_paragraphs=review_paragraphs)

@app.route('/review_quiz/<language>/<lesson_num>')
def review_quiz(language, lesson_num):
    """複習未掌握內容的聽寫測試 - 支持詞語和段落"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    content_type = request.args.get('content_type', '詞語').strip()
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return "聽寫內容未找到", 404
    
    lesson_content = data[language][lesson_num]
    
    # Get only items that need review (accuracy < 0.75)
    items_to_review = []
    
    if content_type == '詞語' and '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            if item['attempts'] == 0:
                accuracy = 0
            else:
                accuracy = item['correct'] / item['attempts']
            
            if accuracy < 0.75:
                items_to_review.append(item['word'])
    
    elif content_type == '段落' and '段落' in lesson_content:
        for para in lesson_content['段落']:
            for sent_item in para.get('sentences', []):
                if sent_item['attempts'] == 0:
                    accuracy = 0
                else:
                    accuracy = sent_item['correct'] / sent_item['attempts']
                
                if accuracy < 0.75:
                    items_to_review.append(sent_item['sentence'])
    
    if not items_to_review:
        return render_template('review.html', 
                              lesson_name=f"{language} - {lesson_num}",
                              language=language,
                              lesson_num=lesson_num,
                              review_words=[],
                              review_paragraphs=[],
                              message=f"所有{content_type}已掌握，無需複習！")
    
    session.permanent = True
    session['current_quiz'] = {
        'language': language,
        'lesson': lesson_num,
        'content_type': content_type,
        'words': items_to_review,
        'current_index': 0,
        'results': [],
        'is_review': True
    }
    
    import json as json_module
    items_json = json_module.dumps(items_to_review, ensure_ascii=False)
    
    display_name = f"{language} - {lesson_num}"
    return render_template('quiz.html', 
                          lesson_name=display_name, 
                          language=language,
                          lesson_num=lesson_num,
                          word_count=len(items_to_review),
                          current_word=items_to_review[0] if items_to_review else None,
                          words_json=items_json,
                          content_type=content_type,
                          is_review=True)

@app.route('/api/lesson/<language>/<lesson_num>/stats')
def lesson_stats_api(language, lesson_num):
    """統計API - 返回JSON"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return jsonify({'error': '聽寫內容未找到'}), 404
    
    lesson_content = data[language][lesson_num]
    
    total_items = 0
    mastered = 0
    needs_review = 0
    
    # Count words (詞語)
    if '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            total_items += 1
            
            # Only count tested words (attempts > 0) for statistics
            if item['attempts'] > 0:
                accuracy = item['correct'] / item['attempts']
                if accuracy >= 0.75:
                    mastered += 1
                else:
                    needs_review += 1
            else:
                # Untested words are counted in needs_review
                needs_review += 1
    
    # Count sentences in paragraphs (段落)
    if '段落' in lesson_content:
        for para in lesson_content['段落']:
            for sent in para.get('sentences', []):
                total_items += 1
                
                if sent['attempts'] > 0:
                    accuracy = sent['correct'] / sent['attempts']
                    if accuracy >= 0.75:
                        mastered += 1
                    else:
                        needs_review += 1
                else:
                    # Untested sentences are counted in needs_review
                    needs_review += 1
    
    return jsonify({
        'total_words': total_items,
        'mastered': mastered,
        'needs_review': needs_review,
        'mastered_percentage': round((mastered / total_items) * 100, 1) if total_items > 0 else 0
    })

@app.route('/stats_simple/<lesson_name>')
def stats_simple(lesson_name):
    """統計頁面 - 新簡化流程，不需要語言參數"""
    lesson_name = unquote(lesson_name)
    
    data = load_data()
    
    if lesson_name not in data:
        return "聽寫內容未找到", 404
    
    lesson_content = data[lesson_name]
    
    # Collect word statistics
    word_stats = {
        'total': 0,
        'mastered': 0,
        'needs_review': 0,
        'words': []
    }
    
    if '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            word_stats['total'] += 1
            
            if item['attempts'] == 0:
                status = '未測試'
                accuracy = 0
                word_stats['needs_review'] += 1
            else:
                accuracy = item['correct'] / item['attempts']
                if accuracy >= 0.75:
                    status = '已掌握'
                    word_stats['mastered'] += 1
                else:
                    status = '需複習'
                    word_stats['needs_review'] += 1
            
            word_stats['words'].append({
                'word': item['word'],
                'meaning': item['meaning'],
                'attempts': item['attempts'],
                'correct': item['correct'],
                'incorrect': item['incorrect'],
                'accuracy': round(accuracy * 100, 1) if item['attempts'] > 0 else 0,
                'status': status
            })
    
    # Collect paragraph statistics
    para_stats = {
        'total': 0,
        'mastered': 0,
        'needs_review': 0,
        'paragraphs': []
    }
    
    if '段落' in lesson_content:
        for para in lesson_content['段落']:
            para_id = para.get('id', '')
            para_info = {
                'id': para_id,
                'title': para['title'],
                'total': 0,
                'mastered': 0,
                'needs_review': 0,
                'sentences': [],
                'para_attempts': para.get('attempts', 0),
                'para_correct': para.get('correct', 0),
                'para_incorrect': para.get('incorrect', 0)
            }
            
            for sent in para.get('sentences', []):
                para_stats['total'] += 1
                para_info['total'] += 1
                
                if sent['attempts'] == 0:
                    status = '未測試'
                    accuracy = 0
                    para_stats['needs_review'] += 1
                    para_info['needs_review'] += 1
                else:
                    accuracy = sent['correct'] / sent['attempts']
                    if accuracy >= 0.75:
                        status = '已掌握'
                        para_stats['mastered'] += 1
                        para_info['mastered'] += 1
                    else:
                        status = '需複習'
                        para_stats['needs_review'] += 1
                        para_info['needs_review'] += 1
                
                para_info['sentences'].append({
                    'sentence': sent['sentence'],
                    'attempts': sent['attempts'],
                    'correct': sent['correct'],
                    'incorrect': sent['incorrect'],
                    'accuracy': round(accuracy * 100, 1) if sent['attempts'] > 0 else 0,
                    'status': status
                })
            
            para_stats['paragraphs'].append(para_info)
    
    # Calculate overall stats - only count words, not paragraphs
    total_items = word_stats['total']
    total_mastered = word_stats['mastered']
    total_needs_review = word_stats['needs_review']
    overall_percentage = round((total_mastered / total_items) * 100, 1) if total_items > 0 else 0
    
    return render_template('stats.html',
                          lesson_name=lesson_name,
                          language='',
                          lesson_num=lesson_name,
                          total_items=total_items,
                          total_mastered=total_mastered,
                          total_needs_review=total_needs_review,
                          overall_percentage=overall_percentage,
                          word_stats=word_stats,
                          para_stats=para_stats)

@app.route('/stats/<language>/<lesson_num>')
def lesson_stats_new(language, lesson_num):
    """統計頁面 - 返回HTML"""
    language = unquote(language)
    lesson_num = unquote(lesson_num)
    
    data = load_data()
    
    # 支持新格式（language 為空）和舊格式
    if language and language in data and lesson_num in data[language]:
        # 舊格式：language/lesson
        lesson_content = data[language][lesson_num]
    elif not language and lesson_num in data:
        # 新格式：直接 lesson
        lesson_content = data[lesson_num]
    else:
        return "聽寫內容未找到", 404
    
    # Collect word statistics
    word_stats = {
        'total': 0,
        'mastered': 0,
        'needs_review': 0,
        'words': []  # Changed from 'items' to 'words'
    }
    
    if '詞語' in lesson_content:
        for item in lesson_content['詞語']:
            word_stats['total'] += 1
            
            if item['attempts'] == 0:
                status = '未測試'
                accuracy = 0
                word_stats['needs_review'] += 1
            else:
                accuracy = item['correct'] / item['attempts']
                if accuracy >= 0.75:
                    status = '已掌握'
                    word_stats['mastered'] += 1
                else:
                    status = '需複習'
                    word_stats['needs_review'] += 1
            
            word_stats['words'].append({
                'word': item['word'],
                'meaning': item['meaning'],
                'attempts': item['attempts'],
                'correct': item['correct'],
                'incorrect': item['incorrect'],
                'accuracy': round(accuracy * 100, 1) if item['attempts'] > 0 else 0,
                'status': status
            })
    
    # Collect paragraph statistics
    para_stats = {
        'total': 0,
        'mastered': 0,
        'needs_review': 0,
        'paragraphs': []
    }
    
    if '段落' in lesson_content:
        for para in lesson_content['段落']:
            para_id = para.get('id', '')
            para_info = {
                'id': para_id,
                'title': para['title'],
                'total': 0,
                'mastered': 0,
                'needs_review': 0,
                'sentences': [],
                'para_attempts': para.get('attempts', 0),
                'para_correct': para.get('correct', 0),
                'para_incorrect': para.get('incorrect', 0)
            }
            
            for sent in para.get('sentences', []):
                para_stats['total'] += 1
                para_info['total'] += 1
                
                if sent['attempts'] == 0:
                    status = '未測試'
                    accuracy = 0
                    para_stats['needs_review'] += 1
                    para_info['needs_review'] += 1
                else:
                    accuracy = sent['correct'] / sent['attempts']
                    if accuracy >= 0.75:
                        status = '已掌握'
                        para_stats['mastered'] += 1
                        para_info['mastered'] += 1
                    else:
                        status = '需複習'
                        para_stats['needs_review'] += 1
                        para_info['needs_review'] += 1
                
                para_info['sentences'].append({
                    'sentence': sent['sentence'],
                    'attempts': sent['attempts'],
                    'correct': sent['correct'],
                    'incorrect': sent['incorrect'],
                    'accuracy': round(accuracy * 100, 1) if sent['attempts'] > 0 else 0,
                    'status': status
                })
            
            para_stats['paragraphs'].append(para_info)
    
    # Calculate overall stats - only count words, not paragraphs
    total_items = word_stats['total']
    total_mastered = word_stats['mastered']
    total_needs_review = word_stats['needs_review']
    overall_percentage = round((total_mastered / total_items) * 100, 1) if total_items > 0 else 0
    
    display_name = lesson_num if not language else f"{language} - {lesson_num}"
    
    return render_template('stats.html',
                          lesson_name=display_name,
                          language=language,
                          lesson_num=lesson_num,
                          total_items=total_items,
                          total_mastered=total_mastered,
                          total_needs_review=total_needs_review,
                          overall_percentage=overall_percentage,
                          word_stats=word_stats,
                          para_stats=para_stats)

@app.route('/save_content', methods=['POST'])
def save_content():
    """Save edited content from textarea format - 支持新舊流程"""
    try:
        req_data = request.get_json()
        print(f"[SAVE] Received request: {type(req_data)}")
        
        language = req_data.get('language', '')
        lesson = req_data.get('lesson')
        words = req_data.get('words', [])
        paragraphs = req_data.get('paragraphs', [])
        is_simple = req_data.get('is_simple', False)
        
        print(f"[SAVE] Lesson: {lesson}, Language: {language}, Is_simple: {is_simple}")
        print(f"[SAVE] Words: {len(words)}, Paragraphs: {len(paragraphs)}")
        
        if not lesson:
            return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
        
        data = load_data()
        print(f"[SAVE] Data loaded, total lessons: {len(data)}")
        print(f"[SAVE] Available lessons: {list(data.keys())}")
        print(f"[SAVE] Looking for lesson: '{lesson}' (is_simple={is_simple}, language='{language}')")
        
        # 支持兩種數據結構：新流程（無語言）和舊流程（有語言）
        if is_simple or not language:
            # 新流程：直接在數據根層級查找課程
            if lesson not in data:
                print(f"[SAVE] ERROR: Lesson '{lesson}' not found in root level")
                print(f"[SAVE] Available lessons: {list(data.keys())}")
                return jsonify({'status': 'error', 'message': f'課程未找到: {lesson}'}), 404
            lesson_content = data[lesson]
        else:
            # 舊流程：通過語言和課程查找
            if language not in data or lesson not in data[language]:
                print(f"[SAVE] ERROR: Language '{language}' or lesson '{lesson}' not found in language level")
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
            
            for para_idx, para_data in enumerate(paragraphs):
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
                    # 检查和清理空白文本
                    if not sent_text or not isinstance(sent_text, str):
                        print(f"[SAVE] ⚠ Skipping invalid sentence: {repr(sent_text)}")
                        continue
                    
                    sent_text = sent_text.strip()
                    if not sent_text:
                        print(f"[SAVE] ⚠ Skipping empty sentence after strip")
                        continue
                    
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
                
                # Generate paragraph ID (use index as ID)
                para_id = str(para_idx)
                
                # Calculate paragraph statistics from sentences
                para_attempts = sum(s.get('attempts', 0) for s in updated_sentences)
                para_correct = sum(s.get('correct', 0) for s in updated_sentences)
                para_history = []
                for s in updated_sentences:
                    para_history.extend(s.get('history', []))
                # 按时间戳排序
                para_history = sorted(para_history, key=lambda x: x.get('timestamp', ''))
                
                updated_paragraphs.append({
                    'id': para_id,
                    'title': title,
                    'sentences': updated_sentences,
                    'attempts': para_attempts,
                    'correct': para_correct,
                    'history': para_history
                })
            
            lesson_content['段落'] = updated_paragraphs
        
        # Save the updated data
        save_data(data)
        
        # 计算词语和段落数量
        word_count = len(lesson_content.get('詞語', []))
        para_count = len(lesson_content.get('段落', []))
        
        # 收集所有需要生成的文本
        texts_to_generate = []
        
        # 添加词语
        for word_obj in lesson_content.get('詞語', []):
            text = word_obj.get('word', '')
            if text:
                texts_to_generate.append(text)
        
        # 添加段落中的句子
        for para_obj in lesson_content.get('段落', []):
            for sent_obj in para_obj.get('sentences', []):
                text = sent_obj.get('sentence', '')
                if text:
                    texts_to_generate.append(text)
        
        # ✓ 同步生成音频：阻塞等待所有文件生成完成，确保可靠性
        print(f"[SAVE] Starting synchronous TTS generation for lesson: {lesson}")
        print(f"[SAVE] Generating {len(texts_to_generate)} audio files...")
        
        generated_count = 0
        failed_texts = []
        
        for idx, text in enumerate(texts_to_generate, 1):
            word_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            audio_file = os.path.join(AUDIO_DIR, f'{word_hash}.mp3')
            
            # 检查文件是否已存在且有效
            if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                file_size = os.path.getsize(audio_file)
                print(f"[SAVE]   [{idx}/{len(texts_to_generate)}] [OK] Cached: '{text}' ({file_size} bytes)")
                generated_count += 1
                continue
            
            # 生成新文件
            print(f"[SAVE]   [{idx}/{len(texts_to_generate)}] Generating: '{text}'...")
            max_retries = 5
            success = False
            
            for attempt in range(1, max_retries + 1):
                try:
                    tts = gTTS_lib(text=text, lang='zh-CN', slow=False)
                    tts.save(audio_file)
                    
                    # 验证文件
                    if os.path.exists(audio_file):
                        file_size = os.path.getsize(audio_file)
                        if file_size > 0:
                            os.chmod(audio_file, 0o644)
                            print(f"[SAVE]   [{idx}/{len(texts_to_generate)}] [OK] Generated: '{text}' ({file_size} bytes)")
                            generated_count += 1
                            success = True
                            break
                        else:
                            print(f"[SAVE]   [{idx}/{len(texts_to_generate)}] [WARN] Empty file for: '{text}'")
                    else:
                        print(f"[SAVE]   [{idx}/{len(texts_to_generate)}] [WARN] File not created for: '{text}'")
                    
                except Exception as e:
                    error_type = type(e).__name__
                    print(f"[SAVE]   [{idx}/{len(texts_to_generate)}] [FAIL] Attempt {attempt}/{max_retries} failed ({error_type}): {str(e)[:80]}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries and not success:
                    wait_time = 0.5 * attempt  # 0.5s, 1s, 1.5s, 2s, 2.5s
                    print(f"[SAVE]      Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            if not success:
                print(f"[SAVE]   [{idx}/{len(texts_to_generate)}] [FAIL] FAILED: '{text}'")
                failed_texts.append(text)
        
        print(f"[SAVE] [OK] Generation complete: {generated_count}/{len(texts_to_generate)} successful")
        if failed_texts:
            print(f"[SAVE] [WARN] Failed files: {failed_texts}")
        
        # 返回课程元数据供前端记录到最近访问
        return jsonify({
            'status': 'success', 
            'message': f'內容已保存！{generated_count}/{len(texts_to_generate)} 个音频文件已生成。',
            'text_count': len(texts_to_generate),
            'generated_count': generated_count,
            'failed_texts': failed_texts,
            'lesson': {
                'language': language,
                'lesson_number': lesson,
                'word_count': word_count,
                'para_count': para_count,
                'is_simple': is_simple
            }
        })
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"\n[SAVE] [ERROR] ERROR occurred:")
        print(f"[SAVE] Error type: {type(e).__name__}")
        print(f"[SAVE] Error message: {str(e)}")
        print(f"[SAVE] Full traceback:")
        print(error_traceback)
        print(f"[SAVE] END OF TRACEBACK\n")
        
        return jsonify({
            'status': 'error', 
            'message': f'{type(e).__name__}: {str(e)}',
            'traceback': error_traceback
        }), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("\n[STARTUP] Starting Flask app...")
    print("[STARTUP] TTS engine ready")
    print("[STARTUP] Loading data...")
    try:
        data = load_data()
        print(f"[STARTUP] Data loaded: {len(data)} courses")
    except Exception as e:
        print(f"[STARTUP] Error loading data: {e}")
    
    # 禁用自动重加载以防止 TTS 线程重复启动
    print("[STARTUP] Starting Flask on http://127.0.0.1:5002")
    app.run(debug=False, host='127.0.0.1', port=5002, use_reloader=False)