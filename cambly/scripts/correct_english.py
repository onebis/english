#!/usr/bin/env python3
"""
Cambly English Correction Script

Sends formatted transcript to OpenAI API for English correction
and saves the result to output directory.

Usage (run from parent directory of cambly/):
    python cambly/scripts/correct_english.py <YYYYMMDD>
    python cambly/scripts/correct_english.py 20251222
"""

import sys
import os
from pathlib import Path
import json

try:
    import openai
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed. Run: pip install python-dotenv")
    sys.exit(1)


def load_api_key() -> str:
    """Load OpenAI API key from cambly/.env file"""
    env_path = Path("cambly") / ".env"
    
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        print("Create the file with your OpenAI API key:")
        print(f"  echo 'OPENAI_API_KEY=your-api-key' > {env_path}")
        sys.exit(1)
    
    load_dotenv(env_path)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print(f"Error: OPENAI_API_KEY not found in {env_path}")
        print("Add the following line to your .env file:")
        print("  OPENAI_API_KEY=your-api-key")
        sys.exit(1)
    
    return api_key


# =============================================================================
# CORRECTION PROMPT - Edit this section to customize the correction behavior
# =============================================================================

SYSTEM_PROMPT = """
あなたは日本人に英語を教える先生です
入力された会話文字起こしを使って、私の英語学習に役立つ分析と改善提案をしてください。出力は以下のステップに分けてください。
私はNealの箇所です


# 目的
- 後で復習に使える資料にする
- 自身の英会話から自分だけの英語学習資料を作る

# 厳守事項
- 回答のみ出力してください
- 最後の余計なアドバイスやフォローアップは不要です

【ステップ1: 採点】
私が話した内容を採点すると何点ですか？以下を基準に教えてください
またA1~C2だとどのレベルか教えてください。またそれらの理由を教えて
A1:0~20
A2:21~40
B1:41~60
B2:61~80
C1:81~99
C2:100

【ステップ2: 誤り修正】
私が話した英語の文法的な誤りや不自然な表現を大事と思われる10個をピックアップしてください
それをネイティブが使いそうな表現に直してください
その10個の文法や修正理由を説明してください。

【ステップ3: 会話リプレイ】
返答に困っていたと思われる部分を探し、その場面でネイティブならどう返すか自然な返答例を質問とその回答を日本語訳を付けて提示してください。

【ステップ4: 自己分析】
会話全体を振り返り、私の強みと弱みをまとめ、次回の会話で意識すべき具体的な学習アドバイスを3つ提案してください。

【ステップ5: 新しい単語やフレーズ】
会話全体を振り返り、覚えておくとよい単語や表現があれば理由と今回の会話で使える例文にして提案してください。


"""

USER_PROMPT_TEMPLATE = """
---
{transcript}
---
"""

# =============================================================================
# End of customizable prompt section
# =============================================================================


def get_correction(transcript: str, api_key: str) -> str:
    """Send transcript to OpenAI API and get correction."""
    client = openai.OpenAI(api_key=api_key)
    
    user_prompt = USER_PROMPT_TEMPLATE.format(transcript=transcript)
    
    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            # max_completion_tokens=4000
        )
        return response.choices[0].message.content
    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python cambly/scripts/correct_english.py <YYYYMMDD>")
        print("Example: python cambly/scripts/correct_english.py 20251222")
        sys.exit(1)
    
    date_str = sys.argv[1]
    
    # Validate date format
    if not (len(date_str) == 8 and date_str.isdigit()):
        print(f"Error: Invalid date format '{date_str}'. Use YYYYMMDD (e.g., 20251222)")
        sys.exit(1)
    
    # Define paths (run from parent directory of cambly/)
    base_dir = Path("cambly")
    formatted_path = base_dir / "formatted" / f"{date_str}.md"
    output_dir = base_dir / "output"
    output_path = output_dir / f"{date_str}.md"
    
    # Check input file exists
    if not formatted_path.exists():
        print(f"Error: Formatted file not found: {formatted_path}")
        print("\nAvailable formatted files:")
        formatted_dir = base_dir / "formatted"
        if formatted_dir.exists():
            for f in sorted(formatted_dir.glob("*.md")):
                print(f"  - {f.name}")
        else:
            print("  (none - formatted directory does not exist)")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load transcript
    print(f"Reading: {formatted_path}")
    transcript = formatted_path.read_text(encoding="utf-8")
    
    # Load API key
    api_key = load_api_key()
    
    # Get correction from API
    print(f"Sending to OpenAI API (gpt-5.1)...")
    correction = get_correction(transcript, api_key)
    
    # Build output content
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    output_content = f"""# Cambly English Correction - {formatted_date}

---

## Corrections and Suggestions

{correction}
"""
    
    # Save output
    output_path.write_text(output_content, encoding="utf-8")
    print(f"Saved: {output_path}")
    print("Done!")


if __name__ == "__main__":
    main()