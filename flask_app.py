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
                        max_retries = 3
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
                                    # 确保文件权限正确
                                    os.chmod(audio_file, 0o644)
                                    print(f"[TTS] ✓ Generated successfully: {word} -> {audio_file} ({file_size} bytes)")
                                    success = True
                                else:
                                    print(f"[TTS] ✗ File was not created after save() call for: {word}")
                                    retry_count += 1
                                    if retry_count < max_retries:
                                        wait_time = 2 ** retry_count
                                        print(f"[TTS] Retrying in {wait_time}s...")
                                        time.sleep(wait_time)
                                    
                            except Exception as gen_err:
                                retry_count += 1
                                if retry_count < max_retries:
                                    wait_time = 2 ** retry_count  # 指数退避：2s, 4s, 8s
                                    print(f"[TTS] ✗ Generation error for '{word}': {str(gen_err)}. Retrying in {wait_time}s...")
                                    time.sleep(wait_time)
                                else:
                                    print(f"[TTS] ✗ Final generation error for '{word}' after {max_retries} attempts: {str(gen_err)}")
                        
                        if not success:
                            print(f"[TTS] ✗ FAILED to generate audio for: {word}")
                    else:
                        file_size = os.path.getsize(audio_file)
                        print(f"[TTS] ✓ Already cached: {word} ({file_size} bytes)")
                    
                    # 在两个请求之间添加延迟，避免 gTTS API 限制
                    time.sleep(1)
                    tts_queue.task_done()
                except Exception as e:
                    print(f"[TTS] ✗ Worker Error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(1)
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
                word_count = len(value.get('詞語', []))
                para_count = len(value.get('段落', []))
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
                        word_count = len(lesson_content.get('詞語', []))
                        para_count = len(lesson_content.get('段落', []))
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
                         content_type='詞語')

