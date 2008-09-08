import sha

def indent(strings, delim = '  '):
    return delim+('\n'+delim).join(strings.split('\n'))

class DBEntity(object):
    allowed_args = set([])
    children = ()
    
    def __unicode__(self):
        repr = self.__repr__()
        output = [repr]
        for attr in self.children:
            subitem = getattr(self, attr)
            output.extend([indent(unicode(s)) for s in subitem])
        return '\n'.join(output)
    
    def to_dict(self):
        dict = {}
        if hasattr(self, 'traits'):
            dict['traits'] = self.traits
        for attr in self.children:
            subdict = {}
            subitem = getattr(self, attr)
            for child in subitem:
                subdict[child.name] = child
            dict[attr] = subdict
        return dict
    
    def __getattr__(self, name):
        if name in self.allowed_args:
            return self.traits[name]
        else:
            raise AttributeError, name
    
    def _to_set(self, value):
        if value is None: 
            return set([])
        elif isinstance(value, basestring):
            return set([value])
        else:
            return set(value)
    
    def __setattr__(self, name, value):
        if name == 'aka':
            return object.__setattr__(self, name, self._to_set(value))
        elif name in self.allowed_args:
            self.traits[name] = value
        else:
            return object.__setattr__(self, name, value)
        
    def items(self):
        if hasattr(self, 'traits'):
            return self.traits.items()
        else:
            return []
    
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
        return 'Schema "%s":' % self.name
    
    def get_hash(self):
        output = self.__unicode__()
        return sha.new(output).hexdigest()[:10]

class EMPTY(object): pass 

class AmbiguityOnRenameException(Exception): pass

class NodeChange(object):
    def __init__(self, left, right, nested = None):
        if nested is None:
            nested = []
        self.nested = nested
        self.left = left
        self.right = right

    def format(self, item):
        return unicode(item) 
    
    def rformat(self, item):
        return repr(item) 
    
    def action(self):
        if self.left is None:
            return 'add'
        elif self.right is None:
            return 'remove'
        else:
            lname = self.rformat(self.left)
            rname = self.rformat(self.right)
            if lname != rname:
                return 'rename'
            else:
                return 'update'
    
    def attr(self):
        if self.left is None:
            return self.rformat(self.right)
        if self.right is None:
            return self.rformat(self.left)
        lname = self.rformat(self.left)
        rname = self.rformat(self.right)
        if lname != rname:
            return "%s => %s" % (lname, rname)
        else:
            return lname
    
    def __repr__(self):
        action = (self.action()+'ing').replace('eing', 'ing').capitalize()
        return "%s %s" % (action, self.attr()) 
    
    def __unicode__(self):
        output = []
        if self.left is None:
            output.append(indent(self.format(self.right), '+ '))
        elif self.right is None:
            output.append(indent(self.format(self.left), '- '))
        else:
            lname = self.rformat(self.left)
            rname = self.rformat(self.right)
            if lname != rname:
                if isinstance(self.left, DBEntity) and isinstance(self.right, DBEntity):
                    output.append('* '+lname + ' => ' + rname)
                else:
                    output.append('* '+self.klass+': '+lname + ' -> ' + rname)
            else:
                output.append('  '+lname)
        
        for child in self.nested:
            output.append(indent(unicode(child)))
        return '\n'.join(output)

class AttributeChange(NodeChange):
    def __init__(self, left, right, klass):
        super(AttributeChange, self).__init__(left, right)
        self.klass = klass
        
    def action(self):
        return "change"
    
    def format(self, item):
        return '%s "%s"' % (self.klass, item)
    
    def __unicode__(self):
        return '* '+self.klass+': %s -> %s' % (self.left, self.right)
    
    def __repr__(self):
        return "Changing attribute "+self.klass

class TreeDiff(object):
    def __init__(self, m1, m2):
        self.m1 = m1
        self.m2 = m2
        self.changes = self.diff(m1, m2)

    def __nonzero__(self):
        return bool(self.changes)

    def __unicode__(self):
        fmt = 'Diff: %s => %s' % (self.m1.name, self.m2.name)
        return fmt + '\n' +self.__repr__()

    def __repr__(self):
        return "\n".join([unicode(x) for x in self.changes])

#    def dict_diff(self, old, new):
#        a = old.items()
#        b = new.items()
#        d1 = [i for i in a if not i in b]
#        d2 = [i for i in b if not i in a]
#        if d1 or d2:
#            return d1, d2
#    
    def diff(self, old, new):
        oldtypes = old.to_dict()
        newtypes = new.to_dict()
        
        groups = set(oldtypes.keys()) | set(newtypes.keys())
        
        changes = []
        for group in groups:
            olddict = oldtypes.get(group, [])
            newdict = newtypes.get(group, [])

            renamed = []
            
            oldkeys = set(olddict.keys())
            
            for newname, newitem in sorted(newdict.iteritems()):
                olditem = None
                oldname = None
                if newname in oldkeys:
                    oldname = newname
                    olditem = olddict[newname]
                elif hasattr(newitem, 'aka'):
                    intersect = oldkeys & set(newitem.aka)
                    if len(intersect)>1: 
                        msg = "For "+repr(newitem)+" choices: "+tuple(intersect)
                        raise AmbiguityOnRenameException(msg) 
                    if intersect:
                        oldname = intersect.pop()
                        renamed.append(oldname)
                        olditem = olddict[oldname]
                
                if oldname: 
                    if isinstance(olditem, DBEntity):
                        subquery = self.diff(olditem, newitem)
                        if subquery or oldname != newname: 
                            changes.append(NodeChange(olditem, newitem, subquery)) #update
                    elif oldname != newname:
                        raise Exception("Invalid schema.")
                    elif olditem != newitem:
                        changes.append(AttributeChange(olditem, newitem, newname))
                else:
                    changes.append(NodeChange(None, newitem)) #add

            for oldname, olditem in sorted(olddict.iteritems()):
                if not oldname in newdict and not oldname in renamed:
                    changes.append(NodeChange(olditem, None)) #remove
                    
        return changes
