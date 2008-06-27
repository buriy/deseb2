class DatabaseIntrospection: 
    def get_known_column_flags_new(self, cursor, table_name, column_name):
        dict = {
            'primary_key': False,
            'foreign_key': False,
            'unique': False,
#DEFAULT    'default': '',
            'max_length': None,
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
            dict['max_length'] = int(row[0])
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
    
    def get_known_column_flags_compare(self, cursor, table_name, column_name):
        gcfold = self.get_known_column_flags_old(cursor, table_name, column_name)
        gcfnew = self.get_known_column_flags_new(cursor, table_name, column_name)
        d1 = [i for i in dict.items() if not i in gcfnew.items()]
        d2 = [i for i in gcfnew.items() if not i in dict.items()]
        if d1 or d2:
            print 'Diff!', d1, '<->', d2
        return gcfold
            