@app.route('/tts/<word>')
def generate_tts(word):
    """获取或生成音频文件 URL"""
    if not tts_engine:
        print("[TTS] TTS engine not available")
        return jsonify({'error': 'TTS engine not available'}), 500
    
    try:
        # 解码 URL 编码的词语
        word = unquote(word)
        print(f"[TTS] Request for: {word}")
        
        # 生成文件名（使用MD5哈希避免重复生成）
        word_hash = hashlib.md5(word.encode('utf-8')).hexdigest()
        audio_file = os.path.join(AUDIO_DIR, f'{word_hash}.mp3')
        
        # 检查缓存中是否已有该音频文件
        file_exists = os.path.exists(audio_file)
        if file_exists:
            file_size = os.path.getsize(audio_file)
            print(f"[TTS] ✓ Cache hit: {word} ({file_size} bytes)")
        else:
            print(f"[TTS] Cache miss: {word}")
        
        if not file_exists:
            # 将任务加入队列，由后台线程处理
            print(f"[TTS] Queueing for generation: {word}")
            tts_queue.put((word, audio_file))
            
            # 给后台线程时间生成文件（最多等待20秒，每200ms检查一次）
            print(f"[TTS] Waiting for file generation (up to 20s)...")
            for i in range(100):
                if os.path.exists(audio_file):
                    file_size = os.path.getsize(audio_file)
                    print(f"[TTS] ✓ File generated after {i*200}ms ({file_size} bytes)")
                    break
                time.sleep(0.2)
            
            if not os.path.exists(audio_file):
                print(f"[TTS] ✗ Timeout: File still not generated after 20s for: {word}")
        
        # 生成绝对路径URL，确保在不同域名下也能工作
        audio_url = f'/static/audio/{word_hash}.mp3?v={int(time.time())}'
        
        # 检查文件是否存在（用于客户端验证）
        file_ready = os.path.exists(audio_file)
        
        if file_ready:
            file_size = os.path.getsize(audio_file)
            print(f"[TTS] ✓ Returning URL: {word} (ready={file_ready}, size={file_size} bytes)")
        else:
            print(f"[TTS] ⚠ Returning URL but file not ready: {word}")
        
        return jsonify({
            'success': True,
            'url': audio_url,
            'cached': file_exists,
            'ready': file_ready,
            'word': word,
            'hash': word_hash
        })
    except Exception as e:
        print(f"[TTS] ✗ Error: {str(e)}")
        import traceback
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
        # 如果指定了段落ID，只選擇該段落
        if paragraph_id:
            for para in lesson_content['段落']:
                if para.get('id') == paragraph_id:
                    for sent_item in para.get('sentences', []):
                        words_to_practice.append(sent_item.get('sentence') if isinstance(sent_item, dict) else sent_item)
                    break
        else:
            # 沒有指定段落ID，則選擇所有段落
            for para in lesson_content['段落']:
                for sent_item in para.get('sentences', []):
                    words_to_practice.append(sent_item.get('sentence') if isinstance(sent_item, dict) else sent_item)
    
    if not words_to_practice:
        return f"沒有{content_type}可以聽寫", 404
    
    # 預先將所有詞語加入 TTS 生成隊列，避免延遲
    print(f"[QUIZ] Preloading {len(words_to_practice)} words for TTS")
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
    
    data = load_data()
    
    if language not in data or lesson_num not in data[language]:
        return "聽寫內容未找到", 404
    
    lesson_content = data[language][lesson_num]
    
    words_to_practice = []
    if content_type == '詞語' and '詞語' in lesson_content:
        # 詞語作為整體框，總是聽寫所有詞語
        words_to_practice = [item['word'] for item in lesson_content['詞語']]
    elif content_type == '段落' and '段落' in lesson_content:
        # 如果指定了段落ID，只選擇該段落
        if paragraph_id:
            for para in lesson_content['段落']:
                if para.get('id') == paragraph_id:
                    for sent_item in para.get('sentences', []):
                        words_to_practice.append(sent_item.get('sentence') if isinstance(sent_item, dict) else sent_item)
                    break
        else:
            # 沒有指定段落ID，則選擇所有段落
            for para in lesson_content['段落']:
                for sent_item in para.get('sentences', []):
                    words_to_practice.append(sent_item.get('sentence') if isinstance(sent_item, dict) else sent_item)
    
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
                    if sent_text == word:
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
    
    # Calculate overall stats (only for words)
    overall_percentage = round((word_stats['mastered'] / word_stats['total']) * 100, 1) if word_stats['total'] > 0 else 0
    
    return render_template('stats.html',
                          lesson_name=lesson_name,
                          language='',
                          lesson_num=lesson_name,
                          overall_percentage=overall_percentage,
                          word_stats=word_stats,
                          para_stats={'total': 0, 'mastered': 0, 'paragraphs': []})

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
    
    # Calculate overall stats
    total_items = word_stats['total'] + para_stats['total']
    total_mastered = word_stats['mastered'] + para_stats['mastered']
    total_needs_review = word_stats['needs_review'] + para_stats['needs_review']
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
        
        language = req_data.get('language', '')
        lesson = req_data.get('lesson')
        words = req_data.get('words', [])
        paragraphs = req_data.get('paragraphs', [])
        is_simple = req_data.get('is_simple', False)
        
        if not lesson:
            return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
        
        data = load_data()
        
        # 支持兩種數據結構：新流程（無語言）和舊流程（有語言）
        if is_simple or not language:
            # 新流程：直接在數據根層級查找課程
            if lesson not in data:
                return jsonify({'status': 'error', 'message': '課程未找到'}), 404
            lesson_content = data[lesson]
        else:
            # 舊流程：通過語言和課程查找
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
        
        # 计算词语和段落数量
        word_count = len(lesson_content.get('詞語', []))
        para_count = len(lesson_content.get('段落', []))
        
        # 保存后，立即生成所有词语和段落的音频
        print(f"[SAVE] Triggering TTS generation for lesson: {lesson}")
        
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
        
        # 将所有文本加入 TTS 生成队列
        print(f"[SAVE] Queueing {len(texts_to_generate)} texts for TTS generation")
        for text in texts_to_generate:
            word_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            audio_file = os.path.join(AUDIO_DIR, f'{word_hash}.mp3')
            # 即使文件已存在也重新加入队列，确保内容更新时重新生成
            tts_queue.put((text, audio_file))
            print(f"[SAVE] Queued: {text}")
        
        # 返回课程元数据供前端记录到最近访问
        return jsonify({
            'status': 'success', 
            'message': '內容已保存，正在生成音频...', 
            'text_count': len(texts_to_generate),
            'lesson': {
                'language': language,
                'lesson_number': lesson,
                'word_count': word_count,
                'para_count': para_count,
                'is_simple': is_simple
            }
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # 禁用自动重加载以防止 TTS 线程重复启动
    app.run(debug=True, host='127.0.0.1', port=5002, use_reloader=False)