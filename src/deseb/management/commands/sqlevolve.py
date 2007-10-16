from django.core.management.base import AppCommand

class Command(AppCommand):
    help = """Prints the ALTER TABLE SQL statements for the given app name(s), in order to 
non-destructively bring them into compliance with your models.
See: http://code.google.com/p/deseb/wiki/Usage"""

    output_transaction = True

    def handle(self, *app_labels, **options):
        from django.db.models.loading import get_apps 
        all_apps = get_apps()
        run_apps = []

        if app_labels:
            for app in all_apps:
                app_name = app.__name__.split('.')[-2]
                if app_name in app_labels:
                    run_apps.append(app)
        else:
            run_apps = all_apps
            
        output = []
        for app in run_apps:
            app_output = self.handle_app(app, **options)
            if app_output:
                output.append(app_output)
        return '\n'.join(output)

    def handle_app(self, app, **options):
        import deseb.schema_evolution
        return '\n'.join(deseb.schema_evolution.get_sql_evolution(app, self.style))
