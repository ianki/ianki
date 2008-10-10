# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""iAnki web server

This is the web server setup of the iAnki plugin for Anki.

"""

__version__ = "0.1"
__all__ = []

import os
import time
from web.SimpleHTTPServer import SimpleHTTPRequestHandler 

# Direct the server to the plugin directory
iankiPath = os.path.dirname(__file__)
SimpleHTTPRequestHandler.baseServerPath = iankiPath

# Hack to get around bug in SimpleHTTPServer file handling
send_head = SimpleHTTPRequestHandler.send_head 

def new_send_head(*a, **kw):
    print 'new_send_head', a, kw
    f = send_head(*a, **kw)
    return f and open(f.name, 'rb')

SimpleHTTPRequestHandler.send_head = new_send_head

def unload():
    # Revert send_head hook
    SimpleHTTPRequestHandler.send_head = send_head

import web
import simplejson
from anki import DeckStorage
from anki.stats import dailyStats, globalStats

urls = (
  '/', 'index',
  '',  'index',
  '/anki/sync.html', 'anki_sync')

render = web.template.render(iankiPath+'/templates/', False) # Cashing is turned off

class index:
    def GET(self):
        web.output(render.ianki())

tables = {}
tables['decks'] = [ 'id',
                    'created',
                    'modified',
                    'description',
                    'version',
                    'currentModelId',
                    'syncName',
                    'lastSync',
                    'hardIntervalMin',
                    'hardIntervalMax',
                    'midIntervalMin',
                    'midIntervalMax',
                    'easyIntervalMin',
                    'easyIntervalMax',
                    'delay0',
                    'delay1',
                    'delay2',
                    'collapseTime',
                    'highPriority',
                    'medPriority',
                    'lowPriority',
                    'suspended',
                    'newCardOrder',
                    'newCardSpacing',
                    'failedCardMax',
                    'newCardsPerDay',
                    'sessionRepLimit',
                    'sessionTimeLimit']
tables['models'] = ['id',
                    'deckId',
                    'created',
                    'modified',
                    'tags',
                    'name',
                    'description',
                    'features',
                    'spacing',
                    'initialSpacing']
tables['cards'] = [ "id",
                    "factId",
                    "cardModelId",
                    "created",
                    "modified",
                    "tags",
                    "ordinal",
                    "question",
                    "answer",
                    "priority",
                    "interval",
                    "lastInterval",
                    "due",
                    "lastDue",
                    "factor",
                    "lastFactor",
                    "firstAnswered",
                    "reps",
                    "successive",
                    "averageTime",
                    "reviewTime",
                    "youngEase0",
                    "youngEase1",
                    "youngEase2",
                    "youngEase3",
                    "youngEase4",
                    "matureEase0",
                    "matureEase1",
                    "matureEase2",
                    "matureEase3",
                    "matureEase4",
                    "yesCount",
                    "noCount",
                    "spaceUntil",
                    "relativeDelay",
                    "isDue",
                    "type",
                    "combinedDue"]
tables['facts'] = [ 'id',
                    'modelId',
                    'created',
                    'modified',
                    'tags',
                    'spaceUntil',
                    'lastCardId']

'''
tables['reviewHistory'] = ['id',
                    'cardId',
                    'time',
                    'lastInterval',
                    'nextInterval',
                    'ease',
                    'delay',
                    'lastFactor',
                    'nextFactor',
                    'reps',
                    'thinkingTime',
                    'yesCount',
                    'noCount']
tables['stats'] = [ 'id',
                    'type',
                    'day',
                    'reps',
                    'averageTime',
                    'reviewTime',
                    # next two columns no longer used
                    'distractedTime',
                    'distractedReps',
                    'newEase0',
                    'newEase1',
                    'newEase2',
                    'newEase3',
                    'newEase4',
                    'youngEase0',
                    'youngEase1',
                    'youngEase2',
                    'youngEase3',
                    'youngEase4',
                    'matureEase0',
                    'matureEase1',
                    'matureEase2',
                    'matureEase3',
                    'matureEase4']
'''

def getFieldList(fields):
    fieldList = '"' + fields[0] + '"'
    for f in fields[1:]:
        fieldList += ', "' + f + '"'
    return fieldList

def getValueList(fields):
    fieldList = '?'
    for f in fields[1:]:
        fieldList += ', ?'
    return fieldList

def getSetList(fields):
    fieldList = '"' + fields[1] + '" = ?'
    for f in fields[2:]:
        fieldList += ', "' + f + '" = ?'
    return fieldList

def procRow(table, row, update, unique=''):
    ret = []
    if not update:
        i = 0
        for f in table:
            if f in ['id', 'factId', 'cardModelId', 'lastCardId', 'cardId', 'deckId', 'modelId', 'currentModelId']:
                ret.append(unique + str(row[i]))
            else:
                ret.append(row[i])
            i += 1
    else:
        i = 1
        for f in table[1:]:
            if f in ['id', 'factId', 'cardModelId', 'lastCardId', 'cardId', 'deckId', 'modelId', 'currentModelId']:
                ret.append(str(row[i]))
            else:
                ret.append(row[i])
            i += 1
        ret.append(str(row[0]))
    return ret

update = {}
def countUpdates():
    ret = 0
    for t in tables.keys():
        ret += len(update[t]['modified'])
        ret += len(update[t]['added'])
    return ret
        
def getUpdate(maxCount):
    ret = {}
    ret['numUpdates'] = 0
    for t in tables.keys():
        ret[t] = {'modified':[], 'added':[]}
        mlen = min(maxCount, len(update[t]['modified']))
        if mlen > 0:
            ret[t]['modified'] = update[t]['modified'][:mlen]
            update[t]['modified'] = update[t]['modified'][mlen:]
            maxCount -= mlen
            ret['numUpdates'] += mlen
        mlen = min(maxCount, len(update[t]['added']))
        if mlen > 0:
            ret[t]['added'] = update[t]['added'][:mlen]
            update[t]['added'] = update[t]['added'][mlen:]
            maxCount -= mlen
            ret['numUpdates'] += mlen
    return ret

def printUpdate(up):
    print >> sys.stderr, "numUpdates", up['numUpdates']
    for t in tables.keys():
        if len(update[t]['modified']) > 0:
            print >>  sys.stderr, t, "modified"
            for i in update[t]['modified']:
                print >>  sys.stderr, "  ", i
        if len(update[t]['added']) > 0:
            print >>  sys.stderr, t, "added"
            for i in update[t]['added']:
                print >>  sys.stderr, "  ", i

class anki_sync:
    def POST(self):
        json = {}
        json['error'] = 0
        json['exception'] = 'Unset'
        try:
            data = simplejson.loads(web.data())
            #print >> sys.stderr, "request", data            
            try:
                if data['method'] == 'getdeck':
                    json['deck'] = ui.ankiQt.syncName
                elif data['method'] == 'realsync':
                    # ToDo: Error if syncName doesn't match the current deck
                    ui.logMsg('Sync started for deck ' + data['syncName'])
                    deck = DeckStorage.Deck(ui.ankiQt.deckPath, rebuild=False)
                    try:
                        # Apply client updates
                        if len(data['reviewHistory']) > 0:
                            ui.logMsg(' Applying %d new reviews' % len(data['reviewHistory']))
                            numApplied = 0
                            try:
                                for review in data['reviewHistory']:
                                    #print >> sys.stderr, 'applyReview', review
                                    def timeOverride():
                                        return review['time']
                                    def thinkingTimeOverride():
                                        return review['thinkingTime']
                                    
                                    timeSave = time.time
                                    time.time = timeOverride
                                    try:
                                        card = deck.cardFromId(int(review['cardId']))
                                        thinkingTimeSave = card.thinkingTime
                                        card.thinkingTime = thinkingTimeOverride
                                        try:
                                            numApplied += 1
                                            deck._globalStats = globalStats(deck.s)
                                            deck._dailyStats = dailyStats(deck.s)
                                            deck.answerCard(card, review['ease'])
                                        finally:
                                            card.thinkingTime = thinkingTimeSave
                                    finally:
                                        time.time = timeSave
                            finally:
                                if numApplied > 0:
                                    # Update anything that may have changed
                                    deck.modified = time.time()
                        
                        # Send host updates
                        json['lastSyncHost'] = deck.modified
                        global update
                        update = {}
                        for t in tables.keys():
                            added = deck.s.all('SELECT %s FROM %s WHERE created > %f' % (getFieldList(tables[t]), t, data['lastSyncHost']))
                            modified = deck.s.all('SELECT %s FROM %s WHERE modified > %f and created <= %f' % (getFieldList(tables[t]), t, data['lastSyncHost'], data['lastSyncHost']))
                            
                            added = [procRow(tables[t], x, False) for x in added]
                            if t in ['cards', 'facts']:
                                for i in range(0,2):
                                    added += added
                            modified = [procRow(tables[t], x, True) for x in modified]
                            
                            if len(modified) > 0:
                                ui.logMsg(' Syncing %d modified %s' % (len(modified), t))
                            if len(added) > 0:
                                ui.logMsg(' Syncing %d new %s' % (len(added), t))
                            
                            tableUpdate = {}
                            '''
                            tableUpdate['added'] = []
                            #json[t+'_added'] = []
                            for i in range(0,1):
                                #json[t+'_added'] += [procRow(tables[t], x, False, str(i)) for x in added]
                                tableUpdate['added'] += [procRow(tables[t], x, False, str(i)) for x in added]
                            #json[t+'_modified'] = [procRow(tables[t], x, True) for x in modified]
                            '''
                            tableUpdate['added']    = [procRow(tables[t], x, False) for x in added]
                            tableUpdate['modified'] = [procRow(tables[t], x, True) for x in modified]
                            
                            update[t] = tableUpdate;
                            
                            json[t+'_sql_insert'] = 'INSERT INTO ' + t + ' (' + getFieldList(tables[t]) + ') VALUES (' + getValueList(tables[t]) + ')'
                            json[t+'_sql_update'] = 'UPDATE ' + t + ' SET ' + getSetList(tables[t]) + ' WHERE id = ?'
                        json['numUpdates'] = countUpdates()
                        json['updates'] = getUpdate(200)
                        #printUpdate(json['updates'])
                        #ui.logMsg(' Sending %d items' % (json['updates']['numUpdates']))
                    finally:
                        deck.save()
                        deck.close()
                        
                    #ui.logMsg('Sync complete')
                elif data['method'] == 'nextsync':
                    json['updates'] = getUpdate(200)
                    #printUpdate(json['updates'])
                    #ui.logMsg(' Sending %d items' % (json['updates']['numUpdates']))
                else:
                    json['error'] = 1
                    json['exception'] = 'Invalid method:' + data['method']
            finally:
                pass
        #finally:
        #    pass
        except Exception, e:
            json['error'] = 1
            json['exception'] = str(e)
            print >> sys.stderr, "Exception", e
            ui.logMsg('There were errors during sync.')
        #print >> sys.stderr, "response", json
        res = simplejson.dumps(json, ensure_ascii=False)
        web.output(res)
    def GET(self):
        self.POST()

web.webapi.internalerror = web.debugerror

import ui
import sys
reload( sys.modules['ianki_ext.ui'] )

ui.urls = urls
ui.glob = globals()