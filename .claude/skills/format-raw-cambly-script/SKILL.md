---
name: cambly-transcript-formatter
description: Format Cambly video call transcripts and get English corrections via ChatGPT API. Trigger when user mentions "Cambly", "transcript", or specifies a date like "20251222". Full pipeline reads raw transcript, formats it, sends to GPT for correction, and saves all outputs.
---

# Cambly Transcript Formatter & Corrector

Format Cambly transcripts and get English corrections via ChatGPT API.

## Full Workflow (Default)

1. User specifies a date (e.g., "20251222", "2025-12-22", "12月22日")
2. Run: `cambly/scripts/format_transcript.py {YYYYMMDD}`
   - Reads: `cambly/raw/{YYYYMMDD}.txt`
   - Writes: `cambly/formatted/{YYYYMMDD}.md`
3. Run: `cambly/scripts/correct_english.py {YYYYMMDD}`
   - Reads: `cambly/formatted/{YYYYMMDD}.md`
   - Sends to GPT API
   - Writes: `cambly/output/{YYYYMMDD}.md`

## Date Handling

- Accept various formats: "20251222", "2025-12-22", "12/22", "12月22日"
- Normalize to YYYYMMDD for file paths
- If year omitted, assume current year

## File Paths

```
cambly/
├── .env                    # API key (OPENAI_API_KEY=...)
├── formatted/
│   └── {YYYYMMDD}.md       # Formatted transcript
├── output/
│   └── {YYYYMMDD}.md       # Final output with corrections
├── raw/
│   └── {YYYYMMDD}.txt      # Input (raw transcript)
└── scripts/
    ├── correct_english.py  # API correction script
    └── format_transcript.py # Transcript formatter script
```


## Raw Input Format

```
{Speaker}のアバター
{utterance fragment}
{Other Speaker}のアバター
{utterance fragment}
```

## Formatted Output Format

```markdown
# Cambly Session - {YYYY-MM-DD}

Neal: {merged utterances}
Joey Bell: {merged utterances}
...
```

## Transformation Rules

### 1. Speaker Identification
- Extract speaker name by removing "のアバター" suffix
- Speaker names appear exactly as written (preserve case, spaces)

### 2. Utterance Merging
- Merge consecutive utterances from the same speaker into one turn
- Join with space; add period between distinct sentences
- Preserve speaker turn order from original

### 3. Preservation Requirements (Critical)
- Keep ALL hesitations: "uh", "um", "uh-huh"
- Keep ALL fillers: "yeah", "so", "like", "right"
- Keep repetitions: "yeah yeah", "I I"
- Keep incomplete thoughts and restarts
- Keep informal speech patterns exactly
- Do NOT correct grammar or word choice
- Do NOT add words not in original
- Do NOT remove any spoken content

### 4. Light Punctuation
- Add periods at clear sentence boundaries
- Add question marks for questions
- Add commas only for natural pauses
- Capitalize sentence starts
- Do NOT over-punctuate

### 5. Handling Interjections
When Speaker B interjects briefly during Speaker A's turn:
- If interjection is minimal ("Mmm", "Uh-huh", "Okay"): merge into Speaker A's turn, omit interjection
- If interjection is substantive: preserve as separate turn

## Example

**Input:**
```
Nealのアバター
Hi,
Joey Bellのアバター
And yeah, what's up, buddy?
Nealのアバター
I'm doing great but I'm a little groggy.
Joey Bellのアバター
That's
Nealのアバター
I
Joey Bellのアバター
okay
Nealのアバター
woke up maybe 15 minutes ago.
```

**Output:**
```
Neal: Hi, I'm doing great but I'm a little groggy. I woke up maybe 15 minutes ago.
Joey Bell: And yeah, what's up, buddy? That's okay.
```

Note: The interleaved "That's" / "I" / "okay" is merged based on context. Joey Bell's "That's okay" and Neal's continuous thought "I woke up maybe 15 minutes ago" are reconstructed.

## Processing Steps

1. Parse date from user input → normalize to YYYYMMDD
2. Run format script:
   ```bash
   python cambly/scripts/format_transcript.py {YYYYMMDD}
   ```
3. Run correction script:
   ```bash
   python cambly/scripts/correct_english.py {YYYYMMDD}
   ```
4. Confirm completion with output file path

## Customizing the Scripts

### Format Script (`format_transcript.py`)
- `MINIMAL_INTERJECTIONS`: Set of short interjections to skip (e.g., "mmm", "uh-huh")
- `add_punctuation()`: Modify punctuation rules
- `merge_utterances()`: Adjust merging logic

### Correction Script (`correct_english.py`)
- `SYSTEM_PROMPT`: Overall instruction for the AI tutor
- `USER_PROMPT_TEMPLATE`: Template for each correction request
- Model and parameters can be adjusted in `get_correction()`

## Error Handling

- File not found: Inform user and list available dates in `cambly/raw/`
- Invalid date: Ask user to clarify the date format
- Directory missing: Create directories automatically
- API key missing: Show setup instructions for `cambly/.env`
- API error: Display error message from OpenAI