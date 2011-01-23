// Copyright (C) 2008 Victor Miura
// License: GNU GPL, version 3 or later; 
// http://www.gnu.org/copyleft/gpl.html
//var iankiVersion = 'iAnki (0.1b3)';
var versionTitle = iankiVersion + ' ';
var autoKill = 0;
var autoSync = 0;
var iAnki;
var iAnkiDebug = false;

// Remove additional spaces and replaces newlines and tabs.
function condenseSpaces(text) {
  var l = text.length;
  var i = 0;
  var r = '';
  last_ch = '';
  while (i < l) {
    ch = text[i];
    if (ch == '\n' || ch == '\t') { ch = ' '; }
    if (ch != ' ' || last_ch != ' ') {
      r += ch;
    }
    last_ch = ch;
    ++i;
  }
  return r;
}

// Removes extra line breaks.
function stripEmptyLines(text) {
  var out = text;
  var last = '';
  while (last != out) {
    last = out;
    out = out.replace('<br><br>', '<br>');
  }
  return out;
}

function stripTag(text, tag) {
  var out = text;
  var last = '';
  while(last != out) {
    last = out;
    var i = out.indexOf('<' + tag);
    if (i >= 0) {
      var front = out.substr(0, i);
      var rest = out.substr(i+1);
      var back = rest.substr(rest.indexOf('>')+1);
      out = front + back;
    }
  }
  return out;
}

// Format questions and answers text.
function formatQA(text) {
  var out = text;

  // Images are not supported on the phone: remove img tags.
  out = stripTag(out, 'img');
  // Remove extra spaces and newlines.
  //out = condenseSpaces(out);
  // Remove empty lines.
  //out = stripEmptyLines(out);

  return out;
}

function anki_log(str){
    if(iAnkiDebug){
        try {
            ourDate = new Date();
            var node = new Element('div', {
                //'html': ourDate.toLocaleString() + ': ' + str
                'html': str
            });
            node.inject($('ankilog'), 'top');
        }
        catch(e) {
            alert('Exception in anki_log:' + e + '. ' + str);
        }
    }
}

function anki_exception(str){
    try {
        ourDate = new Date();
        var node = new Element('div', {
            //'html': ourDate.toLocaleString() + ': ' + str
            'html': str
        });
        node.inject($('ankilog'), 'top');
    }
    catch(e) {
        alert('Exception in anki_exception:' + e + '. ' + str);
    }
}

function clear_log() {
    $('ankilog').innerHTML = '';
}

function cloneObject(what) {
    for (i in what) {
        this[i] = what[i];
    }
}

function nowInSeconds(){
	var t = new Date();
	return t.getTime() / 1000.0;
}

String.leftPad = function (val, size, ch) {
    var result = new String(val);
    if (ch == null) {
        ch = " ";
    }
    while (result.length < size) {
        result = ch + result;
    }
    return result;
}

function today(date){
	return date.getFullYear() + '-' + String.leftPad(date.getMonth()+1, 2, '0') + '-' + String.leftPad(date.getDate(), 2, '0');
}

function timeString(period) {
    if(period < 60)
        return '' + Math.floor(period) + ' seconds';
    else if(period < 60*60)
        return '' + Math.floor(period/60) + ' minutes';
    else if(period < 24*60*60)
        return '' + Math.floor(period/(60*60)) + ' hours';
    else
        return '' + Math.floor(period/(24*60*60)) + ' days';
}

function getRandomArbitary(min, max)
{
  return Math.random() * (max - min) + min;
}

function dbOpen(name, version, desc, size){   
    var db = window.openDatabase(name, version, desc, size);
    //var db = window.openDatabase(name, version, desc);
    if (!db)
        alert("Failed to open the database on disk.  This is probably because the version was bad or there is not enough space left in this domain's quota");
    else
	    anki_log("Opened database: " + name);
    return db;
}

function dbTransaction(db, callback1, callback2, callback3){
	db.transaction(
		function(tx){
			try {
				if(callback1)
					callback1(tx);
			}
			catch(e){
				anki_exception('dbTransaction callback1 exception - ' + e);
			}
		},
		function(error){
			try {
				anki_exception("Transaction error - " + error.message);
				if(callback2)
					callback2(error);
			}
			catch(e){
				anki_exception('dbTransaction callback2 exception - ' + e);
			}
		},
		function(){
			try {
				if(callback3)
					callback3();
			}
			catch(e){
				anki_exception('dbTransaction callback3 exception - ' + e);
			}
		}
	);
}

function dbSql(tx, sql, args, callback1, callback2){
	try {
        //anki_log("SQL:"+sql+"<BR>ARG:"+args);
        
		tx.executeSql(sql, args,
			function(tx, result){
				try {
					if(callback1)
						callback1(tx, result);
				}
				catch(e){
					anki_exception('dbSql callback1 exception - ' + e);
				}
			},
			function(tx, error){
				try {
					anki_exception("dbSql error - " + sql + "<br> -> " + error.message + "<br> -> " + args);
					if(callback2)
						callback2(tx, error);
				}
				catch(e){
					anki_exception('dbSql callback2 exception - ' + e);
				}
			}
	);
	}
	catch(e){
		anki_exception('dbSql exception - ' + e);
	}
}

function dbSqlQ(tx, sql, args){
	try {
		var self = this;
		self._ready = false;
		self._success = false;
		self._result = undefined;
		self._error = undefined;
		dbSql(tx,sql, args,
			function(tx, result){
				self._result = result;
				self._success = true;
				self._ready = true;
			},
			function(tx, error){
				self._error = error;
				self._ready = true;
			}
		);
	}
	catch(e){
		anki_exception('dbSqlObj exception - ' + e);
	}
}

dbSqlQ.prototype.ready = function(){
	return this._ready;
}
dbSqlQ.prototype.success = function(){
	if(!this._ready)
		throw "dbSqlQ.getSuccess exception: Not ready.";
	return this._success;
}
dbSqlQ.prototype.result = function(){
	if(!this._ready)
		throw "dbSqlQ.getResult exception: Not ready.";
	return this._result;
}
dbSqlQ.prototype.error = function(){
	if(!this._ready)
		throw "dbSqlQ.getError exception: Not ready.";
	return this._error;
}

var STATS_LIFE = 0;
var STATS_DAY = 1;

var PRIORITY_HIGH = 4;
var PRIORITY_MED = 3;
var PRIORITY_NORM = 2;
var PRIORITY_LOW = 1;
var PRIORITY_NONE = 0;
var MATURE_THRESHOLD = 21;
// need interval > 0 to ensure relative delay is ordered properly
var NEW_INTERVAL = 0.001;
var NEW_CARDS_LAST = 1;
var NEW_CARDS_DISTRIBUTE = 0;

function Deck(syncName, isNewDeck)
{
    this.syncName = syncName
	this.currCard = null;
	
	this.tables = ['decks', 'models', 'cards', 'facts']; // 'reviewHistory' 'stats'
	
    this.factorFour = 1.3;
    this.initialFactor = 2.5;
    this.maxScheduleTime = 1825;
    
	// initial intervals
	this.hardIntervalMin=0.333;
	this.hardIntervalMax=0.5;
	this.midIntervalMin=3.0;
	this.midIntervalMax=5.0;
	this.easyIntervalMin=7.0;
	this.easyIntervalMax=9.0;
	// delays on failure
	this.delay0 = 600;
	this.delay1 = 600;
	this.delay2 = 0;
	// collapsing future cards
	this.collapseTime = 1;
	// 0 is random, 1 is by input date
	this.newCardOrder = 0;
	// when to show new cards
	this.newCardSpacing = NEW_CARDS_DISTRIBUTE;
	this.revCardOrder = 0;
    
    this.initialize(isNewDeck);
}

Deck.prototype.markExpiredCardsDue = function() {
	var self = this;
	dbTransaction(self.db,
		function(tx){
			var now = new Date();
			dbSql(tx,'	update cards \
							set isDue = 1, relativeDelay = interval / (strftime("%s", "now") - due + 1) \
							where isDue = 0 and priority in (1,2,3,4) and combinedDue < ?',
							[now.getTime() / 1000.0],
			   function(tx, result) {
			   	anki_log('Trace markExpiredCardsDue done at time ' + now.getTime() / 1000.0);
	        }, function(tx, error) {
	            anki_exception('Failed to markExpiredCardsDue - ' + error.message);
	        });
		}
	);
}

Deck.prototype.getCounts = function(resCallback){
	var self = this;
	var failedCount;
	var reviewCount;
	var newCount;
	
	//self.markExpiredCardsDue();
    
	dbTransaction(self.db,
		function(tx) {
			tx.executeSql('select count(id) from "failedCards"', [],
			   function(tx, result) {
				//anki_log('Trace failedCount: ' + result.rows.item(0)['count(id)']);
                failedCount = result.rows.item(0)['count(id)'];
	        }, function(tx, error) {
	            anki_exception('failedCount query failed - ' + error.message);
	        });
			
			tx.executeSql('select count(isDue) from cards where isDue = 1 and type = 1', [],
			   function(tx, result) {
				//anki_log('Trace reviewCount: ' + result.rows.item(0)['count(isDue)']);
                reviewCount = result.rows.item(0)['count(isDue)'];
	        }, function(tx, error) {
	            anki_exception('reviewCount query failed - ' + error.message);
	        });
			
			tx.executeSql('select count(isDue) from cards where isDue = 1 and type = 2', [],
			   function(tx, result) {
				//anki_log('Trace newCount: ' + result.rows.item(0)['count(isDue)']);
                newCount = result.rows.item(0)['count(isDue)'];
	        }, function(tx, error) {
	            anki_exception('newCount query failed - ' + error.message);
	        });
		},
		function(error) {
			anki_exception('getCounts failed - ' + error.message);
			resCallback(failedCount, reviewCount, newCount);
		},
		function(tx) {
			resCallback(failedCount, reviewCount, newCount);
		}
	);
}

// Card predicates
////////////////////////////////////////////////////////////////////////////

