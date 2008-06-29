from deseb.meta import DBSchema
from deseb.meta import DBTable
from deseb.meta import DBField
from deseb.meta import TreeDiff
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
    Schema "First"
      Table "table1"
        Field "id"
      Table "table2"
        Field "id"
        Field "name"
    d0db1b989c
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
    Schema "First" => Schema "Second"
      Table "table1"
        Field "id"
    * Table "table2" => Table "table3"
      * Field "name" => Field "xxx"
      + Field "yyy"
      - Field "id"
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
    Schema "First"
      Table "table2"
        Field "abc"
    Schema "Second"
      Table "table3"
        Field "abc"
    Schema "First" => Schema "Second"
    * Table "table2" => Table "table3"
        Field "abc"
        * unique: False -> True
    """

def run():
    import doctest
    err, tests = doctest.testmod(report=False)
    if not err: print "All %s tests passed." % tests
    
if __name__ == "__main__":
    run()