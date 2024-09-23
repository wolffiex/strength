from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date
from exercise.models import Workout, Exercise, WorkoutExercise, Set

from exercise.workouts.sep4 import get_workout_data


class Command(BaseCommand):
    help = "Creates a new workout with the specified exercises and sets"

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create a new Workout instance for September 4th
            workout = Workout.objects.create(date=date(2023, 9, 4), completed=True)

            sep4 = get_workout_data()
            # Process the workout data
            for exercise_data in [
                item for sublist in sep4.values() for item in sublist
            ]:
                print(exercise_data)
                exercise = Exercise.objects.get(pk=exercise_data["pk"])
                workout_exercise = WorkoutExercise.objects.create(
                    workout=workout, exercise=exercise
                )

                for set_data in exercise_data["sets"]:
                    Set.objects.create(
                        **set_data,
                        exercise=workout_exercise,
                    )

            self.stdout.write(self.style.SUCCESS("Workout created successfully."))
