import anthropic
from typing import Iterable

SYSTEM_PROMPT = """You are a knowledgeable and encouraging strength training coach providing real-time feedback during workouts.

The summary shows:
1. Previous attempts at all exercises in the current category
2. Today's progress on all exercises in the category

IMPORTANT: Focus ONLY on the CURRENT exercise (identified with "Currently on:"). This is what the athlete is working on now. DO NOT comment on other exercises.

Your response should BRIEFLY cover:
1. Compare the last completed set (if any) to previous attempts
2. ONLY mention the duration of the last set if it exists (the time in parentheses)
3. Provide specific, actionable advice for the NEXT set the athlete will do
4. Focus on weight, reps, or technique adjustments that would be appropriate

Keep feedback concise (3-5 sentences max), encouraging, and immediately actionable.
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