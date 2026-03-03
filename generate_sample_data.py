"""
生成示例测试数据的脚本
"""
import json
import os
from datetime import datetime, timedelta

DATA_FILE = 'vocabulary_data.json'

def generate_sample_data():
    """生成示例课程和词汇数据"""
    data = {
        "第一課-城市": {
            "詞語": [
                {
                    "word": "建築",
                    "meaning": "building or construction",
                    "attempts": 3,
                    "correct": 3,
                    "incorrect": 0,
                    "history": [
                        {"timestamp": "2026-03-03 10:00:00", "known": True},
                        {"timestamp": "2026-03-03 11:00:00", "known": True},
                        {"timestamp": "2026-03-03 12:00:00", "known": True}
                    ]
                },
                {
                    "word": "摩天大樓",
                    "meaning": "skyscraper",
                    "attempts": 2,
                    "correct": 1,
                    "incorrect": 1,
                    "history": [
                        {"timestamp": "2026-03-03 10:15:00", "known": False},
                        {"timestamp": "2026-03-03 11:15:00", "known": True}
                    ]
                },
                {
                    "word": "古蹟",
                    "meaning": "historic site or monument",
                    "attempts": 1,
                    "correct": 0,
                    "incorrect": 1,
                    "history": [
                        {"timestamp": "2026-03-03 10:30:00", "known": False}
                    ]
                },
                {
                    "word": "街道",
                    "meaning": "street",
                    "attempts": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "history": []
                }
            ],
            "段落": [
                {
                    "id": "para_1",
                    "title": "城市介紹",
                    "sentences": [
                        {
                            "sentence": "香港是一個充滿活力的國際大都市",
                            "attempts": 2,
                            "correct": 2,
                            "incorrect": 0,
                            "history": [
                                {"timestamp": "2026-03-03 09:00:00", "known": True},
                                {"timestamp": "2026-03-03 10:00:00", "known": True}
                            ]
                        },
                        {
                            "sentence": "這裡有許多現代建築和古老廟宇",
                            "attempts": 1,
                            "correct": 0,
                            "incorrect": 1,
                            "history": [
                                {"timestamp": "2026-03-03 09:15:00", "known": False}
                            ]
                        }
                    ],
                    "attempts": 2,
                    "correct": 1,
                    "incorrect": 1,
                    "history": [
                        {"timestamp": "2026-03-03 09:00:00", "known": True},
                        {"timestamp": "2026-03-03 09:15:00", "known": False}
                    ]
                },
                {
                    "id": "para_2",
                    "title": "交通運輸",
                    "sentences": [
                        {
                            "sentence": "地鐵是最方便的交通工具",
                            "attempts": 0,
                            "correct": 0,
                            "incorrect": 0,
                            "history": []
                        },
                        {
                            "sentence": "雙層電車也很受歡迎",
                            "attempts": 0,
                            "correct": 0,
                            "incorrect": 0,
                            "history": []
                        }
                    ],
                    "attempts": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "history": []
                }
            ]
        },
        "第二課-天氣": {
            "詞語": [
                {
                    "word": "陽光",
                    "meaning": "sunshine",
                    "attempts": 2,
                    "correct": 2,
                    "incorrect": 0,
                    "history": [
                        {"timestamp": "2026-03-03 13:00:00", "known": True},
                        {"timestamp": "2026-03-03 14:00:00", "known": True}
                    ]
                },
                {
                    "word": "暴雨",
                    "meaning": "heavy rain or downpour",
                    "attempts": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "history": []
                },
                {
                    "word": "溫度",
                    "meaning": "temperature",
                    "attempts": 1,
                    "correct": 1,
                    "incorrect": 0,
                    "history": [
                        {"timestamp": "2026-03-03 13:30:00", "known": True}
                    ]
                }
            ],
            "段落": [
                {
                    "id": "para_1",
                    "title": "春天天氣",
                    "sentences": [
                        {
                            "sentence": "春天的天氣變化很快",
                            "attempts": 1,
                            "correct": 1,
                            "incorrect": 0,
                            "history": [
                                {"timestamp": "2026-03-03 12:00:00", "known": True}
                            ]
                        },
                        {
                            "sentence": "有時候陽光明媚有時候下雨",
                            "attempts": 0,
                            "correct": 0,
                            "incorrect": 0,
                            "history": []
                        }
                    ],
                    "attempts": 1,
                    "correct": 1,
                    "incorrect": 0,
                    "history": [
                        {"timestamp": "2026-03-03 12:00:00", "known": True}
                    ]
                }
            ]
        },
        "Lesson3-Family": {
            "詞語": [
                {
                    "word": "家庭",
                    "meaning": "family",
                    "attempts": 2,
                    "correct": 2,
                    "incorrect": 0,
                    "history": [
                        {"timestamp": "2026-03-03 15:00:00", "known": True},
                        {"timestamp": "2026-03-03 16:00:00", "known": True}
                    ]
                },
                {
                    "word": "父親",
                    "meaning": "father",
                    "attempts": 1,
                    "correct": 1,
                    "incorrect": 0,
                    "history": [
                        {"timestamp": "2026-03-03 15:15:00", "known": True}
                    ]
                },
                {
                    "word": "母親",
                    "meaning": "mother",
                    "attempts": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "history": []
                }
            ],
            "段落": [
                {
                    "id": "para_1",
                    "title": "My Family",
                    "sentences": [
                        {
                            "sentence": "我有一個幸福的家庭",
                            "attempts": 1,
                            "correct": 1,
                            "incorrect": 0,
                            "history": [
                                {"timestamp": "2026-03-03 14:00:00", "known": True}
                            ]
                        },
                        {
                            "sentence": "我的父親是一位工程師",
                            "attempts": 0,
                            "correct": 0,
                            "incorrect": 0,
                            "history": []
                        }
                    ],
                    "attempts": 1,
                    "correct": 1,
                    "incorrect": 0,
                    "history": [
                        {"timestamp": "2026-03-03 14:00:00", "known": True}
                    ]
                }
            ]
        }
    }
    
    return data

def save_data(data):
    """保存數據到 JSON 文件"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ 測試數據已生成到 {DATA_FILE}")
    print(f"✓ 共包含 {len(data)} 個課程")
    
    total_words = 0
    total_paragraphs = 0
    for lesson_name, lesson_data in data.items():
        word_count = len(lesson_data.get('詞語', []))
        para_count = len(lesson_data.get('段落', []))
        total_words += word_count
        total_paragraphs += para_count
        print(f"  - {lesson_name}: {word_count} 個詞語, {para_count} 個段落")
    
    print(f"\n總計:")
    print(f"  - {total_words} 個詞語")
    print(f"  - {total_paragraphs} 個段落")

if __name__ == '__main__':
    print("正在生成測試數據...")
    sample_data = generate_sample_data()
    save_data(sample_data)
    print("\n✓ 完成！現在可以重新啟動應用程式來查看測試數據。")
