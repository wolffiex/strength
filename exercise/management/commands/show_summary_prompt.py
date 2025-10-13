from django.core.management.base import BaseCommand

from exercise.coach import TRAINER_SUMMARY_PROMPT, build_trainer_summary_prompt
from exercise.models import Workout, WorkoutExercise, Set


class Command(BaseCommand):
    help = "Display the complete trainer summary prompt for a workout category"

    def add_arguments(self, parser):
        parser.add_argument("category", type=str, help="Exercise category code (e.g., COND, MAIN, ACCE, CORE)")
        parser.add_argument(
            "workout_id",
            type=int,
            nargs="?",
            default=None,
            help="Optional workout ID. If omitted, uses the active (uncompleted) workout.",
        )

    def handle(self, *args, **options):
        category = options["category"]
        workout_id = options["workout_id"]

        # Resolve workout
        workout = None
        if workout_id is not None:
            try:
                workout = Workout.objects.get(pk=workout_id)
            except Workout.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"No workout found with ID {workout_id}"))
                return
        else:
            workout = Workout.objects.filter(completed=False).first()
            if not workout:
                self.stderr.write(self.style.ERROR("No active workout found"))
                return

        # Collect exercises for category in this workout
        exercises = workout.exercises.filter(exercise__category=category).order_by("order")
        if not exercises.exists():
            self.stderr.write(self.style.ERROR(f"No exercises found for category {category} in selected workout"))
            return

        # Build exercise data consistent with get_trainer_summary
        exercise_data = []
        for exercise in exercises:
            current_sets = list(map(lambda s: s.render(), exercise.sets.all().order_by("set_num")))

            # Determine last_workout depending on whether this workout is completed
            if workout.completed:
                last_workout = (
                    Workout.objects.filter(completed=True, exercises__exercise=exercise.exercise, date__lt=workout.date)
                    .order_by("-date")
                    .first()
                )
            else:
                last_workout = (
                    Workout.objects.filter(completed=True, exercises__exercise=exercise.exercise)
                    .order_by("-date")
                    .first()
                )

            last_sets = []
            last_exercise = None
            if last_workout:
                try:
                    last_exercise = WorkoutExercise.objects.get(workout=last_workout, exercise=exercise.exercise)
                    last_sets = list(
                        map(lambda s: s.render(), Set.objects.filter(exercise=last_exercise).order_by("set_num"))
                    )
                except WorkoutExercise.DoesNotExist:
                    pass

            exercise_data.append(
                {
                    "exercise": exercise,
                    "current_sets": current_sets,
                    "last_sets": last_sets,
                    "last_workout": last_workout,
                    "last_exercise": last_exercise,
                }
            )

        # Build the user prompt
        user_prompt = build_trainer_summary_prompt(exercise_data)

        # Output prompts
        self.stdout.write("System Prompt:")
        self.stdout.write("-" * 40)
        self.stdout.write(TRAINER_SUMMARY_PROMPT.strip())
        self.stdout.write("")

        self.stdout.write("User Prompt:")
        self.stdout.write("-" * 40)
        self.stdout.write(user_prompt)

