from django.core.management.base import BaseCommand
from exercise.views import get_exercise_summary
from exercise.coach import get_coach_response


class Command(BaseCommand):
    help = "Show Claude coach output for a workout exercise"

    def add_arguments(self, parser):
        parser.add_argument("exercise_id", type=int)

    def handle(self, *args, **options):
        exercise_id = options["exercise_id"]

        # Get the workout summary
        summary_lines = get_exercise_summary(exercise_id)

        # First show the summary
        self.stdout.write("\nWorkout Summary:")
        self.stdout.write("-" * 40)
        for line in summary_lines:
            self.stdout.write(line)

        # Then show Claude's response
        self.stdout.write("\nCoach Claude:")
        self.stdout.write("-" * 40)
        for text in get_coach_response(summary_lines):
            self.stdout.write(text, ending="")
