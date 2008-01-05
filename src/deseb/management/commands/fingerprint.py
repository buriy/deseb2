from django.core.management.base import AppCommand

class Command(AppCommand):
    help = """Prints the app fingerprints
See: http://code.google.com/p/deseb/wiki/Usage"""

    output_transaction = True

    def handle_app(self, app, **options):
        import deseb.schema_evolution
        deseb.schema_evolution.get_sql_fingerprint(app, self.style)
