import os
import requests
import json
import re
import datetime
import openai
from openai import OpenAI
from typing import Optional

GEMINI_API_KEY = "YOUR_KEY"
TARGET_FILE = "/path/to/target_file"
LOG_PATH = os.path.dirname(os.path.abspath(__file__)) + "/log/"
VOICE_PATH = "/path/to/voice/"
VOICE_URL = "https://sample.com/path/to/"
GEMINI_MODEL_NAME = "gemini-1.5-flash"
OPENAI_API_KEY="YOUR_KEY"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
LINE_ENDPOINT = "https://api.line.me/v2/bot/message/broadcast"
CHANNEL_ACCESS_TOKEN = "YOUR_TOKEN"
CHANNEL_ACCESS_TOKEN = "YOUR_TOKEN"


def get_prompt(text_data: str) -> str:
    return f"""
以下の時系列データについて、詳細な分析を行ってください。
・各項目（体重、血圧最小・最大値、温度、湿度、気圧、風速、曜日）の長期的・短期的な傾向やパターン
・異常値や外れ値の検出とその可能性のある原因
・項目間の相関関係推察（例：気圧と血圧の関係など）
・季節性や曜日による変動パターン
・欠損値の影響と今後の対策案
・全体を踏まえた健康管理や生活リズムへの示唆
・直近1ヶ月の傾向と考察
・マークダウン等の特殊な形式を用いず、改行なしのテキストのみの文章で
また、以下の人物を演じて、講義形式で語ってください
・あなたはシキという名のエンジニアで、人類史上最大の天才です
・計算能力、想像力を併せ持ち、人智をはるかに超越しています
・あなたは今、大勢の前で講義をします。
・よりメタ的に問題を抽出し、哲学的に実存を問うように内容を整理してください
・構造的に、段階的に、ときには冗談を言いつつ解説してください
データは以下の通りです。
{text_data}
"""


def create_request_payload(prompt: str) -> dict:
    return {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }


def get_response(endpoint: str, payload: dict) -> dict:
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def extract_generated_text(response_json: dict) -> str:
    return response_json["candidates"][0]["content"]["parts"][0]["text"]


def get_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def get_voice(text: str, file_path: str, key: str, voice_type: str) -> None:
    openai.api_key = key
    response = openai.audio.speech.create(
        model="tts-1-hd",
        voice=voice_type,  # alloy, echo, fable, onyx, nova, shimmer
        input=text,
        speed=1.0
    )
    response.stream_to_file(file_path)


def post_line_voice(url: str, endpoint: str, token: str) -> Optional[requests.Response]:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    data = {
        "messages": [
            {
                "type": "audio",
                "originalContentUrl": url,
                "duration": 180000
            }
        ]
    }
    response = requests.post(endpoint, headers=headers, data=json.dumps(data))
    return response


def save_file(text: str, file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    # 前処理
    try:
        #prompt = get_prompt(get_file(TARGET_FILE))
        prompt = get_prompt(get_file("hoge.csv"))
        payload = create_request_payload(prompt)
        print("Success: create payload.")
    except Exception as e:
        raise Exception(f"Error: create payload. {e}")

    # 解析
    try:
        response_json = get_response(GEMINI_ENDPOINT, payload)
        response_text = extract_generated_text(response_json)
        print("Success: get response.")
    except Exception as e:
        raise Exception(f"Error: get response. {e}")

    # 結果保存
    try:
        suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M_%S")
        file_name_log = LOG_PATH + suffix + ".log"
        save_file(response_text, file_name_log)
        print("Success: save file.")
    except Exception as e:
        raise Exception(f"Error: save file. {e}")

    # 音声変換
    try:
        file_name_voice = suffix + "_report.mp3"
        file_full_path = VOICE_PATH + file_name_voice
        get_voice(response_text, file_full_path, OPENAI_API_KEY, "alloy")
        print("Success: get voice.")
    except Exception as e:
        raise Exception(f"Error: get voice. {e}")

    # 通知
    try:
        url = VOICE_URL + file_name_voice
        post_line_voice(url, LINE_ENDPOINT, CHANNEL_ACCESS_TOKEN)
        print("Success: post line.")
    except Exception as e:
        raise Exception(f"Error: post line. {e}")


main()
