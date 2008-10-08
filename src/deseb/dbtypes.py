from django.conf import settings

class DataType(object):
    def __init__(self, coltype, **attrs):
        self.realtype = None
        self.coltype = coltype
        self.attrs = attrs
    
    @property
    def dbtype(self):
        return self.realtype
    
    def clone(self):
        return DataType(self.coltype, **self.attrs)
    
    def __eq__(self, rhs):
        return self.coltype == rhs.coltype and self.attrs == rhs.attrs
    
    def __ne__(self, rhs):
        return not self == rhs
    
    def __repr__(self):
        attrs = ", ".join(["%s=%s" % (k,v) for k,v in sorted(self.attrs.items())])
        return "%s [%s; %s]" % (self.realtype, self.coltype, attrs)

defaults = {
    'sqlite3':{
    },
            
    'mysql': {
        'integer': DataType('int', max_length=11),
        'smallint': DataType('smallint', max_length=6),
        'text': DataType('text', max_length=65534),
        'longtext': DataType('longtext', max_length=1000000000),
        'tinyint': DataType('bool', max_length=1),
        'bool': DataType('bool', max_length=1),
        'boolean': DataType('bool', max_length=1),
        'decimal': 'numeric',
        'double precision': 'double',
    },
    
    'postgresql': {
        'serial': DataType('int'),
        'character varying': 'varchar',
        'integer': 'int',
        'inet': DataType('inet', max_length=15),
        'time without time zone': 'time',
    }
}

defaults['postgresql_psycopg2'] = defaults['postgresql']

backend_defaults = defaults[settings.DATABASE_ENGINE]


"""

COMMON:
def get_field_type(f, empty='unknown'):
    if not f: return empty
    f = f.split('(')[0].split(' CHECK')[0]
    if f in ['integer', 'serial']: return 'int'
    if f in ['tinyint']: return 'bool'
    if f in ['character varying']: return 'varchar'
    if f in ['decimal']: return 'numeric'
    return f    

SQLITE3
if row[2][0:7]=='varchar':
    col['max_length'] = int(row[2][8:-1])
    col['coltype'] = 'varchar'
"""

"""
MYSQL
# maxlength check goes here
if row[1][0:7]=='varchar':
    dict['max_length'] = int(row[1][8:len(row[1])-1])
elif row[1][0:8]=='tinyint(':
    #dict['max_length'] = int(row[1][8:row[1].find(')')])
    dict['dbtype'] = 'bool'
    pass
elif row[1][0:4]=='int(':
    #dict['max_length'] = int(row[1][4:row[1].find(')')])
    dict['dbtype'] = 'integer'
elif row[1]=='text':
    dict['max_length'] = 65534
elif row[1]=='longtext':
    dict['max_length'] = 100000000
"""

"""
POSTGRESQL
# maxlength check goes here
if row[2][0:7]=='varchar':
    col['max_length'] = int(row[2][8:-1])
    col['coltype'] = 'varchar'
    
if row[1][0:17]=='character varying':
    col['max_length'] = int(row[1][18:-1])
if row[1][0:7]=='varchar':
    col['max_length'] = int(row[1][8:-1])
elif row[1] == 'text':
    col['max_length'] = 1000000000
"""

def get_column_type(realtype, **attrs):
    coltype = realtype
    if ' CHECK ' in coltype.upper():
        coltype = coltype.split(' CHECK ',1)[0]
    if coltype.upper().endswith(' AUTO_INCREMENT'):
        attrs['auto_increment'] = True
        coltype = coltype[:-len(' AUTO_INCREMENT')]
    if coltype.upper().endswith(' UNSIGNED'):
        attrs['unsigned'] = True
        coltype = coltype[:-len(' UNSIGNED')]
    if '(' in coltype and coltype.endswith(')'):
        coltype, pars = coltype.split('(')
        pars = [s.strip() for s in pars.split(')')[0].split(',')]
        if len(pars) == 1:
            attrs['max_length'] = int(pars[0])
        if len(pars) == 2:
            attrs['max_digits'] = int(pars[0])
            attrs['decimal_places'] = int(pars[1])
    if settings.DATABASE_ENGINE == 'sqlite3' and coltype == 'decimal':
        #sqlite3 inconsistency in django
        if 'max_digits' in attrs: del attrs['max_digits']
        if 'decimal_places' in attrs: del attrs['decimal_places']
    if coltype.lower() in backend_defaults:
        normtype = backend_defaults[coltype]
        if isinstance(normtype, DataType):
            r = normtype.clone()
            r.attrs.update(attrs)
            if attrs.get('unsigned') and not attrs.get('max_length'):
                r.attrs['max_length'] = r.attrs['max_length'] - 1
        else:
            r = DataType(normtype, **attrs)
    else:
        r = DataType(coltype, **attrs)
    r.realtype = realtype
    return r

def get_field_type(field):
    to_try = ['max_length', 'decimal_places', 'max_digits']
    attrs = {}
    for attr in to_try:
        if hasattr(field, attr) and getattr(field, attr) != None:
            attrs[attr] = getattr(field, attr)
            #print field.db_type(), '->', field.column, attr, getattr(field, attr)
    return get_column_type(field.db_type(), **attrs)
