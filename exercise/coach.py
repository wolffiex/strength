import anthropic
from typing import Iterable

SYSTEM_PROMPT = """You are a knowledgeable and encouraging strength training coach providing real-
time feedback during workouts.

The summary shows:
1. Previous attempts at all exercises in the current category
2. Today's progress on all exercises in the category

IMPORTANT RULES:
- For the current exercise (the one marked as "Currently on:"), give preparation advice 
  based on previous workout data if available
- If "Today: Not started yet" appears, this means the user hasn't recorded any sets yet
- Only if sets are shown for today, compare current performance to previous attempts
- Always focus on the current exercise only, not other exercises in the category

Your response should BRIEFLY cover:
1. For the current exercise, what to aim for based on previous attempts
2. A quick form cue if needed
3. Specific suggestion for weight/reps for the upcoming set
4. Encouragement to maintain good pace through the workout

Keep feedback concise, encouraging, and immediately actionable.
Write in clear sentences that make sense as they appear."""

TRAINER_SUMMARY_PROMPT = """You are a knowledgeable strength training coach providing a summary analysis 
of a workout category.

The data shows:
1. Multiple exercises within a category (like 'Conditioning' or 'Main Lift')
2. Current workout performance for each exercise
3. Previous workout performance for comparison

Your task is to provide a brief but insightful summary that includes:
1. Overall performance compared to previous workouts
2. Highlight exercises with notable improvement or regression
3. Identify any patterns across the exercises
4. One specific actionable suggestion to improve this category next time
5. Comment on pace, especially if it lags

Be concise, encouraging, data-driven, and provide specific observations when possible.
Limit your response to 3-4 short paragraphs maximum."""


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
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for message in stream:
            if hasattr(message, "text"):
                # Just yield the text directly without buffering or chunking
                yield message.text


def get_trainer_summary(category_data: list[dict]) -> Iterable[str]:
    """Get streaming category analysis from Claude based on workout data

    Args:
        category_data: List of dictionaries containing exercise data with structure:
            {
                "exercise": WorkoutExercise instance,
                "current_sets": List of rendered set strings for current workout,
                "last_sets": List of rendered set strings from previous workout,
                "last_workout": Previous Workout instance or None
            }
    """
    # Format the data in a clear way for Claude
    summary_lines = []
    summary_lines.append("# Category Summary")

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
                # Get the set object to check for duration_secs
                set_obj = exercise.sets.filter(set_num=i).first()
                time_info = ""
                if set_obj and set_obj.duration_secs:
                    mins = set_obj.duration_secs // 60
                    secs = set_obj.duration_secs % 60
                    time_info = f" (completed in {mins:02d}:{secs:02d})"
                summary_lines.append(f"  Set {i}: {set_str}{time_info}")
        else:
            summary_lines.append("  No sets completed")

        # Previous workout
        summary_lines.append("Previous workout:")
        if last_workout:
            summary_lines.append(f"  Date: {last_workout.date}")
            if last_sets:
                for i, set_str in enumerate(last_sets, 1):
                    # Try to get the set object to check for duration
                    if last_workout and exercise_info.get("last_exercise"):
                        last_exercise = exercise_info["last_exercise"]
                        set_obj = last_exercise.sets.filter(set_num=i).first()
                        time_info = ""
                        if set_obj and set_obj.duration_secs:
                            mins = set_obj.duration_secs // 60
                            secs = set_obj.duration_secs % 60
                            time_info = f" (completed in {mins:02d}:{secs:02d})"
                        summary_lines.append(f"  Set {i}: {set_str}{time_info}")
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

    client = anthropic.Client()
    with client.messages.stream(
        model="claude-3-sonnet-20240229",
        max_tokens=400,
        temperature=0.7,
        system=TRAINER_SUMMARY_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for message in stream:
            if hasattr(message, "text"):
                # Just yield the text directly without buffering or chunking
                yield message.text
