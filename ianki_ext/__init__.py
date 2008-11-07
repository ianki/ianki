# Copyright (C) 2008 Victor Miura
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""iAnki web server

This is the web server setup of the iAnki plugin for Anki.

"""

import os
import sys
import time

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
  '/anki/sync.html', 'anki_sync',
  '/anki/sync2.html', 'anki_sync2')

render = web.template.render(iankiPath+'/templates/', False) # Cashing is turned off

class index:
    def GET(self):
        f = open(iankiPath+'/static/base.css')
        css = f.read()
        f.close()
        print >>  sys.stderr, css
        f = open(iankiPath+'/static/mootools.js')
        s1 = f.read()
        f.close()
        f = open(iankiPath+'/static/ianki.js')
        s2 = f.read()
        f.close()
        magicHTML = r'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html manifest="cache.manifest">
    <head>
        <meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; user-scalable=1;" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <!--meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" /-->
        
        <title>iAnki (0.2b1) - loading...</title>
        
        <!--
        <link rel="stylesheet" type="text/css" href="/static/base.css">
        
        <link rel="shorcut icon" href="/static/favicon.ico"/>
        <link rel="apple-touch-icon" href="/static/anki-logo.png"/>
        -->
        
        <STYLE>
        %s
        </STYLE>       
        <script type="text/javascript">
            var iankiVersion = 'iAnki ($version)';
            
            /**
            * Tests if an element is defined.
            * @param type - The type of the element to be tested.
            */
            function isDefined(type) {
             return type != 'undefined' && type != 'unknown';
            }
            
            /**
            * Retrieve a DOM element by its ID.
            * @param id - The ID of the element to locate.
            */
            function getDOMElementById(id) {
             if (isDefined(typeof document.getElementById)) {
                return document.getElementById(id);
             } else if (isDefined(typeof document.all)) {
                return document.all[id];
             } else {
               throw new Error("Can not find a method to locate DOM element.");
               return null;
             }
            }
        </script>

        <script type="text/javascript">
        %s
        </script>
        <script type="text/javascript">
        %s
        </script>

    </head>
    <body>
    
    <div id='infoMode' style='display:none'>
        <div style="margin: 16px">
            <div id="info" style="font-size: 32px; ">Welcome!</div>
        </div>
    </div>
    
    <div id='reviewMode' style='display:none'>
        <div id="reviewContent" style="margin: 16px 0px 16px 16px">
            <div id="question" style="font-size: 20px; ">Sample question</div>
            <div id="padding" style="font-size: 4px; ">&nbsp</div>
            
            <div id="showAnswerDiv" align='center'>
                <button id="showAnswer" title="Show the answer" style="font-size: 28px; " onclick="iAnki.deck.showAnswer()">Show answer</button>
                <div id="lastCardInfo" align='center' style="font-size: 10px; margin-top=30px; "></div>
            </div>
            
            <div id="answerSide" style='display:none'>
                <div id="answer" style="font-size: 20px; ">Sample answer</div>
                <div id="padding" style="font-size: 4px; ">&nbsp</div>
                <div align='center'>
                    <button id='answer0' title='First time' style='font-size: 28px; ' onclick='iAnki.deck.answerCard(0)'>0</button>
                    <button id='answer1' title='Made a mistake' style='font-size: 28px; ' onclick='iAnki.deck.answerCard(1)'>1</button>
                    <button id='answer2' title='Difficult' style='font-size: 28px; ' onclick='iAnki.deck.answerCard(2)'>2</button>
                    <button id='answer3' title='About right' style='font-size: 28px; ' onclick='iAnki.deck.answerCard(3)'>3</button>                    
                    <button id='answer4' title='Easy' style='font-size: 28px; ' onclick='iAnki.deck.answerCard(4)'>4</button>
                </div>
            </div>
        </div>
    </div>
    
    <div id='changeDeckMode' style='display:none' style="margin: 16px">
        <div id="info" style="font-size: 32px; margin: 16px">Change deck</div>
        <div id="deckTable"></div>
    </div>
    
    <div id="padding" style="font-size: 40x; ">&nbsp</div>
    <h1>
        <table width=100%%><TR>
            <td width=70%%>
                <span id='title'>iAnki - Welcome</span>
            </td>
            <td align="right">
                <button title="Choose deck" id="chooseDeck" onclick="iAnki.chooseDeck()">Deck</button>                
                <button title="Sync deck" id="syncDeck" onclick="iAnki.syncDeck(1)">Sync</button>
                <!--<button title="More" id="more">More</button>-->
            </td>
        </tr></table>
    </h1>
    
    <!--
    <div id="vertical_slide" style="margin: 16px">
        <table width=100%%>
        <tr><td>Mark card</td> <td><input type=checkbox id='markCard' name="markCard" title="Mark card"/></td></tr>
        <tr><td>Tags</td> <td><input type=text id='cardTags' name='cardTags' title="Card tags"/></td></tr>
        </table>
	</div>
    -->

    <div id='debugLog'>
        <span id="ankilog"></span>
    </div>
	</body>
</html>
''' % (css, s1, s2)
        
        import base64
        test64 = base64.b64encode(magicHTML)
        dataURL = r'<a href="data:text/html;charset=utf-8;base64,%s" >Click here</a>' % test64
        indexHTML = r'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
    <title>Magic URL</title>
</head>
<body>
    %s
</body>
</html>
''' % dataURL
        web.output(indexHTML)

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

class anki_sync:
    def POST(self):
        json = {}
        json['error'] = 0
        json['exception'] = 'Unset'
        try:
            data = simplejson.loads(web.data())
            #print >> sys.stderr, "request"
            #pretty.pretty(data)
            try:
                if data['method'] == 'getdeck':
                    json['deck'] = ui.ankiQt.syncName
                elif data['method'] == 'realsync':
                    # ToDo: Error if syncName doesn't match the current deck
                    ui.logMsg('Sync started for deck ' + data['syncName'])
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
        web.output(res)
    def GET(self):
        self.POST()

class anki_sync2:
    def GET(self):
        #print >> sys.stderr, "anki_sync2 was called", web.input()
        
        json = {}
        json['error'] = 0
        json['exception'] = 'Unset'
        try:
            print >> sys.stderr, "anki_sync2:", web.input()
            input = web.input(json='{}')
            data = simplejson.loads(input.json)
            print >> sys.stderr, "request", data
            #pretty.pretty(data)
            try:
                if data['method'] == 'getdeck':
                    json['deck'] = ui.ankiQt.syncName
                elif data['method'] == 'realsync':
                    # ToDo: Error if syncName doesn't match the current deck
                    ui.logMsg('Sync started for deck ' + data['syncName'])
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

                        #updateCards = [[],[],[]] # modify, add, remove
                        #updateFacts = [[],[],[]] # modify, add, remove
                        #updateModels = [[],[],[]] # modify, add, remove
                        
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
        
        #pretty.pretty(json)
        res = simplejson.dumps(json, ensure_ascii=False)
        #web.output('request_callback("%s");' % res)
        out = u"request_callback(%s);" % res
        '''
        out = out.replace("\\", "\\^_")
        out = out.replace("\b", "\\b")
        out = out.replace("\t", "\\t")
        out = out.replace("\n", "\\n")
        out = out.replace("\f", "\\f")
        out = out.replace("\r", "\\r")
        out = out.replace('"', '\\"')
        out = out.replace("\\^_", "\\\\")
        
        #$specialChars: {'\b': '\\b', '\t': '\\t', '\n': '\\n', '\f': '\\f', '\r': '\\r', '"' : '\\"', '\\': '\\\\'},
        '''
        
        #print >> sys.stderr, "response: '"+ out +"'"
        web.output(out)
        
web.webapi.internalerror = web.debugerror

ui.urls = urls
ui.glob = globals()
