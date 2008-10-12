# Copyright (C) 2008 Victor Miura
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
'''Module for printing nested structures in a more readable manner.'''

from types import *
import sys

def hasContainers(obj):
    if type(obj) in [list, tuple, set]:
        for x in obj:
            if type(x) in [list, tuple, set, dict]:
                return True
    elif type(obj) == dict:
        for x in obj.values():
            if type(x) in [list, tuple, set, dict]:
                return True
    return False

listTypes = {list:'[]', tuple:'()', set:'<>'}
def pretty(obj, indent=0):
    if hasContainers(obj):
        nl = '\n'
        newIndent = indent+1
    else:
        nl = ''
        newIndent = 0
            
    t = type(obj)
    if t in listTypes.keys():
        sys.stderr.write((' ' * indent) + listTypes[t][0] + nl)
        count = 0
        for i in obj:
            if count > 0:
                sys.stderr.write(', ' + nl)
            pretty(i, newIndent)
            count += 1
            
        sys.stderr.write(nl + (' ' * indent) + listTypes[t][1])
    elif t == dict:
        sys.stderr.write((' ' * indent) + '{' + nl)
        count = 0
        for i in obj.keys():
            if count > 0:
                sys.stderr.write(', ' + nl)
            pretty(i, newIndent)
            sys.stderr.write(': ')
            pretty(obj[i], newIndent)
            count += 1
        sys.stderr.write(nl + (' ' * indent) + '}')
    elif t in [str, unicode]:
        sys.stderr.write((' ' * indent) + "'"+unicode(obj).encode('ascii', 'xmlcharrefreplace')+"'")
    else:
        sys.stderr.write((' ' * indent) + unicode(obj).encode('ascii', 'xmlcharrefreplace'))