Deck.prototype.cardState = function (card){
    if(this.cardIsNew(card))
        return "new";
    else if(card.interval > MATURE_THRESHOLD)
        return "mature";
    return "young";
}

Deck.prototype.cardIsNew = function (card){
	return card.reps == 0;
}

Deck.prototype.cardIsBeingLearnt = function(card){
	// "True if card should use present intervals."
	return card.interval < this.easyIntervalMin;
}

Deck.prototype.cardIsYoung = function(card){
	//"True if card is not new and not mature."
    return (!this.cardIsNew(card) &&
            !this.cardIsMature(card));
}

Deck.prototype.cardIsMature = function(card){
	return card.interval >= MATURE_THRESHOLD;
}

// Card selectors
////////////////////////////////////////////////////////////////////////////

Deck.prototype.getNewCard = function(tx, resCallback){
	var self = this;
    var query;
    if(self.newCardOrder == 0)
        query = 'select * from "acqCardsRandom" limit 1';
    else
        query = 'select * from "acqCardsOrdered" limit 1';
	dbSql(tx, query, [],
		function(tx, result) {
			if (result.rows.length > 0) {
				var card = result.rows.item(0);
				anki_log('Trace getNewCard: ' + card['id'] + ', ' + card['question']);
				resCallback(new cloneObject(card));
			}
			else {
				resCallback(null);
			}
        }, function(tx, error) {
            anki_exception('getNewCard query failed - ' + error.message);
			resCallback(null);
        }
	);
}

Deck.prototype.getDueCardNow = function(tx, resCallback){
	var self = this;
	
	var revQuery;
	if(self.revCardOrder == 0)
	    revQuery = 'select * from "revCardsOld" limit 1';
	else if(self.revCardOrder == 1)
	    revQuery = 'select * from "revCardsNew" limit 1';
	else if(self.revCardOrder == 2)
	    revQuery = 'select * from "revCardsDue" limit 1';
	else
	    revQuery = 'select * from "revCardsRandom" limit 1';
	    
	dbSql(tx,revQuery, [],
		function(tx, result) {
			if (result.rows.length > 0) {
				var card = result.rows.item(0);
				anki_log('Trace getDueCardNow: ' + card['id'] + ', ' + card['question']);
				resCallback(new cloneObject(card));
			}
			else {
				self.getNewCard(tx, resCallback);
			}
        }, function(tx, error) {
            anki_exception('getDueCardNow query failed - ' + error.message);
			resCallback(null);
        }
	);
}

Deck.prototype.getFailedCardNow = function(tx, resCallback){
	var self = this;
	dbSql(tx,'select * from "failedCardsNow" limit 1', [],
		function(tx, result) {
			if (result.rows.length > 0) {
				var card = result.rows.item(0);
				anki_log('Trace getFailedCardNow: ' + card['id'] + ', ' + card['question']);
				resCallback(new cloneObject(card));
			}
			else {
				self.getDueCardNow(tx, resCallback);
			}
        }, function(tx, error) {
            anki_exception('getFailedCardNow query failed - ' + error.message);
			resCallback(null);
        }
	);
}

Deck.prototype.getNextCardNew = function(resCallback){
    var self = this;
    var failedNowQ;
    var revNowQ;
    var newNowQ;
    
    anki_log('Deck.getNextCardNew');
    
    dbTransaction(self.db,
		function(tx)
		{
            // First start queries for failed, due and new cards.
            failedNowQ = new dbSqlQ(tx,'select * from "failedCardsNow"', [] );
            
            var revQuery;
            if(self.revCardOrder == 0)
                revQuery = 'select * from "revCardsOld" limit 1';
            else if(self.revCardOrder == 1)
                revQuery = 'select * from "revCardsNew" limit 1';
            else if(self.revCardOrder == 2)
                revQuery = 'select * from "revCardsDue" limit 1';
            else
                revQuery = 'select * from "revCardsRandom" limit 1';
                
            revNowQ = new dbSqlQ(tx, revQuery, [] );
            
            var newQuery;
            if(self.newCardOrder == 0)
                newQuery = 'select * from "acqCardsRandom" limit 1';
            else
                newQuery = 'select * from "acqCardsOrdered" limit 1';
                
            newNowQ = new dbSqlQ(tx, newQuery, [] );
        }
    );
    
    dbTransaction(self.db,
		function(tx)
		{
            // At this point the above queries are finished so they
            // can be read, and the following (mostly) implements
            // Anki's Deck.getCardId algorithm.
            
            // # failed card due?
            // if self.delay0 and self.failedNowCount:
            if(self.delay0 > 0 && failedNowQ.result().rows.length > 0) {
                resCallback(new cloneObject(failedNowQ.result().rows.item(0)));
                return;
            }
            
            // # failed card queue too big?   
            // if (self.failedCardMax and self.failedSoonCount >= self.failedCardMax):
            // Optimize this using a count query 'select count(id) from "failedCards"'
            if(self.failedCardMax > 0 && failedNowQ.result().rows.length >= self.failedCardMax) {
                resCallback(new cloneObject(failedNowQ.result().rows.item(0)));
                return;
            }
            
            // # distribute new cards? (ToDo)
            
            // # card due for review?
            if(revNowQ.result().rows.length > 0) {
                resCallback(new cloneObject(revNowQ.result().rows.item(0)));
                return;
            }
            
            // # new cards left?
            if(newNowQ.result().rows.length > 0) {
                resCallback(new cloneObject(newNowQ.result().rows.item(0)));
                return;
            }
            
            // # display failed cards early/last
            // if self.collapseTime or not self.delay0:
            if((self.collapseTime || self.delay0 == 0) && failedNowQ.result().rows.length > 0) {
                resCallback(new cloneObject(failedNowQ.result().rows.item(0)));
                return;
            }
            
            // No cards to review.
            resCallback(null);
        }
    );
}

Deck.prototype.getNextCard = function(resCallback){
	var self = this;
	self.markExpiredCardsDue();
    var failedCount;
	var reviewCount;
	var newCount;
    
    self.getCounts(
        function(a, b, c) {
            failedCount = a;
            reviewCount = b;
            newCount = c;
        }
    );
    
    function cardCallback(card) {
        function under(x, b){
            if(b)
                return '<u>'+x+'</u>';
            else
                return x;
        }
        if(card) {
            iAnki.setTitle(versionTitle + '<br>'+self.syncName +' '+under(failedCount, card.type==0)+' '+under(reviewCount, card.type==1)+' '+under(newCount, card.type==2));
        }
        resCallback(card);
    }
    
    self.getNextCardNew(cardCallback);
    
    /*
	dbTransaction(self.db,
		function(tx)
		{
			try {
				self.getFailedCardNow(  tx,
                    function(card) {
                        function under(x, b){
                            if(b)
                                return '<u>'+x+'</u>';
                            else
                                return x;
                        }
                        if(card) {
                            iAnki.setTitle(versionTitle + '<br>'+self.syncName +' '+under(failedCount, card.type==0)+' '+under(reviewCount, card.type==1)+' '+under(newCount, card.type==2));
                        }
                        resCallback(card);
                    }
                );
			}
			catch(e){
				anki_exception('getFailedCardNow Exception:' + e);
			}
		}
	);
    */
}

Deck.prototype.nextDue = function(card, ease, oldState){
	// Return time when CARD will expire given EASE.
	var due = 0;
	if (ease == 0) {
		due = this.delay0;
	}
	else if (ease == 1) {
        if(oldState == 'mature')
            due = this.delay1;
        else
            due = this.delay0;
	}
	else {
		due = card.interval * 86400.0;
	}
    return due + nowInSeconds();
}

Deck.prototype._adjustedDelay = function(card) {
    if(this.cardIsNew(card))
        return 0;
    
    return Math.max(0, (nowInSeconds() - card.due) / 86400.0);
}

Deck.prototype.nextInterval = function(card, ease){
	// "Return the next interval for CARD given EASE."
	var self = this;
    
	var delay = self._adjustedDelay(card, ease);
	var interval = card.interval;

    if (ease == 0) {
        interval = 0;
    }
    else if (ease == 1) {
        interval *= self.delay2;
        if(interval < self.hardIntervalMin)
            interval = 0;
    }
    else if(interval == 0)
    {
        if(ease == 2)
            interval = getRandomArbitary(self.hardIntervalMin,
                                         self.hardIntervalMax);
        else if(ease == 3)
            interval = getRandomArbitary(self.midIntervalMin,
                                         self.midIntervalMax);
        else if(ease == 4)
            interval = getRandomArbitary(self.easyIntervalMin,
                                         self.easyIntervalMax);
    }
    else {
        //anki_exception("ease " + ease + " factor " + card.factor + " interval " + interval + " himax " + self.hardIntervalMax + " delay " + delay);
        
        // if not cramming, boost initial 2
        if (interval < self.hardIntervalMax && interval > 0.166)
            interval = self.hardIntervalMax * 3.5;
        // multiply last interval by factor
        if (ease == 2)
			interval = (interval + delay / 4) * 1.2;
		else if (ease == 3)
			interval = (interval + delay / 2) * card.factor;
		else if (ease == 4)
			interval = (interval + delay) * card.factor * self.factorFour;
            
        var fuzz = getRandomArbitary(0.95, 1.05);
        interval *= fuzz;
    }
    
    if(self.maxScheduleTime) {
        interval = Math.min(interval, self.maxScheduleTime);
    }
    
    //anki_exception("final interval " + interval);
    return interval;
}
		
Deck.prototype.updateFactor = function(card, ease){
	// Update CARD's factor based on EASE.
	var self = this;
	card.lastFactor = card.factor;
    if(!card.reps)
        card.factor = self.averageFactor; // card is new, inherit beginning factor
    if(self.cardIsBeingLearnt(card) && ease in [0, 1, 2])
        if(card.successive && ease != 2) // only penalize failures after success when starting
            card.factor -= 0.20;
    else if(ease in [0, 1])
        card.factor -= 0.20;
    else if(ease == 2)
        card.factor -= 0.15;
    else if(ease == 4)
        card.factor += 0.10;
    card.factor = Math.max(1.3, card.factor);
	return;
}

