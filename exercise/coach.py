import anthropic
from typing import Iterable

SYSTEM_PROMPT = """You are a knowledgeable and encouraging strength training coach providing real-
time feedback during workouts.

For the current exercise, give preparation advice based on previous workout data if available.

Your response should BRIEFLY cover:
1. For the current exercise, what to aim for based on previous attempts
2. A quick form cue if needed
3. Specific suggestion for weight/reps for the upcoming set
4. Encouragement to maintain good pace through the workout

Keep feedback concise, encouraging, and immediately actionable.
Write in clear sentences that make sense as they appear."""

TRAINER_SUMMARY_PROMPT = """You are a knowledgeable strength training coach providing a warm, encouraging
summary for one workout category.

Write in a supportive, non-judgmental tone. Assume good intent and normal variability in training.

You are given:
- Multiple exercises within a category
- Today’s sets and the most recent prior sets for comparison
- Any notes provided for sets

Goals:
- Start by celebrating at least one tangible win from today.
- When numbers differ from last time, use neutral language (“today looked lighter/different”) and offer plausible reasons (equipment change, fatigue, logging differences, pace).
- Fold in relevant notes when they help explain differences.
- Offer one small, specific next step or option set (e.g., “if dips felt heavy, try assisted dips or 3×5 negatives”).
- If pace seems off, gently suggest a rest guideline.
- End with a short, encouraging line that looks forward.

Avoid:
- Alarmist words like “concerning”, “regressed”, “declined”, or blame.
- Overstating certainty; prefer may/might/could.

Format:
- 2–3 short paragraphs, or 1 short paragraph plus 2–3 compact bullets.
- Keep it concise, actionable, and kind."""


def get_coach_response(summary_lines: list[str]) -> Iterable[str]:
    """Get streaming response from Claude based on workout summary"""
    # Combine the lines into a clean format for Claude
    prompt = "\n".join(summary_lines)

    client = anthropic.Client()
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=150,
        temperature=0.7,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for message in stream:
            if hasattr(message, "text"):
                # Just yield the text directly without buffering or chunking
                yield message.text


def build_trainer_summary_prompt(category_data: list[dict]) -> str:
    """Build the user prompt string used for trainer category summary.

    Args:
        category_data: List of dictionaries containing exercise data with structure:
            {
                "exercise": WorkoutExercise instance,
                "current_sets": List[str],
                "last_sets": List[str],
                "last_workout": Previous Workout instance or None,
                "last_exercise": WorkoutExercise instance or None,
            }
    Returns:
        The user prompt string that will be sent along with TRAINER_SUMMARY_PROMPT.
    """
    summary_lines: list[str] = []
    summary_lines.append("# Category Summary")

    # Notes are single-line; append inline if present

    for exercise_info in category_data:
        exercise = exercise_info["exercise"]
        current_sets = exercise_info["current_sets"]
        last_sets = exercise_info["last_sets"]
        last_workout = exercise_info["last_workout"]

        summary_lines.append(f"\n## {exercise.exercise.name}")

        # Current workout
        summary_lines.append("Current workout:")
        if current_sets:
            for i, set_str in enumerate(current_sets, 1):
                # Get the set object to check for notes
                set_obj = exercise.sets.filter(set_num=i).first()
                note_info = ""
                if set_obj and set_obj.note:
                    note_text = str(set_obj.note).strip()
                    if note_text:
                        note_info = f" - Note: {note_text}"
                summary_lines.append(f"  Set {i}: {set_str}{note_info}")
        else:
            summary_lines.append("  No sets completed")

        # Previous workout
        summary_lines.append("Previous workout:")
        if last_workout:
            summary_lines.append(f"  Date: {last_workout.date}")
            if last_sets:
                for i, set_str in enumerate(last_sets, 1):
                    # Try to get the set object to check for notes
                    if last_workout and exercise_info.get("last_exercise"):
                        last_exercise = exercise_info["last_exercise"]
                        set_obj = last_exercise.sets.filter(set_num=i).first()
                        note_info = ""
                        if set_obj and set_obj.note:
                            note_text = str(set_obj.note).strip()
                            if note_text:
                                note_info = f" - Note: {note_text}"
                        summary_lines.append(f"  Set {i}: {set_str}{note_info}")
                    else:
                        summary_lines.append(f"  Set {i}: {set_str}")
            else:
                summary_lines.append("  No sets completed")
        else:
            summary_lines.append("  No previous data")

    summary = "\n".join(summary_lines)
    prompt = f"""Here's a summary of the recently completed category:

{summary}

Provide encouraging, relevant coaching feedback."""
    return prompt


def get_trainer_summary(category_data: list[dict]) -> Iterable[str]:
    """Get streaming category analysis from Claude based on workout data"""
    prompt = build_trainer_summary_prompt(category_data)

    client = anthropic.Client()
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=400,
        temperature=0.7,
        system=TRAINER_SUMMARY_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for message in stream:
            if hasattr(message, "text"):
                # Just yield the text directly without buffering or chunking
                yield message.text
