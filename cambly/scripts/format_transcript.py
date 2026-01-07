#!/usr/bin/env python3
"""
Cambly Transcript Formatter

Formats raw Cambly transcripts from avatar-labeled format
into clean conversational format.

Usage (run from parent directory of cambly/):
    python cambly/scripts/format_transcript.py <YYYYMMDD>
    python cambly/scripts/format_transcript.py 20251222
"""

import sys
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Utterance:
    speaker: str
    text: str


# Short interjections to potentially skip when they interrupt another speaker
MINIMAL_INTERJECTIONS = {
    "mmm", "mm", "mhm", "mm-hmm", "mmhmm",
    "uh-huh", "uh huh", "uhuh",
    "yeah", "yep", "yup",
    "okay", "ok", "right",
    "oh", "ah", "i see",
}


def parse_transcript(raw_text: str) -> List[Utterance]:
    """Parse raw transcript into list of Utterance objects."""
    lines = raw_text.strip().split('\n')
    utterances = []
    current_speaker = None
    current_text_parts = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this line is a speaker label
        if line.endswith('のアバター'):
            # Save previous utterance if exists
            if current_speaker and current_text_parts:
                text = ' '.join(current_text_parts).strip()
                if text:
                    utterances.append(Utterance(current_speaker, text))
            
            # Start new speaker
            current_speaker = line.replace('のアバター', '')
            current_text_parts = []
        else:
            # This is speech content
            if current_speaker:
                current_text_parts.append(line)
    
    # Don't forget the last utterance
    if current_speaker and current_text_parts:
        text = ' '.join(current_text_parts).strip()
        if text:
            utterances.append(Utterance(current_speaker, text))
    
    return utterances


def is_minimal_interjection(text: str) -> bool:
    """Check if text is a minimal interjection that can be skipped."""
    cleaned = text.lower().strip().rstrip('.,!?')
    return cleaned in MINIMAL_INTERJECTIONS


def merge_utterances(utterances: List[Utterance]) -> List[Utterance]:
    """
    Merge consecutive utterances from the same speaker.
    Handle minimal interjections from other speakers.
    """
    if not utterances:
        return []
    
    merged = []
    i = 0
    
    while i < len(utterances):
        current = utterances[i]
        combined_texts = [current.text]
        
        j = i + 1
        while j < len(utterances):
            next_utt = utterances[j]
            
            if next_utt.speaker == current.speaker:
                # Same speaker - merge
                combined_texts.append(next_utt.text)
                j += 1
            elif is_minimal_interjection(next_utt.text):
                # Different speaker but minimal interjection
                # Check if the speaker after this is the same as current
                if j + 1 < len(utterances) and utterances[j + 1].speaker == current.speaker:
                    # Skip the interjection and continue merging
                    j += 1
                else:
                    # Interjection ends this speaker's turn
                    break
            else:
                # Different speaker with substantive content
                break
        
        # Create merged utterance
        merged_text = ' '.join(combined_texts)
        merged.append(Utterance(current.speaker, merged_text))
        i = j
    
    return merged


def clean_text(text: str) -> str:
    """Clean and normalize text while preserving hesitations."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove trailing comma if present
    text = text.rstrip(',')
    
    return text


def add_punctuation(text: str) -> str:
    """Add light punctuation to text."""
    text = clean_text(text)
    
    if not text:
        return text
    
    # Capitalize first letter
    text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
    
    # Add period at end if no punctuation
    if text and text[-1] not in '.!?':
        text += '.'
    
    return text


def format_transcript(utterances: List[Utterance]) -> str:
    """Format merged utterances into final output."""
    lines = []
    
    for utt in utterances:
        text = add_punctuation(utt.text)
        lines.append(f"{utt.speaker}: {text}")
    
    return '\n\n'.join(lines)


def main():
    if len(sys.argv) != 2:
        print("Usage: python cambly/scripts/format_transcript.py <YYYYMMDD>")
        print("Example: python cambly/scripts/format_transcript.py 20251222")
        sys.exit(1)
    
    date_str = sys.argv[1]
    
    # Validate date format
    if not (len(date_str) == 8 and date_str.isdigit()):
        print(f"Error: Invalid date format '{date_str}'. Use YYYYMMDD (e.g., 20251222)")
        sys.exit(1)
    
    # Define paths
    base_dir = Path("cambly")
    raw_path = base_dir / "raw" / f"{date_str}.txt"
    formatted_dir = base_dir / "formatted"
    formatted_path = formatted_dir / f"{date_str}.md"
    
    # Check input file exists
    if not raw_path.exists():
        print(f"Error: Raw transcript not found: {raw_path}")
        print("\nAvailable raw files:")
        raw_dir = base_dir / "raw"
        if raw_dir.exists():
            files = sorted(raw_dir.glob("*.txt"))
            if files:
                for f in files:
                    print(f"  - {f.stem}")
            else:
                print("  (none)")
        else:
            print("  (raw directory does not exist)")
        sys.exit(1)
    
    # Create output directory if needed
    formatted_dir.mkdir(parents=True, exist_ok=True)
    
    # Read raw transcript
    print(f"Reading: {raw_path}")
    raw_text = raw_path.read_text(encoding="utf-8")
    
    # Process transcript
    print("Parsing transcript...")
    utterances = parse_transcript(raw_text)
    print(f"  Found {len(utterances)} utterances")
    
    print("Merging consecutive utterances...")
    merged = merge_utterances(utterances)
    print(f"  Merged into {len(merged)} turns")
    
    # Format output
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    output_content = f"# Cambly Session - {formatted_date}\n\n"
    output_content += format_transcript(merged)
    output_content += "\n"
    
    # Save output
    formatted_path.write_text(output_content, encoding="utf-8")
    print(f"Saved: {formatted_path}")
    print("Done!")


if __name__ == "__main__":
    main()