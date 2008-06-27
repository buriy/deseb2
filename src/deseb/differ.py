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
    
class EMPTY(object): pass 
class TreeDiff(object):
    def __init__(self, m1, m2):
        self.m1 = m1
        self.m2 = m2
        self.changes = self.diff(m1, m2)

    def __unicode__(self):
        s = "%s -> %s" % (repr(self.m1), repr(self.m2))
        fmt = 'Diff: %s' % s
        return self.format(fmt, self.changes)

    def __repr__(self):
        import pprint
        return pprint.pformat(self.changes)

    def to_dict(self, el):
        if isinstance(el, dict):
            return el
        if isinstance(el, DBEntity):
            return el.to_dict()
        return el
    
    def dict_diff(self, old, new):
        a = old.items()
        b = new.items()
        d1 = [i for i in a if not i in b]
        d2 = [i for i in b if not i in a]
        if d1 or d2:
            return d1, d2
    
    def format(self, name, changes):
        output = []
        if isinstance(changes, basestring):
            return changes
        elif changes:
            output.append(name)
            for key1, key2, value in changes:
                #print '@=>', name, ';', key1, '=>', key2, ';', type(value)
                if key2==EMPTY:  # remove
                    if isinstance(value, DBEntity):
                        output.append(indent(unicode(value), '- '))
                    else:
                        output.append(indent(key1+': '+unicode(value), '- '))
                elif key1==EMPTY: # add
                    if isinstance(value, DBEntity):
                        output.append(indent(unicode(value), '+ '))
                    else:
                        output.append(indent(key2+': '+unicode(value), '+ '))
                elif isinstance(value, list):
                    if key1 == key2: # edit subitems
                            output.append(indent(self.format(key1, value)))
                    else: # rename
                            rename = key1 + '->' + key2 
                            output.append(indent(self.format(rename, value), '* '))
                else: # edit item
                        output.append('* ' + key1 + ': ' + unicode(value))
        return '\n'.join(output)
    
    def diff(self, old, new):
        olddict = self.to_dict(old)
        newdict = self.to_dict(new)
        
        if not isinstance(olddict, dict) or not isinstance(newdict, dict):
            if olddict != newdict:
                return '%s -> %s' % (olddict, newdict)
            else:
                return
        
        oldkeys = set(olddict.keys())
        changes = []
        renamed = []
        for newname, newitem in sorted(newdict.iteritems()):
            if newname in oldkeys: 
                olditem = olddict[newname]
                subquery = self.diff(olditem, newitem)
                if subquery:
                    changes.append((newname, newname, subquery)) #update
            elif hasattr(newitem, 'aka'):
                intersect = oldkeys & set(newitem.aka)
                #print 'Aka check:', newname, newitem.aka, oldkeys, '->', intersect
                if len(intersect)>1: raise Exception("More than one aka") 
                if intersect:
                    oldname = intersect.pop()
                    renamed.append(oldname)
                    olditem = olddict[oldname]
                    subquery = self.diff(olditem, newitem)
                    #print 'Subquery:', subquery
                    if subquery:
                        changes.append((oldname, newname, subquery)) #rename
                else: 
                    changes.append((EMPTY, newname, newitem)) #add
                        
        for oldname, olditem in sorted(olddict.iteritems()):
            if not oldname in newdict and not oldname in renamed:
                changes.append((oldname, EMPTY, olditem)) #remove
        return changes


if __name__ == "__main__":
    from dbmodel import run
    run()