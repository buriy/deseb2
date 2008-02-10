from deseb.schema_evolution import NotNullColumnNeedsDefaultException

try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 

class DatabaseOperations:
    def quote_value(self, s):
        if type(s) is bool:
            if s: return "'t'"
            else: return "'f'"
        if type(s) is int:
            return str(s)
        else:
            return u"'%s'" % unicode(s).replace("'","\'")
    
    def __init__(self, connection, style):
        self.connection = connection
        self.style = style
    
    pk_requires_unique = False

    def get_change_table_name_sql( self, table_name, old_table_name ):
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        output.append(
            kw('ALTER TABLE ') + tqn(old_table_name) +
            kw(' RENAME TO ') + tqn(table_name) + ';')
        return output
    
    def get_change_column_name_sql( self, table_name, indexes, old_col_name, new_col_name, col_type, f ):
        # TODO: only supports a single primary key so far
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        for key in indexes.keys():
            if indexes[key]['primary_key']: pk_name = key
        output = []
        output.append( 
            kw('ALTER TABLE ') + tqn(table_name)
            + kw(' RENAME COLUMN ') + fqn(old_col_name)
            + kw(' TO ') + fqn(new_col_name) + ';')
        return output

    def get_change_column_def_sql( self, table_name, col_name, col_type, f, column_flags, f_default, updates ):
        from django.db.models.fields import NOT_PROVIDED
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        if updates['update_type']:
            output.append( 
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ADD COLUMN ') + fqn(col_name+'_tmp') + ' ' + fct(col_type) + ';' )
            output.append( 
                kw('UPDATE ') + tqn(table_name) + 
                kw(' SET ') + fqn(col_name+'_tmp') + 
                ' = ' + fqn(col_name) + ';' )
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' DROP COLUMN ') + fqn(col_name) + ';' )
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' RENAME COLUMN ') + fqn(col_name+'_tmp') + 
                kw(' TO ') + fqn(col_name) + ';' )
        elif updates['update_length']:
            output.append( 
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' ALTER COLUMN ') + fqn(col_name) + 
                kw(' TYPE ')+ fct(col_type) + ';' )

        if updates['update_sequences'] and column_flags and 'sequence' in column_flags:
            seq_name = column_flags['sequence']
            seq_name_correct = table_name+'_'+col_name+'_seq'
            if seq_name != seq_name_correct:
                output.append( 
                    kw('ALTER TABLE ') + tqn(seq_name) +
                    kw(' RENAME TO ') + tqn(seq_name_correct)+';')
                output.append( 
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + tqn(col_name) + 
                    kw(' SET DEFAULT nextval(')+
                    fqv(seq_name_correct)+'::regclass);')

        if updates['update_null']:
            if str(f_default)==str(NOT_PROVIDED) and not f.null: 
                details = 'column "%s" of table "%s"' % (col_name, table_name)
                raise NotNullColumnNeedsDefaultException("when modified " + details)
            if str(f_default)!=str(NOT_PROVIDED) and not f.null: 
                output.append( 
                    kw('UPDATE ') + tqn(table_name) +
                    kw(' SET ') + fqn(col_name) + ' = ' + fqv(f_default) + 
                    kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;') )
            if not f.null:
                output.append( 
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + fqn(col_name) +
                    kw(' SET NOT NULL;') )
            elif not updates['update_type']:
                output.append( 
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + fqn(col_name) +
                    kw(' DROP NOT NULL;') )

        if updates['update_unique'] and f.unique:
            output.append( kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ADD CONSTRAINT ') +
                table_name + '_' + col_name + '_unique_constraint'+
                kw(' UNIQUE(') + fqn(col_name) + kw(')')+';' )
            
        return output
    
    def get_add_column_sql( self, table_name, col_name, col_type, null, unique, primary_key, f_default):
        from django.db.models.fields import NOT_PROVIDED
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        output.append( 
            kw('ALTER TABLE ') + tqn(table_name) +
            kw(' ADD COLUMN ') + fqn(col_name) + ' ' + fct(col_type) + ';' )
        if primary_key: return output
        if str(f_default)==str(NOT_PROVIDED) and not null: 
            details = 'column "%s" into table "%s"' % (col_name, table_name)
            raise NotNullColumnNeedsDefaultException("when added " + details)
        if str(f_default)!=str(NOT_PROVIDED) and not null: 
            output.append( 
                kw('UPDATE ') + tqn(table_name) +
                kw(' SET ') + fqn(col_name) + ' = ' + fqv(f_default) +
                kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;') )
        if not null:
            output.append( 
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ALTER COLUMN ') + fqn(col_name) +
                kw(' SET NOT NULL;') )
        if unique:
            output.append( 
                kw('ALTER TABLE ') + tqn(table_name) + kw(' ADD CONSTRAINT ') +
                table_name + '_' + col_name + '_unique_constraint'+
                kw(' UNIQUE(') + fqn(col_name) + kw(')')+';' )
        return output
    
    def get_drop_column_sql( self, table_name, col_name ):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        output = []
        output.append( 
            kw('ALTER TABLE ') + tqn(table_name) +
            kw(' DROP COLUMN ') + fqn(col_name) + ';' )
        return output
    
    def get_drop_table_sql( self, delete_tables):
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        for table_name in delete_tables:
            output.append( 
                kw('DROP TABLE ')+ tqn(table_name) + ' CASCADE;' )
        return output
    
    def get_autoinc_sql(self, table):
        return None
    

class DatabaseIntrospection:
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_schema_fingerprint( self, cursor, app):
        pass
    
    def get_schema_fingerprint_fv1( self, cursor, app):
        pass

    def get_columns( self, cursor, table_name):
        try:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s",[table_name])
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
        
    def get_known_column_flags_new( self, cursor, table_name, column_name ):
        from django.db.models.fields import NOT_PROVIDED
        dict = {
            'primary_key': False,
            'foreign_key': False,
            'unique': False,
#DEFAULT    'default': '',
            'max_length': '',
            'allow_null': False,
        }
        cursor.execute("""
            SELECT character_maximum_length, is_nullable, column_default, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
            AND table_schema != 'pg_catalog' AND table_schema != 'information_schema'   
            """, [table_name,column_name])
        row = cursor.fetchone()
        # maxlength check goes here
        if row[0] != None:
            dict['max_length'] = str(row[0])
        # null flag check goes here
        if row[1] == 'YES':
            dict['allow_null'] = True 
        
        if row[3] == 'character varying':
            dict['coltype'] = 'varchar'
        elif row[3]=='text':
            dict['max_length'] = 64000
            dict['coltype'] = 'text'
        else:
            dict['coltype'] = row[3]
        # default value check goes here
        if row[2] and row[2][0:7] == 'nextval':
                if row[2].startswith("nextval('") and row[2].endswith("'::regclass)"):
                    dict['sequence'] = row[2][9:-12]
#DEFAULT     elif row[2][0] == "'":
#DEFAULT         dict['default'] = row[2][1:row[2].index("'",1)]
#DEFAULT     else:
#DEFAULT         dict['default'] = row[2]

        cursor.execute("""
            SELECT constraint_name, constraint_type, column_name 
            FROM information_schema.table_constraints 
            INNER JOIN information_schema.constraint_column_usage u USING (constraint_name) 
            WHERE u.table_name = %s AND u.column_name = %s 
            AND NOT (constraint_type = 'UNIQUE' AND 1<(SELECT count(*) 
                    FROM information_schema.constraint_column_usage 
                    WHERE constraint_name = u.constraint_name))
            """, [table_name,column_name])
        for row in cursor.fetchall():
            if row[1]=='PRIMARY KEY': dict['primary_key'] = True
            if row[1]=='FOREIGN KEY': dict['foreign_key'] = True
            if row[1]=='UNIQUE': dict['unique']= True
        return dict
    
    def get_known_column_flags_compare( self, cursor, table_name, column_name ):
        gcfold = self.get_known_column_flags_old(cursor, table_name, column_name)
        gcfnew = self.get_known_column_flags_new(cursor, table_name, column_name)
        d1 = [i for i in dict.items() if not i in gcfnew.items()]
        d2 = [i for i in gcfnew.items() if not i in dict.items()]
        if d1 or d2:
            print 'Diff!', d1, '<->', d2
        return gcfold
            
    def get_known_column_flags( self, cursor, table_name, column_name ):
    #    print "SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef), a.attnotnull, a.attnum, pg_catalog.col_description(a.attrelid, a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid = (SELECT c.oid from pg_catalog.pg_class c where c.relname ~ '^%s$') AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum" % table_name
        cursor.execute("SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef), a.attnotnull, a.attnum, pg_catalog.col_description(a.attrelid, a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid = (SELECT c.oid from pg_catalog.pg_class c where c.relname ~ '^%s$') AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum" % table_name)
        dict = {
            'primary_key': False,
            'foreign_key': False,
            'unique': False,
            'allow_null': False,
            'max_length': None
        }
    
        for row in cursor.fetchall():
            if row[0] == column_name:
        # maxlength check goes here
                dict['allow_null'] = not row[3]
                dict['coltype'] = row[1]
                if row[1][0:17]=='character varying':
                    dict['max_length'] = str(row[1][18:len(row[1])-1])
                    dict['coltype'] = 'varchar'
                elif row[1][0:4]=='text':
                    dict['max_length'] = 1000000000
                # null flag check goes here
                
        # pk, fk and unique checks go here
    #    print "select pg_constraint.conname, pg_constraint.contype, pg_attribute.attname from pg_constraint, pg_attribute where pg_constraint.conrelid=pg_attribute.attrelid and pg_attribute.attnum=any(pg_constraint.conkey) and pg_constraint.conname~'^%s'" % table_name 
        unique_conname = None
        shared_unique_connames = set()
        cursor.execute("select pg_constraint.conname, pg_constraint.contype, pg_attribute.attname from pg_constraint, pg_attribute, pg_class where pg_constraint.conrelid=pg_class.oid and pg_constraint.conrelid=pg_attribute.attrelid and pg_attribute.attnum=any(pg_constraint.conkey) and pg_class.relname='%s'" % table_name )
        for row in cursor.fetchall():
    #        print row
            if row[2] == column_name:
                if row[1]=='p': dict['primary_key'] = True
                if row[1]=='f': dict['foreign_key'] = True
                if row[1]=='u': unique_conname = row[0]
            else:
                if row[1]=='u': shared_unique_connames.add( row[0] )
        if unique_conname and unique_conname not in shared_unique_connames:
            dict['unique'] = True
            
                # default value check goes here
        #cursor.execute("SELECT character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = %s AND column_name = %s" , [table_name,column_name])
        #print 'cursor.fetchall()', cursor.fetchall()
        cursor.execute("select pg_attribute.attname, adsrc from pg_attrdef, pg_attribute WHERE pg_attrdef.adrelid=pg_attribute.attrelid and pg_attribute.attnum=pg_attrdef.adnum and pg_attrdef.adrelid = (SELECT c.oid from pg_catalog.pg_class c where c.relname ~ '^%s$')" % table_name )
        for row in cursor.fetchall():
            if row[0] == column_name:
                if row[1][0:7] == 'nextval': 
                    if row[1].startswith("nextval('") and row[1].endswith("'::regclass)"):
                        dict['sequence'] = row[1][9:-12]
                    continue

        return dict
