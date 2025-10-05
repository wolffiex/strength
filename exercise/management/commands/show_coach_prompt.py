from django.core.management.base import BaseCommand

from exercise.coach import SYSTEM_PROMPT
from exercise.views import get_exercise_summary


class Command(BaseCommand):
    help = "Display the complete coach prompt for a workout exercise"

    def add_arguments(self, parser):
        parser.add_argument("exercise_id", type=int, help="WorkoutExercise primary key")

    def handle(self, *args, **options):
        exercise_id = options["exercise_id"]

        summary_lines = get_exercise_summary(exercise_id)
        user_prompt = "\n".join(summary_lines)

        self.stdout.write("System Prompt:")
        self.stdout.write("-" * 40)
        self.stdout.write(SYSTEM_PROMPT.strip())
        self.stdout.write("")

        self.stdout.write("User Prompt:")
        self.stdout.write("-" * 40)
        self.stdout.write(user_prompt)