Deck.prototype.showAnswer = function(){
    try{
        // this.thinkingTime = Math.min(Math.max(nowInSeconds() - this.currCard.startTime, 0.0), 60.0);
        anki_log('Deck.showAnswer')
        $('showAnswerDiv').style.display='none';
        $('answerSide').style.display='block';
        $('answerButtons').style.display='block';
    }
    catch(e){
		anki_exception('Deck.showAnswer Exception:' + e);
	}
}

Deck.prototype.markCard = function(){
	var self = this;
	try {
    }
    catch(e) {
        anki_exception('Deck.answerCard Exception:' + e);
    }
}

Deck.prototype.answerCard = function(ease){
	var self = this;
	try {
        clear_log();
		anki_log('Clicked answer ' + ease + '.');
		$('answerSide').style.display='none';
		        
        var answerTime = nowInSeconds();
		var card = new cloneObject(self.currCard);
        
        this.thinkingTime = Math.min(Math.max(nowInSeconds() - this.currCard.startTime, 0.0), 60.0);
		
		arg = [ card.modified,
                card.firstAnswered,
                card.lastInterval,
                card.interval,
                card.lastDue,
                card.spaceUntil,
                card.due,
                card.combinedDue,
                card.isDue,
                card.lastFactor,
                card.factor,
                card.reps,
                card.successive,
                card.reviewTime,
                card.averageTime,
                card.youngEase0,
                card.youngEase1,
                card.youngEase2,
                card.youngEase3,
                card.youngEase4,
                card.matureEase0,
                card.matureEase1,
                card.matureEase2,
                card.matureEase3,
                card.matureEase4,
                card.yesCount,
                card.noCount,
                card.id ];
		anki_log('Before ' + arg);
				
		var oldState = this.cardState(card);

		
		var lastDelay = (answerTime - card.due) / 86400.0;
		if(lastDelay < 0) lastDelay = 0;
		
		//anki_exception('Thinking time ' + this.thinkingTime);
		
		card.thinkingTime = this.thinkingTime;
		card.lastInterval = card.interval;
	    card.interval = this.nextInterval(card, ease);
	    card.lastDue = card.due;
	    card.due = self.nextDue(card, ease, oldState);
	    card.isDue = 0;
	    card.lastFactor = card.factor;
	    self.updateFactor(card, ease);
	    card.spaceUntil = 0
		card.combinedDue = card.due;
			
		// spacing - first, we get the times of all other cards with the same fact	
		var spacingQ;
		var minIntervalQ;
		
		dbTransaction(self.db,
			function(tx){
				spacingQ = new dbSqlQ(tx,'select models.initialSpacing as initialSpacing, models.spacing as spacing from \
										facts, models where facts.modelId = models.id and facts.id = ?', [card.factId]
										);
				minIntervalQ = new dbSqlQ(tx,'select min(interval) as minInterval from cards \
											where factId = ? and id != ?', [card.factId, card.id]
											);
			}
		);
		dbTransaction(self.db,
			function(tx){
				// This bit must run in a new transaction as it depends on the previous queries to have finished.
                if(spacingQ.result().rows.length > 0) {                    
                    minSpacing = spacingQ.result().rows.item(0)['initialSpacing'];
                    spaceFactor = spacingQ.result().rows.item(0)['spacing'];
                }
                else {
                    minSpacing = 0;
                    spaceFactor = 0;
                }
				
				if (minIntervalQ.result().rows.length > 0)
					minOfOtherCards = minIntervalQ.result().rows.item(0)['minInterval'];
				else
					minOfOtherCards = 0;
				
				var space;
				if(minOfOtherCards)
		            space = Math.min(minOfOtherCards, card.interval);
		        else
		            space = 0;
		        space = space * spaceFactor * 86400.0;
		        space = Math.max(minSpacing, space);
		        space += answerTime;
				
				dbSql(tx,'update cards set \
							spaceUntil = ?, \
							combinedDue = max(?, due), \
							modified = ?, \
							isDue = 0 \
							where factId = ? and id != ?',
							[space, space, answerTime, card.factId, card.id]
							);
			}
		);
	
		// card stats
		dbTransaction(self.db,
			function(tx){
				function updateStats(card, ease, state)
				{
					card.reps += 1;
			        if(ease > 1)
			            card.successive += 1;
			        else
			            card.successive = 0;
			        delay = card.thinkingTime;
			        // ignore any times over 60 seconds
			        if(delay < 60)
			            card.reviewTime += delay;
			            if(card.averageTime)
			                card.averageTime = (card.averageTime + delay) / 2.0;
			            else
			                card.averageTime = delay;
			        // we don't track first answer for cards
			        if(state == "new")
			            state = "young";
			        // update ease and yes/no count
			        var attr = state + "Ease" + ease;
					card[attr] += 1;
			        if(ease < 2)
			            card.noCount += 1;
			        else
			            card.yesCount += 1;
			        if(!card.firstAnswered)
			            card.firstAnswered = answerTime;
			        card.modified = answerTime;
				}
				
				updateStats(card, ease, oldState);
            
                // Update card type
                if(card.reps == 0)
                    card.type = 2;
                else if(card.successive)
                    card.type = 1;
                else
                    card.type = 0;
				
				arg = [card.modified,
								 card.firstAnswered,
								 card.lastInterval,
								 card.interval,
								 card.lastDue,
								 card.spaceUntil,
								 card.due,
								 card.combinedDue,
								 card.isDue,
								 card.lastFactor,
								 card.factor,
								 card.reps,
								 card.successive,
								 card.reviewTime,
								 card.averageTime,
								 card.youngEase0,
								 card.youngEase1,
								 card.youngEase2,
								 card.youngEase3,
								 card.youngEase4,
								 card.matureEase0,
								 card.matureEase1,
								 card.matureEase2,
								 card.matureEase3,
								 card.matureEase4,
								 card.yesCount,
								 card.noCount,
                                 card.type,
								 card.id];
				anki_log('After ' + arg);
				dbSql(tx,'	update cards \
								set modified = ?, \
									firstAnswered = ?, \
									lastInterval = ?, \
									interval = ?, \
									lastDue = ?, \
									spaceUntil = ?, \
									due = ?, \
									combinedDue = ?, \
									isDue = ?, \
									lastFactor = ?, \
									factor = ?, \
									reps = ?, \
									successive = ?, \
									reviewTime = ?, \
									averageTime = ?, \
									youngEase0 = ?, \
									youngEase1 = ?, \
									youngEase2 = ?, \
									youngEase3 = ?, \
									youngEase4 = ?, \
									matureEase0 = ?, \
									matureEase1 = ?, \
									matureEase2 = ?, \
									matureEase3 = ?, \
									matureEase4 = ?, \
									yesCount = ?, \
									noCount = ?, \
                                    type = ? \
								where id = ?',
								arg
				,  function(tx, result) {
				   	anki_log('Updated card ' + card.id);
		        }, function(tx, error) {
		            anki_log('Failed to update card - ' + error.message);
		        });
			}
		);
		
        
        /*
        // Although the stats code below was working, I've disabled it as we don't need to maintain
        // these stats on the client currently.
        
        // global/daily stats
		var globalStatsQ;
		var dailyStatsQ;
		var day = today(new Date());
		
		function createStats(tx, type, day){
			dbSql(tx,'insert into stats \
					(type, day, reps, averageTime, reviewTime, distractedTime, distractedReps, \
					newEase0, newEase1, newEase2, newEase3, newEase4, youngEase0, youngEase1, \
					youngEase2, youngEase3, youngEase4, matureEase0, matureEase1, matureEase2, \
					matureEase3, matureEase4) values (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, \
					0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)',
					[type, day]
			);
		}
		function getGlobalStatsQ(tx){
			return new dbSqlQ(tx,'SELECT * FROM stats \
								where type=? \
								', [STATS_LIFE]
								);
		}
		function getDailyStatsQ(tx, day){
			return new dbSqlQ(tx,'SELECT * FROM stats \
							where day=? and type=? \
							', [day, STATS_DAY]
							);
		}

		dbTransaction(self.db,
			function(tx){
				// Start reading getting stats from db
				globalStatsQ = getGlobalStatsQ(tx);
				dailyStatsQ = getDailyStatsQ(tx, day);
			}
		);
		dbTransaction(self.db,
			function(tx){
				// If stats weren't found, create them
				if (globalStatsQ.result().rows.length == 0) {
					anki_log('Creating new global stats');
					createStats(tx, STATS_LIFE, day);
					globalStatsQ = getGlobalStatsQ(tx);
				}
				if (dailyStatsQ.result().rows.length == 0) {
					anki_log('Creating new stats for today');
					createStats(tx, STATS_DAY, day);
					dailyStatsQ = getDailyStatsQ(tx, day);
				}
			}
		);
		
		function updateStats(tx, stats, card, ease, oldState){
			arg = [stats.type,
					 stats.day,
					 stats.reps,
					 stats.averageTime,
					 stats.reviewTime,
					 stats.newEase0,
					 stats.newEase1,
					 stats.newEase2,
					 stats.newEase3,
					 stats.newEase4,
					 stats.youngEase0,
					 stats.youngEase1,
					 stats.youngEase2,
					 stats.youngEase3,
					 stats.youngEase4,
					 stats.matureEase0,
					 stats.matureEase1,
					 stats.matureEase2,
					 stats.matureEase3,
					 stats.matureEase4,
					 stats.id];
			anki_log('Stats Before' + arg);
					 
			stats.reps += 1;
			delay = card.thinkingTime;
			if (delay >= 60) {
				// make a guess as to the time spent answering
				stats.reviewTime += stats.averageTime;
			}
			else {
				stats.reviewTime += delay;
				stats.averageTime = (stats.reviewTime / (1.0 * stats.reps));
			}
			// update eases
			stats[oldState+'Ease'+ease] += 1;
			
			arg = [stats.type,
					 stats.day,
					 stats.reps,
					 stats.averageTime,
					 stats.reviewTime,
					 stats.newEase0,
					 stats.newEase1,
					 stats.newEase2,
					 stats.newEase3,
					 stats.newEase4,
					 stats.youngEase0,
					 stats.youngEase1,
					 stats.youngEase2,
					 stats.youngEase3,
					 stats.youngEase4,
					 stats.matureEase0,
					 stats.matureEase1,
					 stats.matureEase2,
					 stats.matureEase3,
					 stats.matureEase4,
					 stats.id];
			anki_log('Stats After' + arg);
			dbSql(tx,'update stats set \
					type=?, \
					day=?, \
					reps=?, \
					averageTime=?, \
					reviewTime=?, \
					newEase0=?, \
					newEase1=?, \
					newEase2=?, \
					newEase3=?, \
					newEase4=?, \
					youngEase0=?, \
					youngEase1=?, \
					youngEase2=?, \
					youngEase3=?, \
					youngEase4=?, \
					matureEase0=?, \
					matureEase1=?, \
					matureEase2=?, \
					matureEase3=?, \
					matureEase4=? \
					where id = ?',
					arg
			);
		}
		
		dbTransaction(self.db,
			function(tx){
				// By this point the stats should be ready for processing
				globalStats = new cloneObject(globalStatsQ.result().rows.item(0));	// Copy, since the query result is read only
				dailyStats = new cloneObject(dailyStatsQ.result().rows.item(0));	// Copy, since the query result is read only
				updateStats(tx, globalStats, card, ease, oldState);
				updateStats(tx, dailyStats, card, ease, oldState);
			}
		);
        */
				
		dbTransaction(self.db,
			function(tx){
                // Write card history
                var hist = [card.id, card.lastInterval, card.nextInterval, ease, lastDelay, 
							 card.lastFactor, card.factor, card.reps, card.thinkingTime, card.yesCount, card.noCount,
							 answerTime];
                
				dbSql(tx,	'insert into reviewHistory \
							(cardId, lastInterval, nextInterval, ease, delay, \
                            lastFactor, nextFactor, reps, thinkingTime, yesCount, noCount, \
                            time) \
							values ( \
							?, ?, ?, ?, ?, \
							?, ?, ?, ?, ?, ?, \
							?)',
							hist
							);
                
                // Update modified time on this deck
				dbSql(tx,	'update decks \
							set modified = ?',[answerTime]);
                
                // Update lastCardInfo
                                var q = card.question;
                q = stripTag(q, 'img');
                q = stripTag(q, 'div');
                q = stripTag(q, 'span');
                
                if(ease < 2 && self.delay0 == 0) {
                    $('lastCardInfo').innerHTML = ' <br>'+q+'<br>Will be shown again at the end.';
                }
                else {
                    var dueIn = card.due - answerTime;
                    var next = timeString(dueIn);
                    $('lastCardInfo').innerHTML = ' <br>'+q+'<br>Will be shown again in '+next+'.';
                }
                
                
				// Finally after all the previous transactions are finished, show the next card.
				self.nextCard();
			}
		);

	}
	catch(e){
		anki_exception('Deck.answerCard Exception:' + e);
	}
}

