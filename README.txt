
ok, this is ugly as heck right now, but here's the basic deal:
this is a standalone implementation of the django schema evolution branch

status:
    pre-alpha
    very crappy code
    only mysql support

setup:
check deseb out
copy or symlink src/deseb into your site-packages folder
add "import deseb" to the top of your models.py

usage:
http://code.djangoproject.com/wiki/SchemaEvolutionDocumentation

important notes:
the sqlevolve command is NOT registered yet!  you must put the following
into django/core/management/commands/sqlevolve.py:
---
from django.core.management.base import AppCommand

class Command(AppCommand):
    help = "Prints the CREATE TABLE SQL statements for the given app name(s)."

    output_transaction = True

    def handle_app(self, app, **options):
        import deseb.schema_evolution
        return '\n'.join(deseb.schema_evolution.get_sql_evolution(app, self.style))
---


