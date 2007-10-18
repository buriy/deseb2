from django.core.management.base import AppCommand

class Command(AppCommand):
    help = """Prints the ALTER TABLE SQL statements for the given app name(s), in order to 
non-destructively bring them into compliance with your models.
See: http://code.google.com/p/deseb/wiki/Usage"""

    output_transaction = True

    def handle_app(self, app, **options):
        import deseb.schema_evolution
        deseb.schema_evolution.get_sql_fingerprint(app, self.style)