Deck.prototype.nextCard = function() {
    anki_log('Deck.nextCard');
	var self = this;
    anki_log('What the?');
	//$(content).innerHTML = '';
	//iAnki.currMode.style.display='none';
	
	this.getNextCard(
		function(card){
            if(card != null){
                self.currCard = new cloneObject(card);
                $('question').innerHTML = formatQA(( self.currCard.question ));
                $('answer').innerHTML = formatQA(( self.currCard.answer ));
                $('showAnswerDiv').style.display = 'block';
                $('answerSide').style.display = 'none';
                $('answerButtons').style.display = 'none';

                self.currCard.startTime = nowInSeconds();
                
                //iAnki.setTitle(versionTitle + self.syncName);
                iAnki.setMode($('reviewMode'));
			}
			else {
                self.currCard = null;
             
                var nextReviewQ;   
                dbTransaction(self.db,
                    function(tx){
                        nextReviewQ = new dbSqlQ(tx,'SELECT min(combinedDue) FROM cards WHERE priority != 0', []);
                    }
                );
                
                dbTransaction(self.db,
                    function(tx){
                        iAnki.setTitle(versionTitle+'Welcome');
                        if(nextReviewQ.result().rows.length > 0) {
                            var dueIn = Math.max(0, nextReviewQ.result().rows.item(0)['min(combinedDue)'] - nowInSeconds());
                            if(dueIn > 0)
                                iAnki.setInfo('No reviews to do at this time.<br>The next review will be in ' + timeString(dueIn) + '.');
                            else
                                iAnki.setInfo('No reviews to do at this time.');
                        }
                        else {
                            iAnki.setInfo('There are no cards to review.');
                        }
                        iAnki.setMode($('infoMode'));
                    }
                );
			}
		}
	);
}

Deck.prototype.loadDeck = function() {
    anki_log("Deck.loadDeck");
    var self = this;
    var deckQ, extraQ;
    var averageFactorQ;
    dbTransaction(self.db,
        function(tx) {
            deckQ = new dbSqlQ(tx, 'SELECT * FROM decks LIMIT 1');
            averageFactorQ = new dbSqlQ(tx, 'select avg(factor) from cards where reps > 0');
            extraQ = new dbSqlQ(tx, 'SELECT * FROM extra LIMIT 1');
        }
    );
    
    dbTransaction(self.db,
        function(tx) {
            // Update deck
            if(deckQ.result().rows.length > 0) {
                var deck = deckQ.result().rows.item(0);
                // initial intervals
                self.hardIntervalMin=deck.hardIntervalMin;
                self.hardIntervalMax=deck.hardIntervalMax;
                self.midIntervalMin=deck.midIntervalMin;
                self.midIntervalMax=deck.midIntervalMax;
                self.easyIntervalMin=deck.easyIntervalMin;
                self.easyIntervalMax=deck.easyIntervalMax;
                // delays on failure
                self.delay0 = deck.delay0;
                self.delay1 = deck.delay1;
                self.delay2 = deck.delay2;
                
                self.failedCardMax = deck.failedCardMax;
				
                if(self.version < 15){
                    self.delay1 = deck.delay0;
                    self.delay2 = 0.0;
                }
                
                anki_log("delay0 " + self.delay0);
                anki_log("delay1 " + self.delay1);
                anki_log("delay2 " + self.delay2);
				
                // collapsing future cards
                self.collapseTime = deck.collapseTime;
                // 0 is random, 1 is by input date
                self.newCardOrder = deck.newCardOrder;
                self.revCardOrder = deck.revCardOrder;
                // when to show new cards
                self.newCardSpacing = deck.newCardSpacing;
            }
            if(averageFactorQ.result().rows.length > 0)
                self.averageFactor = averageFactorQ.result().rows.item(0)['avg(factor)'];
            else
                self.averageFactor = self.initialFactor;
                
            if(extraQ.result().rows.length > 0) {
                var extra = extraQ.result().rows.item(0);
                var css = document.createElement('link'); 
                css.rel = 'stylesheet';
                css.type = 'text/css';
                css.href = "data:text/css;charset=utf-8," + escape(extra.css);
                document.head.appendChild(css);
            }
        }
    );
}

var realSyncJson;

