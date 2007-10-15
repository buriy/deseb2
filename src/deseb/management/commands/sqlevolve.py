from django.core.management.base import AppCommand

class Command(AppCommand):
    help = """Prints the ALTER TABLE SQL statements for the given app name(s), in order to 
non-destructively bring them into compliance with your models.
See: http://code.google.com/p/deseb/wiki/Usage"""

    output_transaction = True

    def handle(self, *app_labels, **options):
        if not app_labels:
            from django.db.models.loading import get_apps 
            app_list = get_apps()
            output = []
            for app in app_list:
                app_output = self.handle_app(app, **options)
                if app_output:
                    output.append(app_output)
            return '\n'.join(output)
        else:
            super(Command, self).handle(*app_labels, **options)

    def handle_app(self, app, **options):
        import deseb.schema_evolution
        return '\n'.join(deseb.schema_evolution.get_sql_evolution(app, self.style))
