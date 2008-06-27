from deseb.differ import DBEntity
from deseb.differ import TreeDiff
import sha

class DBField(DBEntity):
    allowed_args = set(['allow_null', 'coltype', 'primary_key', 'foreign_key', 
                        'unique', 'max_length', 'sequence'])
    def __init__(self, name = None, aka=None, **kwargs):
        if not set(kwargs) <= self.allowed_args:
            raise Exception("Unsupported args: %s" % (set(kwargs) - self.allowed_args))
        self.name = name
        self.aka = aka
        self.traits = kwargs
    
    def __repr__(self):
        return 'Field "%s"' % self.name
#        traits = []
#        for k,v in sorted(self.traits.iteritems()):
#            traits.append('%s=%s' % (k,v)) 
#        return 'Field "%s", %s' % (self.name, ', '.join(traits))
    
class DBIndex(DBEntity):
    allowed_args = set(['pk', 'unique'])
    def __init__(self, name, pk=False, unique=False):
        self.name = name
        self.traits = dict(pk = pk, unique = unique)

    def __repr__(self):
        return 'Index "%s"' % self.name

class DBTable(DBEntity):
    children = ['fields', 'indexes']

    def __init__(self, name, aka=None, **kwargs):
        self.name = name
        self.fields = []
        self.indexes = []
        self.aka = aka
        self.traits = kwargs
        
    def get_field(self, name):
        for f in self.fields:
            if f.name == name:
                return f 

    def __repr__(self):
        return 'Table "%s"' % self.name

class DBSchema(DBEntity):
    children = ('tables',)
    def __init__(self, name = 'Schema'):
        self.name = name
        self.tables = []
    
    def __repr__(self):
        return "%s:" % self.name
    
    def get_hash(self):
        output = self.__unicode__()
        return sha.new(output).hexdigest()[:10]

def try_diff1():
    schema = DBSchema('First')
    table1 = DBTable('table1')
    table1.fields.append(DBField('id', primary_key=True))
    table2 = DBTable('table2')
    table2.fields.append(DBField('id'))
    table2.fields.append(DBField('name'))
    schema.tables.append(table1)
    schema.tables.append(table2)
    print unicode(schema)
    print schema.get_hash()

def test_diff1():
    """
    >>> try_diff1()
    First:
      Table "table1"
        Field "id"
      Table "table2"
        Field "id"
        Field "name"
    2b49284c2c
    """
    
def try_diff2():
    f = DBField('xxx', primary_key=False)
    print f.primary_key
    print f.name
    print f
    try:
        print f.yyy
    except AttributeError:
        print "no f.yyy -- that's ok"
def test_diff2():
    """
    >>> try_diff2()
    False
    xxx
    Field "xxx"
    no f.yyy -- that's ok
    """
    
def try_diff3():
    schema = DBSchema('First')
    table1 = DBTable('table1')
    table1.fields = [DBField('id', primary_key=True)]
    table2 = DBTable('table2')
    table2.fields = [DBField('id'), DBField('name')]
    schema.tables = [table1, table2]

    schema2 = DBSchema('Second')
    table3 = DBTable('table3', aka='table2')
    table3.fields = [DBField('xxx', aka='name'), DBField('yyy', aka='')]
    schema2.tables = [table1, table3]
    print unicode(TreeDiff(schema, schema2))

def test_diff3():
    """
    >>> try_diff3()
    Diff: First: -> Second:
      tables
      * table2->table3
      *   fields
      *   + Field "yyy"
      *   - Field "id"
    """

def try_diff4():
    schema = DBSchema('First')
    table2 = DBTable('table2')
    table2.fields.append(DBField('abc'))
    table2.get_field('abc').unique = False
    schema.tables.append(table2)
    
    schema2 = DBSchema('Second')
    table3 = DBTable('table3', aka='table2')
    table3.fields.append(DBField('abc'))
    table3.get_field('abc').unique = True
    schema2.tables.append(table3)
    print unicode(schema)
    print unicode(schema2)
    print unicode(TreeDiff(schema, schema2))

def test_diff4():
    """
    >>> try_diff4()
    Diff: First: -> Second:
    """

def run():
    import doctest
    err, tests = doctest.testmod(report=False)
    if not err: print "All %s tests passed." % tests
    
if __name__ == "__main__":
    run()