Deck.prototype.realSync = function(resCallback){
    try {
        var self = this;
        anki_log("Deck.realSync " + self.syncName);
        iAnki.setInfo('Syncing ' + self.syncName + '...');
        iAnki.setMode($('infoMode'));
        var sendData = {};
                
        // Get deck settings
        var settingsQ;
        dbTransaction(self.db,
            function(tx) {
                settingsQ = new dbSqlQ(tx, 'SELECT * FROM syncTimes',[]);
            }
        );
        
        var reviewsSynched = 0;
        var counts = {};
        self.tables.each( function(table) {
            counts[table] = [0,0,0];
        });
        
        function finished() {
            var info = 'Sync Finished\n';
            if(reviewsSynched > 0)
                info += '' + reviewsSynched + ' reviews synched\n';
            self.tables.each( function(table) {
                // This removal message is a bit confusing, because cards are removed simply for not being due soon.
                ///if(counts[table][0] > 0)
                //    info += '' + counts[table][0] + ' ' + table + ' removed.\n';
                if(counts[table][1] > 0)
                    info += '' + counts[table][1] + ' ' + table + ' updated.\n';
                if(counts[table][2] > 0)
                    info += '' + counts[table][2] + ' ' + table + ' added.\n';
            });
            alert(info);
        }
        
        // Get new reviewHistory
        var lastSyncHost;
        var lastSyncClient;
        var modifiedQ;
        var haveCardsQ;
        var haveFactsQ;
        var haveModelsQ;
        dbTransaction(self.db,
            function(tx) {
                if(settingsQ.result().rows.length == 0){
                    // First time sync
                    anki_log(" First time sync.");
                    lastSyncHost = 0;
                    lastSyncClient = 0;
                    sendData['lastSyncHost'] = 0;
                    sendData['lastSyncClient'] = 0;
                    dbSql(tx, 'INSERT INTO syncTimes (lastSyncHost, lastSyncClient) VALUES (?,?)',[0, 0]);
                }
                else {
                    // Sync existing tables
                    lastSyncHost = settingsQ.result().rows.item(0).lastSyncHost;
                    lastSyncClient = settingsQ.result().rows.item(0).lastSyncClient;
                    anki_log(" Sync existing tables. " + lastSyncHost + " " + lastSyncClient);
                }
                
                sendData['lastSyncHost'] = lastSyncHost;
                sendData['lastSyncClient'] = lastSyncClient;
                
                // Get history modified since last client sync time
                modifiedQ = new dbSqlQ(tx, 'SELECT * FROM reviewHistory WHERE time > ?',[lastSyncClient]);
                haveCardsQ = new dbSqlQ(tx, 'SELECT id FROM cards',[]);
                haveFactsQ = new dbSqlQ(tx, 'SELECT id FROM facts',[]);
                haveModelsQ = new dbSqlQ(tx, 'SELECT id FROM models',[]);
            }
        );
        
        // Sync
        dbTransaction(self.db,
            function(tx) {
                var result = modifiedQ.result();
                anki_log(" reviewHistory changed " + result.rows.length);
                var diff = [];
                for(var i = 0; i < result.rows.length; i++){
                    diff[i] = result.rows.item(i);
                }
                reviewsSynched = result.rows.length;
                sendData['reviewHistory'] = diff;
                
                var cardIds = [];
                var factIds = [];
                var modelIds = [];
                var haveCards = haveCardsQ.result();
                for(var i = 0; i < haveCards.rows.length; i++)
                    cardIds[i] = haveCards.rows.item(i).id;
                var haveFacts = haveFactsQ.result();
                for(var i = 0; i < haveFacts.rows.length; i++)
                    factIds[i] = haveFacts.rows.item(i).id;
                var haveModels = haveModelsQ.result();
                for(var i = 0; i < haveModels.rows.length; i++)
                    modelIds[i] = haveModels.rows.item(i).id;
                
                function sync_realsync(result) {
                    try {
                        realSyncJson = result; // JSON.decode(result, true)
                        if(realSyncJson['error'] != 0) {
                            anki_exception("Error syncing deck in sync_realsync:" + realSyncJson['exception']);
                            resCallback();
                            return;
                        }
                                               
                        // Delete old reviewHistory
                        dbTransaction(self.db,
                            function(tx) {
                                dbSql(tx, 'DELETE FROM reviewHistory',[]);
                            }
                        );

                        var deckcss = realSyncJson['deckcss'];
                        anki_log('deckcss<br>'+deckcss);
                        
                        // Get deck settings
                        var extraQ;
                        dbTransaction(self.db,
                            function(tx) {
                                extraQ = new dbSqlQ(tx, 'SELECT * FROM extra',[]);
                            }
                        );
                        
                        dbTransaction(self.db,
                            function(tx) {
                                if(extraQ.result().rows.length == 0){
                                    dbSql(tx, 'INSERT INTO extra (css) VALUES (?)',[deckcss]);
                                }
                                else {
                                    dbSql(tx, 'UPDATE extra SET css=?',[deckcss]);
                                }
                            }
                        );
                        
                        var numUpdates = realSyncJson['numUpdates']
                        var updatesDone = 0;
                        
                        function requestNext() {
                            anki_log('requestNext ' + updatesDone + ' ' + numUpdates);
                            
                            function sync_nextsync(result) {
                                try {
                                    if(result['error'] != 0) {
                                        alert("Error syncing deck in sync_nextsync: " + result['exception']);
                                        resCallback();
                                        return;
                                    }
                                    applyNext(result['updates']);
                                }
                                catch(e){
                                    anki_exception('sync_nextsync exception:' + e);
                                }
                            }
                            
                            dbTransaction(self.db,
                                function(tx) {
                                    request_send(encodeURIComponent(JSON.encode({'method':'nextsync', 'syncName':'self.syncName'})), 'anki/sync.html', sync_nextsync);
                                }
                            );
                            /*
                            var requestUp = new Request.JSON({
                                url: '/anki/sync.html',
                                data: JSON.encode({'method':'nextsync', 'syncName':'self.syncName'}),
                                onSuccess: function(result){
                                    if(result['error'] != 0) {
                                        alert("Error syncing deck: " + result['exception']);
                                        resCallback();
                                        return;
                                    }
                                    
                                    applyNext(result['updates']);
                                }
                            }).POST();
                            */
                        }
                        
                        function applyNext(updates) {
                            dbTransaction(self.db,
                                function(tx) {
                                    updatesDone += updates['numUpdates'];
                                    if(updatesDone < numUpdates && updates['numUpdates'] != 0)
                                    {
                                        //requestNext();
                                    }
                                    
                                    self.tables.each(
                                        function(table) {
                                            // Apply updates
                                            anki_log(table + ' removed ' + updates[table]['removed'].length + ' modified ' + updates[table]['modified'].length + ' added ' + updates[table]['added'].length);
                                            
                                            // Removals
                                            updates[table]['removed'].each(
                                                function(row){
                                                    //anki_log('Remove id ' + row)
                                                    dbSql(tx, 'DELETE FROM '+table+' WHERE id=?', [row]);
                                                }
                                            );
                                            counts[table][0] += updates[table]['removed'].length;
                                            
                                            // Modifications
                                            {
                                                var sql = realSyncJson[table+'_sql_update'];
                                                updates[table]['modified'].each(
                                                    function(row){
                                                        //anki_log('Update id ' + row[0])
                                                        dbSql(tx, sql, row);
                                                    }
                                                );
                                                counts[table][1] += updates[table]['modified'].length;
                                            }
                                            
                                            // Additions
                                            {
                                                var sql = realSyncJson[table+'_sql_insert'];
                                                updates[table]['added'].each(
                                                    function(row){
                                                        //anki_log('Add id ' + row[0])
                                                        dbSql(tx, sql, row);
                                                    }
                                                );                                                   
                                                counts[table][2] += updates[table]['added'].length;
                                            }
                                        }
                                    );
                                },
                                function(error) {
                                    alert("Error syncing deck: " + error);
                                    resCallback();
                                },
                                function() {
                                    //updatesDone += updates['numUpdates'];
                                    iAnki.setTitle('Synched ' + updatesDone + '/' + numUpdates + ' items');
                                    
                                    if(updatesDone < numUpdates && updates['numUpdates'] != 0)
                                    {
                                        requestNext();
                                    }
                                    else
                                    {
                                        // Finished sync
                                        dbTransaction(self.db,
                                            function(tx) {
                                                dbSql(tx, 'UPDATE syncTimes SET lastSyncHost=?, lastSyncClient=?',[realSyncJson['lastSyncHost'], nowInSeconds()]);
                                            }
                                        );
                                        
                                        dbTransaction(self.db,
                                            function(tx) {
                                                finished();
                                                resCallback();
                                            }
                                        );
                                    }
                                }
                            );
                        }
                        
                        applyNext(realSyncJson['updates']);
                    }
                    catch (e) {
                        anki_exception('sync_realsync exception:' + e);
                    }
                }
                
                sendData['cardIds'] = cardIds;
                sendData['factIds'] = factIds;
                sendData['modelIds'] = modelIds;
                
                sendData['method'] = 'realsync';
                sendData['syncName'] = self.syncName;
                
                dbTransaction(self.db,
                    function(tx) {
                        request_send(encodeURIComponent(JSON.encode(sendData)), 'anki/sync.html', sync_realsync);
                    }
                );
                
                /*
                var request = new Request.JSON({
                    url: '/anki/sync.html',
                    data: JSON.encode(sendData),
                    onSuccess: function(json){
                        if(json['error'] != 0) {
                            anki_exception("Error syncing deck:" + json['exception']);
                            resCallback();
                            return;
                        }
                        
                        // Delete old reviewHistory
                        dbTransaction(self.db,
                            function(tx) {
                                dbSql(tx, 'DELETE FROM reviewHistory',[]);
                            }
                        );
                        
                        var numUpdates = json['numUpdates']
                        var updatesDone = 0;
                        
                        function requestNext() {
                            anki_log('requestNext ' + updatesDone + ' ' + numUpdates);
                            var requestUp = new Request.JSON({
                                url: '/anki/sync.html',
                                data: JSON.encode({'method':'nextsync', 'syncName':'self.syncName'}),
                                onSuccess: function(result){
                                    if(result['error'] != 0) {
                                        alert("Error syncing deck: " + result['exception']);
                                        resCallback();
                                        return;
                                    }
                                    
                                    applyNext(result['updates']);
                                }
                            }).POST();
                        }
                        
                        function applyNext(updates) {
                            dbTransaction(self.db,
                                function(tx) {
                                    updatesDone += updates['numUpdates'];
                                    if(updatesDone < numUpdates && updates['numUpdates'] != 0)
                                    {
                                        //requestNext();
                                    }
                                    
                                    self.tables.each(
                                        function(table) {
                                            // Apply updates
                                            anki_log(table + ' removed ' + updates[table]['removed'].length + ' modified ' + updates[table]['modified'].length + ' added ' + updates[table]['added'].length);
                                            
                                            // Removals
                                            updates[table]['removed'].each(
                                                function(row){
                                                    //anki_log('Remove id ' + row)
                                                    dbSql(tx, 'DELETE FROM '+table+' WHERE id=?', [row]);
                                                }
                                            );
                                            counts[table][0] += updates[table]['removed'].length;
                                            
                                            // Modifications
                                            {
                                                var sql = json[table+'_sql_update'];
                                                updates[table]['modified'].each(
                                                    function(row){
                                                        //anki_log('Update id ' + row[0])
                                                        dbSql(tx, sql, row);
                                                    }
                                                );
                                                counts[table][1] += updates[table]['modified'].length;
                                            }
                                            
                                            // Additions
                                            {
                                                var sql = json[table+'_sql_insert'];
                                                updates[table]['added'].each(
                                                    function(row){
                                                        //anki_log('Add id ' + row[0])
                                                        dbSql(tx, sql, row);
                                                    }
                                                );                                                   
                                                counts[table][2] += updates[table]['added'].length;
                                            }
                                        }
                                    );
                                },
                                function(error) {
                                    alert("Error syncing deck: " + error);
                                    resCallback();
                                },
                                function() {
                                    //updatesDone += updates['numUpdates'];
                                    iAnki.setTitle(versionTitle + 'Synched ' + updatesDone + '/' + numUpdates + ' items');
                                    
                                    if(updatesDone < numUpdates && updates['numUpdates'] != 0)
                                    {
                                        requestNext();
                                    }
                                    else
                                    {
                                        // Finished sync
                                        dbTransaction(self.db,
                                            function(tx) {
                                                dbSql(tx, 'UPDATE syncTimes SET lastSyncHost=?, lastSyncClient=?',[json['lastSyncHost'], nowInSeconds()]);
                                            }
                                        );
                                        
                                        dbTransaction(self.db,
                                            function(tx) {
                                                finished();
                                                self.loadDeck();
                                                resCallback();
                                                $('syncDeck').disabled = false;
                                            }
                                        );
                                    }
                                }
                            );
                        }
                        
                        applyNext(json['updates']);
                    },
                    onFailure: function(){
                        alert('Sync failed.');
                        $('syncDeck').disabled = false;
                    },
                    onException: function(){
                        alert('There was an error communicating with the server.');
                        $('syncDeck').disabled = false;
                    }
                }).POST();
                */
            }
        );
    }
    catch(e){
        anki_exception('Deck.realSync exception:' + e);
        $('syncDeck').disabled = false;
    }
}

