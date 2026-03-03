# AI Coding Assistant Instructions - Vocabulary Learning Assistant

## Project Overview

This is a Flask-based Chinese vocabulary learning web application featuring:
- **Core Feature**: Listening comprehension exercises with auto-generated speech (gTTS)
- **Learning Types**: Two parallel systems - "詞語" (words) and "段落" (sentence paragraphs)
- **Progress Tracking**: Mastery calculated as 75% accuracy threshold
- **Data**: Persistent JSON storage (`vocabulary_data.json`)
- **UI**: Dual-format support (legacy multi-language structure + new simplified structure)

**Start**: `python flask_app.py` → http://127.0.0.1:5002

## Critical Architecture Patterns

### Dual Data Format Support (Legacy Compatibility)
The codebase supports TWO JSON structures simultaneously:

**Old Format** (multi-language lessons):
```json
{
  "中文": {
    "第一課": { "詞語": [...], "段落": [...] }
  }
}
```

**New Format** (simplified):
```json
{
  "Lesson1": { "詞語": [...], "段落": [...] }
}
```

**Key Pattern**: Check `if '詞語' in value or '段落' in value` to detect new format, else iterate nested structure. See [flask_app.py#L220-L280](flask_app.py#L220-L280) for examples. Both formats must remain functional during any edits.

### Sentence Splitting Algorithm
Long paragraphs auto-split into ≤15 Chinese characters per segment (from [SENTENCE_SPLITTING_DESIGN.md](SENTENCE_SPLITTING_DESIGN.md)):
- **Count only Chinese characters** (Unicode `\u4e00-\u9fff`), ignore punctuation/numbers/English
- **Priority**: Find exact 15-char boundary, fallback to nearest safe position
- **Recursive split** if segment still > 15 chars
- **Preserve original punctuation** on final segment (for TTS clarity)

This is handled during lesson creation/editing, not runtime.

### Data Structure: Words & Paragraphs
Every word and paragraph tracks:
```json
{
  "word": "詞語",
  "meaning": "optional meaning",
  "attempts": 0,
  "correct": 0,
  "incorrect": 0,
  "history": [{"timestamp": "...", "known": true|false}]
}
```

**Mastery Rule**: `attempts > 0 && correct/attempts >= 0.75` → "Mastered"

## Critical Routes & Workflows

### Quiz/Testing Workflow
1. **`/quiz/<language>/<lesson>` OR `/quiz_simple/<lesson_name>`** - Renders quiz page
2. **`/submit_answer` (POST)** - Records attempt, updates word/paragraph stats
3. **Key URL Parameter**: `?content_type=詞語|段落&paragraph_id=para_1` selects specific content

**Example**: `/quiz/中文/第一課?content_type=段落&paragraph_id=para_2` tests only paragraph 2.

### Audio Generation (Background TTS)
- **Route**: `/tts/<word>` returns cached audio file or queues gTTS generation
- **Threading**: Single background worker (daemon thread, see [flask_app.py#L70-L130](flask_app.py#L70-L130)) processes queue with retry logic
- **Cache**: Stored in `static/audio/` with MD5 hash filenames
- **Rate Limit**: 0.5s delay between gTTS requests to avoid API throttling

## Key File Purposes

| File | Purpose |
|------|---------|
| [flask_app.py](flask_app.py) | All routes, data ops, quiz logic, TTS queue management |
| [vocabulary_trainer.py](vocabulary_trainer.py) | Standalone trainer class (minimal UI, rarely used) |
| [vocabulary_data.json](vocabulary_data.json) | Persistent state (lessons, word stats, history) |
| `templates/quiz.html` | Main quiz interface (word/paragraph selection, answer form) |
| `templates/vocab_list.html` | Lesson browser with edit/delete buttons, per-paragraph quiz triggers |
| `static/audio/` | Cached audio files (deleted files may be regenerated) |

## Common Development Patterns

### Loading Data with Format Detection
```python
data = load_data()
for key, value in data.items():
    if isinstance(value, dict) and ('詞語' in value or '段落' in value):
        # New format: key is lesson name, value is lesson data
        lesson_name = key
    else:
        # Old format: key is language, value contains lessons
        for lesson_num, lesson_content in value.items():
            # lesson_content has '詞語' and '段落'
```
Used in [submit_answer](flask_app.py#L1211), [get_unmastered_words](flask_app.py#L335), all quiz routes.

### Updating Statistics (After Quiz Submit)
1. Find the specific word/sentence in lesson's `詞語` or `段落[i].sentences`
2. Increment `attempts`, update `correct`/`incorrect`, append to `history`
3. Call `save_data(data)` to persist (overwrites entire JSON)

### URL Construction for Tests
- Simple format: `/quiz_simple/課程名`
- Old format: `/quiz/語言/課程號?content_type=詞語|段落`
- New format: `/quiz/課程名?content_type=詞語|段落&paragraph_id=para_1` (reuses same route, auto-detects format)

## Important Technical Notes

1. **No Database**: Pure JSON file. All edits must `save_data()` to persist.
2. **CORS Enabled** for `/tts/*` and `/static/*` (see [flask_app.py#L17-L19](flask_app.py#L17-L19)).
3. **Template Auto-Reload** enabled; session caching disabled for dev convenience (see [flask_app.py#L28-L32](flask_app.py#L28-L32)).
4. **TTS Daemon Thread**: Runs forever; errors logged but don't crash app. Check console output `[TTS]` tags.
5. **Timestamp Format**: `"YYYY-MM-DD HH:MM:SS"` (see [flask_app.py#L1200](flask_app.py#L1200)).

## Testing & Debugging Quick Refs

- **Check TTS Queue**: Look for `[TTS]` log lines in terminal
- **Reset Data**: Delete `vocabulary_data.json`, restart server (auto-generates empty dict)
- **Audio Sync Issue**: Clear `static/audio/` if orphaned files cause conflicts
- **Format Detection Bug**: Always test both old and new JSON structures if modifying data loading

## Integration Points to Watch

- **gTTS API**: External dependency; rate-limited (0.5s delay prevents 429 errors)
- **Web Speech API**: Client-side; only `<audio>` tags used (no browser TTS)
- **File I/O**: Potential race conditions if multiple requests edit simultaneously (current: single-threaded, safe)

---

**Last Updated**: March 2026 | Format: Extended Markdown | Audience: AI Coding Agents
