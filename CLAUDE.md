# Build Commands
- `python manage.py runserver` - Run development server
- `npm run tailwind-watch` - Watch and compile Tailwind CSS
- `npm run tailwind-build` - Build Tailwind CSS

# Code Style
- Imports: stdlib -> Django -> local, grouped with blank lines
- Classes: PascalCase (Exercise, WorkoutSet)
- Functions/Variables: snake_case (get_category, total_reps)
- Constants: UPPERCASE (CATEGORIES, SUPERSETS)
- Indentation: 4 spaces
- Line length: ~80-100 chars
- Type hints: On function parameters where useful
- Error handling: Specific exceptions, clear messages
- Formatting: Blank lines between sections, trailing commas

# Django Patterns
- Models: Include verbose_name and help_text
- Views: Class-based when possible
- Forms: Validate in clean() methods
- Templates: Use base.html inheritance