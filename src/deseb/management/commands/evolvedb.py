from django.core.management.base import AppCommand
from optparse import make_option #@UnresolvedImport

class Command(AppCommand):
    option_list = AppCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--dont-save', action='store_false', dest='do_save', default=True,
            help='Don\'t save evolution to schema_evolution.py near to models.py.'),
        make_option('--verbose', action='store_false', dest='verbose', default=False,
            help='Don\'t save evolution to schema_evolution.py near to models.py.'),
        make_option('--managed-upgrades-only', action='store_true', dest='managed_upgrade_only', default=False,
            help='Only use upgrades found in app_name/schema_evolution.py (recommended for deployments)'),
   )
    help = """Interactively runs the SQL statements to non-destructively 
bring your schema into compliance with your models.
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
            
        for app in run_apps:
            #if app.__name__.startswith('django.contrib.'): continue
            self.handle_app(app, **options)

    def handle_app(self, app, **options):
        import deseb.schema_evolution
        deseb.schema_evolution.evolvedb(app, 
            options.get('interactive', True), 
            options.get('do_save', True),
            options.get('verbose', False),
            options.get('managed_upgrade_only', False))
