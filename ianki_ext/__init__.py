# Copyright (C) 2008 Victor Miura
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""iAnki web server

This is the web server setup of the iAnki plugin for Anki.

"""

import os
import sys
import time
import slimmer

import ui
reload( sys.modules['ianki_ext.ui'] )

__version__ = ui.__version__
__all__ = []

#import pretty
#reload( sys.modules['ianki_ext.pretty'] )

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
from anki import DeckStorage, cards
from anki.stats import dailyStats, globalStats

urls = (
  '/', 'index',
  '',  'index',
  '/cache.manifest',  'cache_manifest',
  '/anki/install.html', 'anki_install',
  '/anki/sync.html', 'anki_sync')

render = web.template.render(iankiPath+'/templates/', False) # Cashing is turned off

class index:
    def GET(self):
        # The index just redirects to the installer, passing it the current location
        redirectHTML = '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <title>iAnki (%(version)s) - launcher</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; user-scalable=1;" />
        <script type="text/javascript">
            window.location = window.location + "anki/install.html?loc=" + escape(window.location)
        </script>
    </head>
    <body>
    </body>
</html> ''' % {'version':ui.__version__}
        web.output(redirectHTML)

makeSlim = True
        
class anki_install:
    def GET(self):
        if (web.ctx.environ['HTTP_USER_AGENT'].lower().find('iphone') < 0) and (web.ctx.environ['HTTP_USER_AGENT'].lower().find('ipod') < 0):
            iPhone = False
        else:
            iPhone = True
            
        import base64
        # css
        f = open(iankiPath+'/static/base.css')
        css = f.read()
        f.close()
        
        if iPhone:
            f = open(iankiPath+'/static/anki-logo.png', 'rb')
            touchicon = '<link rel="apple-touch-icon" href="data:image/png;base64,%s"/>' % base64.b64encode(f.read())
            f.close()
            favicon = ""
            joose = ""
            orm = ""
        else:
            touchicon = ""
            # favicon
            f = open(iankiPath+'/static/favicon.ico', 'rb')
            favicon = '<link rel="shorcut icon" href="data:image/ico;base64,%s"/>' % base64.b64encode(f.read())
            f.close()
            f = open(iankiPath+'/static/joose.mini.js')
            joose = f.read()
            f.close()
            f = open(iankiPath+'/static/orm_async.js')
            orm = f.read()
            f.close()
        f = open(iankiPath+'/static/mootools-1.2.1-core.js')
        s1 = f.read()
        f.close()
        f = open(iankiPath+'/static/ianki.js')
        s2 = f.read()
        f.close()
        f = open(iankiPath+'/templates/ianki.html')
        iankiHTML = f.read()
        f.close()
        
        if makeSlim:
            s2 = slimmer.js_slimmer(s2)            
        
        iankiHTML = iankiHTML % {'version':ui.__version__, 'favicon':favicon, 'touchicon':touchicon, 'css':css, 'joose':joose, 'orm':orm, 'mootools':s1, 'ianki':s2, 'location':web.input(loc='').loc}
        
        #if makeSlim:
        #    iankiHTML = slimmer.xhtml_slimmer(iankiHTML)
            
        test64 = base64.b64encode(iankiHTML)
        #import urllib
        #testUrlencode = urllib.urlencode(magicHTML)
        #dataURL = r'<a href="data:text/html;charset=utf-8;base64,%s" >Click here</a>' % test64
        installHTML = r'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
    <head>
        <title>iAnki (%(version)s) - installer</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; user-scalable=1;" />
    </head>
    <body>
        <div align='center'>
        <span style="font-size: 20px;">Bookmark the following link</span><br>
        <a style="font-size: 32px;" href="data:text/html;charset=utf-8;base64,%(payload)s" >iAnki (%(version)s)</a>
        </div>
    </body>
</html>
''' % {'version':ui.__version__, 'payload':test64}
        web.output(installHTML)

'''
class index:
    def GET(self):
        #ui.logMsg('HTTP_USER_AGENT: ' + web.ctx.environ['HTTP_USER_AGENT'])
        if (web.ctx.environ['HTTP_USER_AGENT'].lower().find('iphone') < 0) and (web.ctx.environ['HTTP_USER_AGENT'].lower().find('ipod') < 0):
            useGears = True
        else:
            useGears = False
        web.output(render.ianki(__version__, useGears))
'''

class cache_manifest:
    def GET(self):
        web.header('Content-Type', 'text/cache-manifest')
        web.output(render.cache_manifest())
        
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
        ret += len(update[t]['removed'])
        ret += len(update[t]['modified'])
        ret += len(update[t]['added'])
    return ret

def getUpdate(maxCount):
    ret = {}
    ret['numUpdates'] = 0
    for t in tables.keys():
        ret[t] = {'modified':[], 'added':[], 'removed':[]}
        mlen = min(maxCount, len(update[t]['removed']))
        if mlen > 0:
            ret[t]['removed'] = update[t]['removed'][:mlen]
            update[t]['removed'] = update[t]['removed'][mlen:]
            maxCount -= mlen
            ret['numUpdates'] += mlen
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

def procSync(inputData):
    json = {}
    json['error'] = 0
    json['exception'] = 'Unset'
    try:
        data = simplejson.loads(inputData)
        #print >> sys.stderr, "request"
        #pretty.pretty(data)
        try:
            if data['method'] == 'getdeck':
                ui.logMsg('Sync started')
                json['deck'] = ui.ankiQt.syncName
            elif data['method'] == 'realsync':
                # ToDo: Error if syncName doesn't match the current deck
                ui.logMsg('Syncing deck ' + data['syncName'])
                deck = DeckStorage.Deck(ui.ankiQt.deckPath, rebuild=False)
                try:
                    deck.rebuildQueue()
                    # Apply client updates
                    if len(data['reviewHistory']) > 0:
                        ui.logMsg(' Applying %d new reviews' % len(data['reviewHistory']))
                        timeSave = time.time
                        thinkingTimeSave = cards.Card.thinkingTime
                        numApplied = 0
                        numDropped = 0
                        try:
                            def timeOverride():
                                    return review['time']
                            def thinkingTimeOverride(self):
                                return review['thinkingTime']
                            
                            try:
                                deck._globalStats = globalStats(deck)
                                deck._dailyStats = dailyStats(deck)
                            except:
                                deck._globalStats = globalStats(deck.s)
                                deck._dailyStats = dailyStats(deck.s)
                            
                            time.time = timeOverride
                            cards.Card.thinkingTime = thinkingTimeOverride
                            
                            for review in data['reviewHistory']:
                                try:
                                    card = deck.cardFromId(int(review['cardId']))
                                    if review['reps'] == card.reps + 1: # Apply only in order reps
                                        deck.answerCard(card, review['ease'])
                                        numApplied += 1
                                    else:
                                        numDropped += 1
                                except:
                                    numDropped += 1
                        finally:
                            time.time = timeSave
                            cards.Card.thinkingTime = thinkingTimeSave
                            if numApplied > 0:
                                # Update anything that may have changed
                                deck.modified = time.time()
                                deck.save()
                            if numDropped > 0:
                                ui.logMsg(' Dropped %d stale reviews' % numDropped)

                    # Send host updates
                    json['lastSyncHost'] = time.time()
                    global update
                    update = {}

                    cardFields = tables['cards']
                    cardIdIndex = cardFields.index('id')
                    cardFactIdIndex = cardFields.index('factId')
                    cardModifiedIndex = cardFields.index('modified')
                    factFields = tables['facts']
                    factIdIndex = factFields.index('id')
                    factModelIdIndex = factFields.index('modelId')
                    factModifiedIndex = factFields.index('modified')
                    modelFields = tables['models']
                    modelIdIndex = modelFields.index('id')
                    modelModifiedIndex = modelFields.index('modified')

                    # Get cards to review for the next 2 days, up to maxCards
                    maxCards = 400
                    gotCards = 0
                    pickCards = []
                    pickCardsIds = set()
                    checkTime = time.time()
                    prevTime = 0
                    for hour in range(0, 48, 4):
                        if gotCards == maxCards:
                            break
                        # First pick due failed cards
                        failedCards = deck.s.all('SELECT %s FROM cards WHERE \
                                            type = 0 AND combinedDue >= %f AND combinedDue <= %f AND priority != 0 \
                                            ORDER BY combinedDue LIMIT %d' % (getFieldList(tables['cards']), prevTime, checkTime, maxCards-gotCards))

                        for c in failedCards:
                            cardId = c[cardIdIndex]
                            if cardId not in pickCardsIds:
                                pickCardsIds.add(cardId)
                                pickCards.append(c)
                                gotCards += 1

                        # Next pick due review cards
                        reviewCards = deck.s.all('SELECT %s FROM cards WHERE \
                                            type = 1 AND combinedDue >= %f AND combinedDue <= %f AND priority != 0 \
                                            ORDER BY priority desc, relativeDelay LIMIT %d' % (getFieldList(tables['cards']), prevTime, checkTime, maxCards-gotCards))

                        for c in reviewCards:
                            cardId = c[cardIdIndex]
                            if cardId not in pickCardsIds:
                                pickCardsIds.add(cardId)
                                pickCards.append(c)
                                gotCards += 1

                        prevTime = checkTime - 60
                        checkTime += 60 * 60

                    # Finally pick new cards
                    if gotCards < maxCards:
                        if deck.newCardOrder == 0: # random
                            newCards = deck.s.all('SELECT %s FROM cards WHERE \
                                                type = 2 \
                                                ORDER BY priority desc, factId, ordinal LIMIT %d' % (getFieldList(tables['cards']), maxCards - gotCards))
                        else: # ordered
                            newCards = deck.s.all('SELECT %s FROM cards WHERE \
                                                type = 2 \
                                                ORDER BY priority desc, due LIMIT %d' % (getFieldList(tables['cards']), maxCards - gotCards))
                        for c in newCards:
                            cardId = c[cardIdIndex]
                            if cardId not in pickCardsIds:
                                pickCardsIds.add(cardId)
                                pickCards.append(c)
                                gotCards += 1

                    #print >> sys.stderr, 'Sync', len(pickCards)

                    haveCards = set()
                    for i in data['cardIds']:
                        haveCards.add(int(i))
                    haveFacts = set()
                    for i in data['factIds']:
                        haveFacts.add(int(i))
                    haveModels = set()
                    for i in data['modelIds']:
                        haveModels.add(int(i))

                    updateCards = [[],[],[]] # modify, add, remove
                    updateFacts = [[],[],[]] # modify, add, remove
                    updateModels = [[],[],[]] # modify, add, remove

                    pickFacts = {}
                    for card in pickCards:
                        cardId = card[cardIdIndex]
                        if cardId in haveCards:
                            if card[cardModifiedIndex] > data['lastSyncHost']:
                                updateCards[0].append( procRow(cardFields, card, True) ) # Modify
                            haveCards.remove(cardId)
                        else:
                            updateCards[1].append( procRow(cardFields, card, False) ) # Add
                        pickFacts[card[cardFactIdIndex]] = None

                    pickModels = {}
                    for factId in pickFacts.keys():
                        fact = deck.s.first('SELECT %s FROM facts WHERE id=%d' % (getFieldList(factFields), factId))
                        if factId in haveFacts:
                            if fact[factModifiedIndex] > data['lastSyncHost']:
                                updateFacts[0].append( procRow(factFields, fact, True) ) # Modify
                            haveFacts.remove(factId)
                        else:
                            updateFacts[1].append( procRow(factFields, fact, False) ) # Add
                        pickModels[fact[factModelIdIndex]] = None

                    for modelId in pickModels.keys():
                        model = deck.s.first('SELECT %s FROM models WHERE id=%d' % (getFieldList(modelFields), modelId))
                        if modelId in haveModels:
                            if model[modelModifiedIndex] > data['lastSyncHost']:
                                updateModels[0].append( procRow(modelFields, model, True) ) # Modify
                            haveModels.remove(modelId)
                        else:
                            updateModels[1].append( procRow(modelFields, model, False) ) # Add

                    # Mark the remaining items for removal
                    for x in haveCards:
                        updateCards[2].append(str(x))
                    for x in haveFacts:
                        updateFacts[2].append(str(x))
                    for x in haveModels:
                        updateModels[2].append(str(x))

                    update['cards'] = {'modified': updateCards[0], 'added': updateCards[1], 'removed': updateCards[2]}
                    update['facts'] = {'modified': updateFacts[0], 'added': updateFacts[1], 'removed': updateFacts[2]}
                    update['models'] = {'modified': updateModels[0], 'added': updateModels[1], 'removed': updateModels[2]}

                    addedDeck = deck.s.all('SELECT %s FROM %s WHERE created > %f' % (getFieldList(tables['decks']), 'decks', data['lastSyncHost']))
                    modifiedDeck = deck.s.all('SELECT %s FROM %s WHERE modified > %f and created <= %f' % (getFieldList(tables['decks']), 'decks', data['lastSyncHost'], data['lastSyncHost']))
                    update['decks'] = { 'modified': [procRow(tables['decks'], x, True) for x in modifiedDeck],
                                        'added': [procRow(tables['decks'], x, False) for x in addedDeck],
                                        'removed': [] }

                    for t in tables.keys():
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
    #print >> sys.stderr, "response"
    #pretty.pretty(json)
    res = simplejson.dumps(json, ensure_ascii=False)
    return res

syncData = {}

class anki_sync:
    def GET(self):
        input = web.input(id=None, togo='0', payload='')
        #print >> sys.stderr, "     id:", input.id
        #print >> sys.stderr, "   togo:", input.togo
        #print >> sys.stderr, "payload:", input.payload
        
        ret = "'bad'"
        
        if id:
            if id in syncData:
                syncData[id] += input.payload
            else:
                syncData[id] = input.payload
                
            if int(input.togo) == 0:
                #print >> sys.stderr, "process:", syncData[id]
                ret = procSync(syncData[id])
                del syncData[id]
            else:
                ret = "'continue'"
        
        #data = simplejson.loads(input.json)
        out = u"request_callback(%s);" % ret
        web.header('Content-Type', 'text/javascript')
        web.output(out)
        #ui.logMsg(' done %d bytes' % len(out));
web.webapi.internalerror = web.debugerror

ui.urls = urls
ui.glob = globals()
