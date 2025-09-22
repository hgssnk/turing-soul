import os
import requests
import json
import time

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME")
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
TARGET_FILES = os.getenv("TARGET_FILES", "main.py").split(",")
README_PATH = os.environ.get("OUTPUT_FILE", "README.md")

def get_prompt(code):
    return f"""
あなたは優れたソフトウェアアーキテクトです。
以下のソースコードについて、設計書をまとめてください。
出力形式は Markdown で記載してください。
ただし、セクションは##から始めてください。
要件は以下です。

1. 概略: コードの全体を簡潔に記述
1. アーキテクチャ図: ファイルがyamlやymlでなければ不要。マーメイド記法で記載
1. シーケンス図: マーメイド記法で記載
1. フローチャート: ファイルがyamlやymlであれば不要。マーメイド記法で記載
1. 拡張性: 将来的な拡張や改善の視点でコメント
1. 課題: 脆弱性や可読性、保守性などの視点でコメント

ソースコード:
{code}
"""

def create_request_payload(prompt: str) -> dict:
    return {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }


def get_response(payload: dict, max_retries=2, base_delay=35) -> str:
    headers = {"Content-Type": "application/json"}
    for attempt in range(max_retries):
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)
        if response.status_code == 429:
            delay = base_delay * (2 ** (attempt + 1))
            print(f"429 Too Many Requests. retry in {delay}s (attempt {attempt+1}/{max_retries})")
            time.sleep(delay)
            continue
        try:
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            raise e
    raise Exception(f"API request failed after {max_retries} retries due to 429.")


def update_readme(text: str):
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(text)


def read_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    try:
        all_texts = []
        for file_path in TARGET_FILES:
            file_path = file_path.strip()
            print(f'start: {file_path}')
            code = read_file(file_path)
            print('success: read_file')
            prompt = get_prompt(code)
            print('success: get_prompt')
            payload = create_request_payload(prompt)
            print('success: create_payload')
            response_text = get_response(payload)
            print('success: get_response')
            section = f'# {file_path}\n\n{response_text}'
            all_texts.append(section)

        # まとめて README に書き出し
        final_text = "\n\n---\n\n".join(all_texts)
        update_readme(final_text)

    except Exception as e:
        raise Exception(f'こけた {file_path}. {e}')


if __name__ == "__main__":
    main()
