from deseb.schema_evolution import evolvedb
from deseb.schema_evolution import get_sql_fingerprint
from deseb.schema_evolution import get_sql_evolution
from deseb.common import management

def get_sql_evolution_v0_96(app, do_notify=False):
    return get_sql_evolution(app, management.style, do_notify)

def run_sql_evolution_v0_96(app, interactive=True, do_save=True, do_notify=False):
    return evolvedb(app, interactive, do_save, do_notify)

def get_sql_fingerprint_v0_96(app):
    return get_sql_fingerprint(app, management.style)