Deck.prototype.eraseDeck = function(resCallback) {
    try {
        var self = this;
        //$('eraseDeck').disabled = true;
        anki_log("Erasing local deck.");
        
        iAnki.setInfo('Erasing deck...');
        iAnki.setMode($('infoMode'));
        
        dbTransaction(self.db,
            function(tx)
            {
                dbSql(tx,'DROP VIEW IF EXISTS acqCardsOrdered');
				dbSql(tx,'DROP VIEW IF EXISTS acqCardsRandom');
				dbSql(tx,'DROP VIEW IF EXISTS failedCardsNow');
				dbSql(tx,'DROP VIEW IF EXISTS failedCards');
				dbSql(tx,'DROP VIEW IF EXISTS failedCardsSoon');
				dbSql(tx,'DROP VIEW IF EXISTS revCards');
                dbSql(tx,'DROP INDEX IF EXISTS ix_cards_markExpired');
                dbSql(tx,'DROP INDEX IF EXISTS ix_cards_failedIsDue');
                dbSql(tx,'DROP INDEX IF EXISTS ix_cards_failedOrder');
                dbSql(tx,'DROP INDEX IF EXISTS ix_cards_revisionOrder');
                dbSql(tx,'DROP INDEX IF EXISTS ix_cards_newRandomOrder');
                dbSql(tx,'DROP INDEX IF EXISTS ix_cards_newOrderedOrder');
                dbSql(tx,'DROP INDEX IF EXISTS ix_cards_factId');
                
                dbSql(tx, 'DROP TABLE IF EXISTS syncTimes');
                dbSql(tx, 'DROP TABLE IF EXISTS reviewHistory');
                self.tables.each( function(table) { dbSql(tx, 'DROP TABLE IF EXISTS ' + table) });
            }
        );
        dbTransaction(self.db,
            function(tx) {
                if(resCallback)
                    resCallback();
                else
                    self.nextCard()
                //$('eraseDeck').disabled = false;
            }
        );
    }
    catch(e){
        anki_exception('Exception:' + e);
    }
}

