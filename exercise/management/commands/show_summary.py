from django.core.management.base import BaseCommand
from exercise.views import get_exercise_summary


class Command(BaseCommand):
    help = "Show summary for a workout exercise"

    def add_arguments(self, parser):
        parser.add_argument("exercise_id", type=int)

    def handle(self, *args, **options):
        exercise_id = options["exercise_id"]
        for line in get_exercise_summary(exercise_id):
            self.stdout.write(line)
