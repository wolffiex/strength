import anthropic
from typing import Iterable

SYSTEM_PROMPT = """You are a knowledgeable and encouraging strength training coach providing real-time feedback during workouts.

The summary shows:
1. Previous attempts at all exercises in the current category
2. Today's progress on all exercises in the category

IMPORTANT: Focus ONLY on the LAST exercise listed in "Today's progress". This is the exercise the athlete just completed. DO NOT comment on earlier exercises.

Your response should BRIEFLY cover:
1. Current exercise vs its previous attempts
2. Quick form cue if needed
3. Suggestion for the next set
4. Brief comment on overall pacing/intensity of this category

Keep feedback concise, encouraging, and immediately actionable.
Write in clear sentences that make sense as they appear."""

def get_coach_response(summary_lines: list[str]) -> Iterable[str]:
    """Get streaming response from Claude based on workout summary"""
    # Combine the lines into a clean format for Claude
    summary = "\n".join(summary_lines)
    prompt = f"""Based on this workout information:

{summary}

Provide encouraging, relevant coaching feedback."""

    client = anthropic.Client()
    with client.messages.stream(
        model="claude-3-sonnet-20240229",
        max_tokens=150,
        temperature=0.7,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        buffer = ""
        for message in stream:
            if hasattr(message, 'text'):
                buffer += message.text
                # Check if we have complete words (ending in space or punctuation)
                while " " in buffer or any(p in buffer for p in ".!?"):
                    # Find the last complete word boundary
                    last_space = buffer.rfind(" ")
                    last_punct = max(buffer.rfind(p) for p in ".!?")
                    split_point = max(last_space, last_punct) + 1
                    
                    if split_point <= 0:
                        break
                        
                    # Yield complete words
                    yield buffer[:split_point]
                    buffer = buffer[split_point:]
                    
        # Yield any remaining text
        if buffer:
            yield buffer