Deck.prototype.initialize = function(isNewDeck){
	var self = this;
	try {
        anki_log('Init deck' + self.syncName);
		self.db = dbOpen("iAnki-"+self.syncName+"-deck", "1.0", "iAnki "+self.syncName+" deck", 4000000);
        anki_log(' create tables');
        
        if(!self.db)
            return;
        if(isNewDeck || autoKill) {
            self.eraseDeck(function() {});
        }
		dbTransaction(self.db,
			function(tx)
			{
                dbSql(tx,'CREATE TABLE IF NOT EXISTS syncTimes ( \
								id INTEGER NOT NULL,  \
								lastSyncHost NUMERIC(10, 2) NOT NULL,  \
                                lastSyncClient NUMERIC(10, 2) NOT NULL,  \
                                version NUMERIC DEFAULT 0.0202, \
                                PRIMARY KEY (id) \
                                )');                
                syncTimesQ = new dbSqlQ(tx, 'SELECT * FROM syncTimes LIMIT 1');
                
                dbSql(tx,'CREATE TABLE IF NOT EXISTS extra ( \
								id INTEGER NOT NULL,  \
								"css" TEXT DEFAULT "",  \
                                PRIMARY KEY (id) \
                                )');
            }
        );
        
        dbTransaction(self.db,
			function(tx)
			{               
                // Unfortunatly the ids in Anki's tables are 64bit ints, which aren't handled correctly
                // in JS, so I've changed them all to TEXT to preserve them.
				dbSql(tx,'CREATE TABLE IF NOT EXISTS decks ( \
								id TEXT NOT NULL,  \
								created NUMERIC(10, 2) NOT NULL,  \
								modified NUMERIC(10, 2) NOT NULL,  \
								description TEXT NOT NULL,  \
								version INTEGER NOT NULL,  \
								"currentModelId" TEXT,  \
								"syncName" TEXT,  \
								"lastSync" NUMERIC(10, 2) NOT NULL,  \
								"hardIntervalMin" NUMERIC(10, 2) NOT NULL,  \
								"hardIntervalMax" NUMERIC(10, 2) NOT NULL,  \
								"midIntervalMin" NUMERIC(10, 2) NOT NULL,  \
								"midIntervalMax" NUMERIC(10, 2) NOT NULL,  \
								"easyIntervalMin" NUMERIC(10, 2) NOT NULL,  \
								"easyIntervalMax" NUMERIC(10, 2) NOT NULL,  \
								delay0 INTEGER NOT NULL,  \
								delay1 INTEGER NOT NULL,  \
								delay2 FLOAT NOT NULL,  \
								"collapseTime" INTEGER NOT NULL,  \
								"highPriority" TEXT NOT NULL,  \
								"medPriority" TEXT NOT NULL,  \
								"lowPriority" TEXT NOT NULL,  \
								suspended TEXT NOT NULL,  \
								"newCardOrder" INTEGER NOT NULL,  \
								"newCardSpacing" INTEGER NOT NULL,  \
								"failedCardMax" INTEGER NOT NULL,  \
								"newCardsPerDay" INTEGER NOT NULL,  \
								"sessionRepLimit" INTEGER NOT NULL,  \
								"sessionTimeLimit" INTEGER NOT NULL,  \
								"revCardOrder" INTEGER NOT NULL, \
                                PRIMARY KEY (id) \
								)');
				dbSql(tx,'CREATE TABLE IF NOT EXISTS models ( \
								id TEXT NOT NULL, \
								"deckId" TEXT, \
								created NUMERIC(10, 2) NOT NULL, \
								modified NUMERIC(10, 2) NOT NULL, \
								tags TEXT NOT NULL, \
								name TEXT NOT NULL, \
								description TEXT NOT NULL, \
								features TEXT NOT NULL, \
								spacing NUMERIC(10, 2) NOT NULL, \
								"initialSpacing" NUMERIC(10, 2) NOT NULL, \
                                PRIMARY KEY (id) \
								)');
				dbSql(tx, 'CREATE TABLE IF NOT EXISTS facts ( \
								id TEXT NOT NULL,  \
								"modelId" TEXT NOT NULL,  \
								created NUMERIC(10, 2) NOT NULL,  \
								modified NUMERIC(10, 2) NOT NULL,  \
								tags TEXT NOT NULL,  \
								"spaceUntil" NUMERIC(10, 2) NOT NULL,  \
								"lastCardId" TEXT,  \
                                PRIMARY KEY (id) \
								)');
				dbSql(tx,'CREATE TABLE IF NOT EXISTS cards ( \
								id TEXT NOT NULL,  \
								"factId" TEXT NOT NULL,  \
								"cardModelId" TEXT NOT NULL,  \
								created NUMERIC(10, 2) NOT NULL,  \
								modified NUMERIC(10, 2) NOT NULL,  \
								tags TEXT NOT NULL,  \
								ordinal INTEGER NOT NULL,  \
								question TEXT NOT NULL,  \
								answer TEXT NOT NULL,  \
								priority INTEGER NOT NULL,  \
								interval NUMERIC(10, 2) NOT NULL,  \
								"lastInterval" NUMERIC(10, 2) NOT NULL,  \
								due NUMERIC(10, 2) NOT NULL,  \
								"lastDue" NUMERIC(10, 2) NOT NULL,  \
								factor NUMERIC(10, 2) NOT NULL,  \
								"lastFactor" NUMERIC(10, 2) NOT NULL,  \
								"firstAnswered" NUMERIC(10, 2) NOT NULL,  \
								reps INTEGER NOT NULL,  \
								successive INTEGER NOT NULL,  \
								"averageTime" NUMERIC(10, 2) NOT NULL,  \
								"reviewTime" NUMERIC(10, 2) NOT NULL,  \
								"youngEase0" INTEGER NOT NULL,  \
								"youngEase1" INTEGER NOT NULL,  \
								"youngEase2" INTEGER NOT NULL,  \
								"youngEase3" INTEGER NOT NULL,  \
								"youngEase4" INTEGER NOT NULL,  \
								"matureEase0" INTEGER NOT NULL,  \
								"matureEase1" INTEGER NOT NULL,  \
								"matureEase2" INTEGER NOT NULL,  \
								"matureEase3" INTEGER NOT NULL,  \
								"matureEase4" INTEGER NOT NULL,  \
								"yesCount" INTEGER NOT NULL,  \
								"noCount" INTEGER NOT NULL,  \
								"spaceUntil" NUMERIC(10, 2) NOT NULL,  \
								"relativeDelay" NUMERIC(10, 2) NOT NULL,  \
								"isDue" BOOLEAN NOT NULL,  \
								type INTEGER NOT NULL,  \
								"combinedDue" INTEGER NOT NULL,  \
                                PRIMARY KEY (id) \
								)');
				dbSql(tx, 'CREATE TABLE IF NOT EXISTS "reviewHistory" ( \
								id INTEGER NOT NULL,  \
								"cardId" TEXT,  \
								time NUMERIC(10, 2) NOT NULL,  \
								"lastInterval" NUMERIC(10, 2) NOT NULL,  \
								"nextInterval" NUMERIC(10, 2) NOT NULL,  \
								ease INTEGER NOT NULL,  \
								delay NUMERIC(10, 2) NOT NULL,  \
								"lastFactor" NUMERIC(10, 2) NOT NULL,  \
								"nextFactor" NUMERIC(10, 2) NOT NULL,  \
								reps NUMERIC(10, 2) NOT NULL,  \
								"thinkingTime" NUMERIC(10, 2) NOT NULL,  \
								"yesCount" NUMERIC(10, 2) NOT NULL,  \
								"noCount" NUMERIC(10, 2) NOT NULL,  \
                                PRIMARY KEY (id) \
								)');
                
                // Stats have been disabled
                dbSql(tx, 'DROP TABLE IF EXISTS stats');
                
                                // Drop old views & indices from decks with older versions
                if(syncTimesQ.result().rows.length > 0) {
                    var sync = syncTimesQ.result().rows.item(0);
                    var version = 0.0;
                    if(sync.version)
                        version = sync.version;
                    else
                        dbSql(tx,'ALTER TABLE syncTimes ADD version NUMERIC DEFAULT 0.0000');                    
                    if(version < 0.22) {
                        dbSql(tx,'DROP VIEW IF EXISTS acqCardsOrdered');
                        dbSql(tx,'DROP VIEW IF EXISTS acqCardsRandom');
                        dbSql(tx,'DROP VIEW IF EXISTS failedCardsNow');
                        dbSql(tx,'DROP VIEW IF EXISTS failedCards');
                        dbSql(tx,'DROP VIEW IF EXISTS failedCardsSoon');
                        dbSql(tx,'DROP VIEW IF EXISTS revCards');
                        
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_markExpired');
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_failedIsDue');
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_failedOrder');
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_revisionOrder');
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_newRandomOrder');
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_newOrderedOrder');
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_factId');
                    }
                    if(version < 0.25) {
                        dbSql(tx,'DROP VIEW IF EXISTS revCards');
                        dbSql(tx,'DROP VIEW IF EXISTS revCardsOld');
                        dbSql(tx,'DROP VIEW IF EXISTS revCardsNew');
                        dbSql(tx,'DROP VIEW IF EXISTS revCardsDue');
                        dbSql(tx,'DROP VIEW IF EXISTS revCardsRandom');
                        dbSql(tx,'DROP VIEW IF EXISTS acqCardsRandom');
                        
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_newRandomOrder');
                        dbSql(tx,'DROP INDEX IF EXISTS ix_cards_revisionOrder');
                        
                        //dbSql(tx,'alter table decks add column revCardOrder integer not null default 0');
                    }
                }
                else
                {
                    dbSql(tx, 'INSERT INTO syncTimes (lastSyncHost, lastSyncClient) VALUES (?,?)',[0, 0]);
                }
                
                /*
				dbSql(tx, 'CREATE TABLE IF NOT EXISTS stats ( \
								id TEXT NOT NULL,  \
								type INTEGER NOT NULL,  \
								day DATE NOT NULL,  \
								reps INTEGER NOT NULL,  \
								"averageTime" NUMERIC(10, 2) NOT NULL,  \
								"reviewTime" NUMERIC(10, 2) NOT NULL,  \
								"distractedTime" NUMERIC(10, 2) NOT NULL,  \
								"distractedReps" INTEGER NOT NULL,  \
								"newEase0" INTEGER NOT NULL,  \
								"newEase1" INTEGER NOT NULL,  \
								"newEase2" INTEGER NOT NULL,  \
								"newEase3" INTEGER NOT NULL,  \
								"newEase4" INTEGER NOT NULL,  \
								"youngEase0" INTEGER NOT NULL,  \
								"youngEase1" INTEGER NOT NULL,  \
								"youngEase2" INTEGER NOT NULL,  \
								"youngEase3" INTEGER NOT NULL,  \
								"youngEase4" INTEGER NOT NULL,  \
								"matureEase0" INTEGER NOT NULL,  \
								"matureEase1" INTEGER NOT NULL,  \
								"matureEase2" INTEGER NOT NULL,  \
								"matureEase3" INTEGER NOT NULL,  \
								"matureEase4" INTEGER NOT NULL,  \
								PRIMARY KEY (id) \
								)');
                */
                dbSql(tx,'	CREATE VIEW IF NOT EXISTS failedCards as \
								select * from cards \
								where type = 0 and priority != 0 \
								order by modified \
								');
				dbSql(tx,'	CREATE VIEW IF NOT EXISTS failedCardsSoon as \
                                select * from cards \
                                where type = 0 and +priority in (1,2,3,4) \
                                and combinedDue <= (select max(delay0, delay1) + \
                                strftime("%s", "now")+1 from decks where id = 1) \
                                order by type, isDue, combinedDue \
								');
                
		dbSql(tx,'	CREATE VIEW IF NOT EXISTS revCardsOld as \
				    select * from cards \
				    where type = 1 and isDue = 1 \
				    order by priority desc, interval desc');
		dbSql(tx,'	CREATE VIEW IF NOT EXISTS revCardsNew as \
				    select * from cards \
				    where type = 1 and isDue = 1 \
				    order by priority desc, interval');
		dbSql(tx,'	CREATE VIEW IF NOT EXISTS revCardsDue as \
				    select * from cards \
				    where type = 1 and isDue = 1 \
				    order by priority desc, combinedDue');
		dbSql(tx,'	CREATE VIEW IF NOT EXISTS revCardsRandom as \
				    select * from cards \
				    where type = 1 and isDue = 1 \
				    order by priority desc, factId, ordinal');
		
		
                dbSql(tx,'	CREATE VIEW IF NOT EXISTS acqCardsRandom as \
								select * from cards \
								where type = 2 and isDue = 1 \
								order by priority desc, factId, ordinal \
								');
				dbSql(tx,'	CREATE VIEW IF NOT EXISTS acqCardsOrdered as \
								select * from cards \
								where type = 2 and isDue = 1 \
								order by priority desc, combinedDue \
								');
				dbSql(tx,'	CREATE VIEW IF NOT EXISTS failedCardsNow as \
                                select * from cards \
                                where type = 0 and isDue = 1 \
                                and +priority in (1,2,3,4) \
                                order by type, isDue, combinedDue \
								');
                
                // card queues
                dbSql(tx,'create index if not exists ix_cards_combinedDue on cards \
                            (type, isDue, combinedDue, priority)');
                
		dbSql(tx,'create index if not exists ix_cards_revOldOrder on cards \
			    (type, isDue, priority desc, interval desc)');
		
		dbSql(tx,'create index if not exists ix_cards_revNewOrder on cards \
			    (type, isDue, priority desc, interval)');
		
                dbSql(tx,'create index if not exists ix_cards_newRandomOrder on cards \
                            (type, isDue, priority desc, factId, ordinal)');
		
                dbSql(tx,'create index if not exists ix_cards_newOrderedOrder on cards \
                            (type, isDue, priority desc, combinedDue)');
                
                // card spacing
                dbSql(tx,'create index if not exists ix_cards_factId on cards (factId)');
                
                ///////////////
                
                dbSql(tx,'create index if not exists ix_cards_markExpired on cards \
                            (isDue, priority desc, combinedDue desc)');
                
                dbSql(tx,'create index if not exists ix_cards_failedIsDue on cards \
                        (type, isDue, combinedDue)');
                
                dbSql(tx,'create index if not exists ix_cards_failedOrder on cards \
                        (type, isDue, due)');    
                 
                dbSql(tx,'UPDATE syncTimes SET version=?', [0.32]);
			}
		);
        
        self.loadDeck();
	}
	catch(e){
		anki_exception('Exception:' + e);
	}
}

// IAnki class
function IAnki(){
}

IAnki.prototype.setTitle = function(title){
    $('title').innerHTML = title;
}

IAnki.prototype.appendTitle = function(title){
    $('title').innerHTML += title;
}

IAnki.prototype.setInfo = function(info){
    $('info').innerHTML = info;
}

IAnki.prototype.setMode = function(mode){
    anki_log('iAnki.setMode ' + mode.id);
    
    if(this.currMode && this.currMode != mode)
        this.currMode.style.display = 'none';
    this.currMode = mode;
    this.currMode.style.display = 'block';
    
    if(this.currMode != $('reviewMode'))
        document.title = iankiVersion;
}

IAnki.prototype.initialize = function() {	
    try {
	var self = this;
	self.currMode = $('infoMode');
        self.setTitle(versionTitle + 'Welcome');
	self.setInfo('Initializing...');
	self.setMode($('infoMode'));
	
	anki_log('Is online, ' + navigator.onLine + ' ' + today(new Date()));
	
        if (!window.openDatabase) {
            alert("Couldn't open the local database.  Please try a browser compatible with HTML 5 database API.");
            return;
        }
                
        // Init deck index
        self.dbBase = dbOpen('iAnki-Settings', "1.0", "iAnki settings database", 100000);
        
        var settingsQ;
		dbTransaction(self.dbBase,
			function(tx)
			{
				//dbSql(tx,'DROP TABLE IF EXISTS settings');
				//dbSql(tx,'DROP TABLE IF EXISTS decks');
				
                dbSql(tx,'CREATE TABLE IF NOT EXISTS settings ( \
							id INTEGER NOT NULL,  \
							currentDeck TEXT, \
                            PRIMARY KEY (id) \
							)', [],
							function(result) {
				       	    	anki_log("Created dbBase settings table.");
							},
							function(tx, error) {
				       	        anki_exception("Failed to create dbBase settings table." + error.message);
							});
                
                settingsQ = new dbSqlQ(tx, 'SELECT * FROM settings LIMIT 1');
                
				dbSql(tx,'CREATE TABLE IF NOT EXISTS decks ( \
							id INTEGER NOT NULL,  \
							name TEXT NOT NULL, \
                            PRIMARY KEY (id) \
							)', [],
							function(result) {
				       	    	anki_log("Created dbBase decks table.");
							},
							function(tx, error) {
				       	        anki_exception("Failed to create dbBase decks table." + error.message);
							});
			}
		);
        
        // Load global settings
        var inDecksQ = null;
        dbTransaction(self.dbBase,
            function(tx)
            {
                anki_log("Load global settings.");
                if(settingsQ.result().rows.length == 0) {
                    anki_log("Setting default initial settings.");
                    self.currentDeck = '';
                    dbSql(tx, 'INSERT INTO settings (currentDeck) values (?)', [self.currentDeck]);
                }
                else{
                    self.currentDeck = settingsQ.result().rows.item(0).currentDeck;
                    inDecksQ = new dbSqlQ(tx, 'SELECT name FROM decks WHERE name = ?', [self.currentDeck]);
                }
            }
        );
        
        dbTransaction(self.dbBase,
            function(tx)
            {
                if(self.currentDeck != '') {
                    if(inDecksQ.result().rows.length == 0) {
                        anki_log("Restoring lost deck " + self.currentDeck);
                        dbSql(tx, 'INSERT INTO decks (name) values (?)', [self.currentDeck]);
                    }
                    anki_log("Load current deck " + self.currentDeck);
                    self.deck = new Deck(self.currentDeck, false);
                    anki_log("Next card on " + self.currentDeck);
                    self.deck.nextCard()
                }
                else {
                    anki_log("No deck is selected.");
                    self.setTitle(versionTitle + 'Welcome');
                    self.setInfo('There are no decks.');
                    self.setMode($('infoMode'));
                }
            }
        );
		
        dbTransaction(self.dbBase,
            function(tx){
            //self.deck = new Deck();
            //self.deck.initialize();
            }
        );
    }
    catch(e){
        anki_exception('Exception:' + e);
    }
}

var numRequests = 0;
request_callback = undefined;

function request_chunk(send, url, callback)
{
    request_callback = callback;
    request_script = document.createElement("script");
    // The browser may cache the request if it has the same URL, so add some salt for randomness
    salt = "&ctime="+encodeURIComponent(''+nowInSeconds()+numRequests);
    var req = iankiServer+url + "?" + send + salt;
    numRequests += 1;
    anki_log("<br>-----<br>"+req.length+" "+req+"<br>-----<br>");
    request_script.src = req;
    document.getElementsByTagName("body")
        [0].appendChild(request_script);
}

function request_receive(data)
{
    document.getElementsByTagName("body")
        [0].removeChild(request_script);
    request_callback(data);
}

function request_send(send, url, callback)
{
    var id = encodeURIComponent(nowInSeconds());
    var data = send;
    var pos = 0;
    var len = data.length;
    var maxChunk = 1000;
    
    function do_chunk(status, arg){
        anki_log("do_chunk "+status + ", " + arg);
	iAnki.appendTitle(' -');
        if(pos != len){
            var todo = Math.min(len-pos, maxChunk);
            if(todo >= 1 && data.charAt(pos+todo-1) == '%')
                todo += 2;
            else if(todo >= 2 && data.charAt(pos+todo-2) == '%')
                todo += 1;
            var todoPart = data.substring(pos, pos+todo);
            anki_log("Todo:"+todoPart);
            pos += todo;
            request_chunk("id="+id+"&togo="+(len-pos)+"&payload="+todoPart, url, do_chunk);
        }	
        else{
	    if(status == 'wait')
		request_chunk("id="+id, url, do_chunk);
	    else
		callback(arg);
        }
    }
    do_chunk('start', '');
}

IAnki.prototype.syncNextDeck = function(){
    try {
        var self = this;
        
        if(self.nextDeck < self.syncDecks.length)
        {
            var syncName = self.syncDecks[self.nextDeck];
            self.nextDeck++;
            
            anki_log("Start sync deck: " + syncName);
            
            var deckQ;
            dbTransaction(self.dbBase,
                function(tx)
                {
                    deckQ = new dbSqlQ(tx,'SELECT * FROM decks \
                                        WHERE name = ?', [syncName])
                }
            );
            
            dbTransaction(self.dbBase,
                function(tx)
                {
                    anki_log("Check result");
                    var isNewDeck = false;
                    if(deckQ.result().rows.length == 0) {
                        anki_log("Creating deck: " + syncName + " on client");
                        dbSql(tx, 'INSERT INTO decks (name) values (?)', [syncName]);
                        isNewDeck = true;
                    }
                    else {
                        anki_log("Syncing existing deck: " + syncName + " on client");
                    }
                    
                    // Set this deck as the current deck, and sync the deck
                    self.currentDeck = syncName;
                    dbSql(tx,'UPDATE settings SET currentDeck=?', [self.currentDeck]);
                    self.deck = new Deck(syncName, isNewDeck);
                    
                    self.deck.realSync(
                        function()
                        {
                            anki_log("syncNextDeck callback " + self.nextDeck + " of " + self.syncDecks.length);
                            if(self.nextDeck < self.syncDecks.length) {
                                self.syncNextDeck();
                            }
                            else {
                                //self.loadDeck();
                                self.deck.nextCard();
                                $('syncDeck').disabled = false;
                            }
                        }
                    );
                }
            );
        }
        else
        {
            $('syncDeck').disabled = false;
        }
    }
    catch (e) {
        anki_exception('IAnki.syncNextDeck exception:' + e);
        $('syncDeck').disabled = false;
    }
}

IAnki.prototype.syncDeck = function(mode){    
    try {
        var self = this;
        $('syncDeck').disabled = true;
        iAnki.setInfo('Syncing...');
	iAnki.setTitle('Synching');
        iAnki.setMode($('infoMode'));
        
        anki_log("Fetching deck info.")
        
        function syncCallback(result) {
            try {
                json = result; // JSON.decode(result, true)
                //alert(json);
                
                if(json['error'] != 0) {
                    anki_exception("Error syncing deck in syncCallback:" + json['exception']);
                    return;
                }
                
                self.syncDecks = json['deck'];
                self.nextDeck = 0;
                self.syncNextDeck();
            }
            catch (e) {
                anki_exception('syncCallback exception:' + e);
            }
        }
        request_send(encodeURIComponent('{"method":"getdeck"}'), 'anki/sync.html', syncCallback);
    }
    catch (e) {
        anki_exception('IAnki.syncDeck exception:' + e);
        $('syncDeck').disabled = false;
    }
}

IAnki.prototype.setDeck = function(name) {
    try {
        var self = this;
        anki_log('IAnki.setDeck ' + name);
        self.currentDeck = name;
        dbTransaction(self.dbBase,
            function(tx)
            {
                dbSql(tx,'UPDATE settings SET currentDeck=?', [self.currentDeck]);
            }
        );
        dbTransaction(self.dbBase,
            function(tx)
            {
                self.deck = new Deck(name, false);
                self.deck.nextCard();
            }
        );
    }
    catch (e) {
        anki_exception('IAnki.setDeck exception:' + e);
    }
}

IAnki.prototype.deleteDeck = function(name) {
    try {
        var self = this;
        anki_log('IAnki.deleteDeck ' + name);
        self.currentDeck = name;
        self.deck = new Deck(name, false);
        self.deck.eraseDeck(
            function(){
                self.deck = null;
                self.currentDeck = '';
                dbTransaction(self.dbBase,
                    function(tx)
                    {
                        dbSql(tx, 'DELETE FROM decks WHERE name = ?', [name])
                        dbSql(tx, 'UPDATE settings SET currentDeck = ?', [''])
                        
                    }
                );
                dbTransaction(self.dbBase,
                    function(tx)
                    {
                        self.chooseDeck();
                    }
                );
            }
        );
    }
    catch (e) {
        anki_exception('IAnki.setDeck exception:' + e);
    }
}

IAnki.prototype.chooseDeck = function(really){
    try {
        var self = this;
        anki_log('Choose deck view.');
        
        var deckQ;
        dbTransaction(self.dbBase,
            function(tx)
            {
                deckQ = new dbSqlQ(tx,'SELECT * FROM decks', [])
            }
        );
        
        dbTransaction(self.dbBase,
            function(tx)
            {
                var rows = "<table cellpadding=0 cellspacing=0 style='font-size: 20px; margin: 16px'>";
                var result = deckQ.result();
                if(result.rows.length > 0){
                    for(var d = 0; d < result.rows.length; d++){
                        var name = result.rows.item(d).name;
                        rows += "<tr>"
                        rows += "<td><a onclick='iAnki.setDeck(\"" + name + "\")'>"+name+"</a></td> ";
                        if(name == really) {
                            rows += "<td align=right><a onclick='iAnki.deleteDeck(\"" + name + "\")'>Confirm?</a></td>";
                        } else {
                            rows += "<td align=right><a onclick='iAnki.chooseDeck(\"" + name + "\")'>Delete</a></td>";
                        }
                        rows += "</tr>";
                    }
                    rows += '</table>';
                    $('deckTable').innerHTML = rows;
                    iAnki.setTitle(iankiVersion);
                    iAnki.setMode($('changeDeckMode'));
                }
                else {
                    iAnki.setTitle(versionTitle+'Welcome');
                    iAnki.setInfo('There are no decks.');
                    iAnki.setMode($('infoMode'));
                }
            }
        );
    }
    catch (e) {
        anki_exception('IAnki.chooseDeck exception:' + e);
    }
}

try {
    if(!isDefined(typeof window.openDatabase)) {
        iAnki.setInfo('Try enabling Gears support.');
        iAnki.setMode($('infoMode'));
    }
    else {
        window.addEvent('domready',
            function(event){
                /*
                var myVerticalSlide = new Fx.Slide('vertical_slide');
                $('more').addEvent('click', function(e){
                    e.stop();
                    myVerticalSlide.toggle();
                });
                */
                
                iAnki = new IAnki(); // The global IAnki class
                iAnki.initialize();
            },
            false
        );
    }
} 
catch (e) {
    anki_exception('\nAn exception ocurred\nTry enabling Gears support.');
}

/*
    <meta name="viewport" content="width=device-width; initial-scale=1.0; maximum-scale=1.0; user-scalable=true;" />
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
    <meta name="apple-mobile-web-app-capable" content="yes" />.
    <meta names="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    //padding: 10px; width: 140px; height: 80px; margin: 16px;
*/
