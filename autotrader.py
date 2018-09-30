import sys
import os
import os.path
import re
import unicodedata
import time
import datetime
import urllib2
import json
import sched
import uuid
from enum import Enum

####################################################################################################
# AUTO TRADER
# A simple script for testing trading algorithms
####################################################################################################

############################################################################# VARIABLES

# Shell parameter: run mode -> dev mode (reset all database!)
runMode = 'standard'
if len(sys.argv) > 1:
    runMode = sys.argv[1]

# scheduler for watch mode interval
watchScheduler = sched.scheduler( time.time, time.sleep )
# amount of seconds the scheduler executes the check function
watchSchedulerDelay = 1 # 3600

# configure file paths
filePathTradeHistoryBtcEur='./trade-history-btceur.csv'
filePathExchangerateHistoryBtcEur='./exchangerate-history.csv'

filePathWalletBtc='./wallet-btc-balance.csv'
filePathWalletEur='./wallet-eur-balance.csv'

# configure URLs
urlExchangeRates = 'https://blockchain.info/ticker'


############################################################################# CONSTANTS

CSV_DELMITER = ','

TRADE_ACTIONS = Enum('TRADE_ACTIONS', 'BUY, SELL')

CURRENCY_BTC_SMALLEST_UNIT = float( 0.00000001 ) # Unit Satoshi

CURRENCY_BTC_SMALLEST_STEP = 100000000

CURRENCY_EUR_SMALLEST_UNIT = float( 0.01 ) # Unit Cent

CURRENCY_EUR_SMALLEST_STEP = 100


############################################################################# FUNCTIONS


############## BASIC

# get UNIX timestamp
def getTimeStampUnix():
    return int( time.time() )

# get UTC timestamp
def getTimeStampUtc():
    return datetime.datetime.utcnow()

# get unique id
def getUniqueId():
    return uuid.uuid4()

# Check if input is a valid number (integer and or float)
def isNumber( numberCheck ):
    try:
        int( numberCheck )
        return True
    except ValueError:
        raise ValueError( 'isNumber(): Is not of type number (INTEGER or FLOAT):', numberCheck )

# Check if the file at given path does exist
def checkFileExist( PATH ):
    if os.path.isfile(PATH) and os.access(PATH, os.R_OK):
        return True
    else:
        raise ValueError( 'checkFileExist(): Either the file is missing or not readable:', PATH )

# Check if the file at given path is not empty
def checkFileIsNotEmpty( PATH ):
    if os.stat( PATH ).st_size > 0:
        return True
    else:
        raise ValueError( 'checkFileIsNotEmpty(): File is empty:', PATH )


############## READ

# Get balance from CSV file, which is the last line and the last cell
# CSV file table columns are: timestamp (unix timestamp), balance (integer)
def getLastRowCellFloatFromCsvFile( PATH, DELIMITER ):
    if ( checkFileExist( PATH ) and checkFileIsNotEmpty( PATH ) ):
        with open( PATH, 'r' ) as f:
            # get all lines
            lines = f.read().splitlines()
            # close file
            f.close()
            # get last line
            lastLine = lines[-1]
            # get last value of line
            currentBalance = lastLine.split( DELIMITER )[-1]
            # return or error
            if isNumber( currentBalance ):
                return int(currentBalance)
            else:
                raise ValueError( 'getLastRowCellFloatFromCsvFile(): Wallet file corrupt:', PATH )

# Get the current balance (amount of currency) of Euros
def getCurrentBalanceEur():
    return getLastRowCellFloatFromCsvFile( filePathWalletEur, CSV_DELMITER )

# Get the current balance (amount of currency) of Bitcoins
def getCurrentBalanceBtc():
    return getLastRowCellFloatFromCsvFile( filePathWalletBtc, CSV_DELMITER )

# Get rate of the last trade made
def getRateOfLastTradeBtcEur():
    return getLastRowCellFloatFromCsvFile( filePathTradeHistoryBtcEur, CSV_DELMITER )


############## GET EXTERNAL DATA

# Make request to blockchain.info to get current exchange rates
def getCurrentExchangeRates():
    response_body = urllib2.urlopen( urlExchangeRates ).read()
    response_dictionary = json.loads( response_body )
    return response_dictionary

# Get latest exchange rate of Bitcoin/Currency
def getCurrentExchangeRate( CURRENCY ):
    currentExchangeRates = getCurrentExchangeRates()
    return currentExchangeRates[ CURRENCY ][ 'last' ]

# Get latest exchange rate of Bitcoin/Euro
def getCurrentExchangeRateBtcEur():
    return getCurrentExchangeRate( 'EUR' )

# Get latest exchange rate of Bitcoin(Satoshi)/Euro
def getCurrentExchangeRateBtcEurInCents():
    return int( getCurrentExchangeRateBtcEur() * CURRENCY_EUR_SMALLEST_STEP )


############## WRITE

# Delete all contents of file at PATH
def truncateFile( PATH ):
    with open( PATH, 'w' ) as f:
        f.truncate()
        f.close()

# Append a new line into a file
def appendNewLineInFile( PATH, LINE ):
    if checkFileExist( PATH ):
        with open( PATH, 'a' ) as f:
            f.write( str(LINE) + '\n' )
            f.close()

# Set wallets to initial, empty value
def resetHistories():
    # reset log files to start data

    # reset wallet BTC to start data
    truncateFile( filePathTradeHistoryBtcEur )
    appendNewLineInFile( filePathTradeHistoryBtcEur, 'timestamp' + CSV_DELMITER + 'id' + CSV_DELMITER + 'BTC' + CSV_DELMITER + 'EUR' + CSV_DELMITER + 'rate' )
    appendNewLineInFile( filePathTradeHistoryBtcEur, '1528524100' + CSV_DELMITER + str(getUniqueId()) + CSV_DELMITER + '+19620000' + CSV_DELMITER + '-109890' + CSV_DELMITER + '540000' )
    appendNewLineInFile( filePathTradeHistoryBtcEur, '1538262307' + CSV_DELMITER + str(getUniqueId()) + CSV_DELMITER + '-19620000' + CSV_DELMITER + '109890' + CSV_DELMITER + '575000' )
    # reset exchange rate history
    truncateFile( filePathExchangerateHistoryBtcEur )
    appendNewLineInFile( filePathExchangerateHistoryBtcEur, 'timestamp' + CSV_DELMITER + 'rate' )
    appendNewLineInFile( filePathExchangerateHistoryBtcEur, '1528524100' + CSV_DELMITER + '558264' )
    # appendNewLineInFile( filePathExchangerateHistoryBtcEur, '1528524100' + CSV_DELMITER + '590000' )

# Set wallets to initial, empty value
def resetWallets():
    # reset wallet BTC
    truncateFile( filePathWalletBtc )
    appendNewLineInFile( filePathWalletBtc, 'timestamp' + CSV_DELMITER + 'id' + CSV_DELMITER + 'amount' )
    # reset wallet EUR
    truncateFile( filePathWalletEur )
    appendNewLineInFile( filePathWalletEur, 'timestamp' + CSV_DELMITER + 'id' + CSV_DELMITER + 'amount' )

# log trade action
def logNewTradeHistoryEntryBtcEur( TRADE_ACTION, BTC, EUR, CURRENT_EXCHANGE_RATE_BTC_SATOSHI_EUR ):

    # define trading amount prefixes
    tradeAction = None
    if TRADE_ACTION == TRADE_ACTIONS.BUY:
        tradeAction = 'BUY'
    if TRADE_ACTION == TRADE_ACTIONS.SELL:
        tradeAction = 'SELL'

    newBalanceBtcLogHumanReadable = BTC * CURRENCY_BTC_SMALLEST_UNIT
    newBalanceBtcLog = str( float( ( '%0.8f' %newBalanceBtcLogHumanReadable ) ) )

    newBalanceEurLogHumanReadable = EUR * CURRENCY_EUR_SMALLEST_UNIT
    newBalanceEurLog = str( float( ( '%0.2f' %newBalanceEurLogHumanReadable ) ) )

    print '### ' + tradeAction + ' ' + str(newBalanceBtcLog) + ' BTC for ' + str(newBalanceEurLog) + ' EUR at ' + str(getTimeStampUtc())

# Log a new trade if being made. Table columns: id, timestamp, btc, eur, rate
def setNewTradeHistoryEntryBtcEur( ID, TRADE_ACTION, BTC, EUR, RATE ):
    # define trading amount prefixes
    prefixBtc = None
    prefixEur = None
    if TRADE_ACTION == TRADE_ACTIONS.BUY:
        prefixBtc = '+'
        prefixEur = '-'
    if TRADE_ACTION == TRADE_ACTIONS.SELL:
        prefixBtc = '-'
        prefixEur = '+'

    newLine = str(getTimeStampUnix()) + CSV_DELMITER + ID + CSV_DELMITER + prefixBtc + str(BTC) + CSV_DELMITER + prefixEur + str(EUR) + CSV_DELMITER + str(RATE)
    appendNewLineInFile( filePathTradeHistoryBtcEur, newLine )
    # log action
    logNewTradeHistoryEntryBtcEur( TRADE_ACTION, BTC, EUR, RATE )

# Log the rate of BTC/EUR rate every watch loop. Table columns: timestamp, rate
def setNewExchangeRateHistoryEntryEur( RATE ):
    newLine = str(getTimeStampUnix()) + CSV_DELMITER + str(RATE)
    appendNewLineInFile( filePathExchangerateHistoryBtcEur, newLine )

# set new currency balance row in file
def setNewBalanceInFile( PATH, ID, BALANCE ):
    newLine = str(getTimeStampUnix()) + CSV_DELMITER + ID + CSV_DELMITER + str(BALANCE)
    appendNewLineInFile( PATH, newLine )

# set new BTC balance
def setNewBalanceBtc( ID, BALANCE ):
    setNewBalanceInFile( filePathWalletBtc, ID, BALANCE )

# set new EUR balance
def setNewBalanceEur( ID, BALANCE ):
    setNewBalanceInFile( filePathWalletEur, ID, BALANCE )

# Exchange BTC for EUR
def sellBtcForEur( AMOUNT_BTC ):

    # generate unique id
    uniqueId = str(getUniqueId())

    # get exchange rate
    currentExchangeRateBtcEur = getCurrentExchangeRateBtcEur()
    currentExchangeRateBtcEurInCents = getCurrentExchangeRateBtcEurInCents()

    # get current balance BTC
    currentBalanceBtc = getCurrentBalanceBtc()
    currentBalanceEur = getCurrentBalanceEur()

    # check if enough BTC to sell
    if currentBalanceBtc < AMOUNT_BTC:
        raise ValueError( 'sellBtcForEur(): Insufficient balance BTC: ', currentBalanceBtc )

    # calculate new balance BTC
    newBalanceBtc = int( currentBalanceBtc - AMOUNT_BTC )

    # calculate amount EUR recieved for amount BTC
    amountEurRecieved = int( round( ( ( AMOUNT_BTC * CURRENCY_BTC_SMALLEST_UNIT ) * currentExchangeRateBtcEur ) * CURRENCY_EUR_SMALLEST_STEP ) )

    # calculate new balance EUR
    newBalanceEur = int(currentBalanceEur + amountEurRecieved)

    # set new balance EUR
    setNewBalanceBtc( uniqueId, newBalanceBtc )

    # set new balance BTC
    setNewBalanceEur( uniqueId, newBalanceEur )
    
    # log action
    setNewTradeHistoryEntryBtcEur( uniqueId, TRADE_ACTIONS.SELL, AMOUNT_BTC, amountEurRecieved, currentExchangeRateBtcEurInCents )

# Exchange EUR for BTC
def buyBtcForEur( AMOUNT_EUR ):

    # generate unique id
    uniqueId = str(getUniqueId())

    # get exchange rate
    currentExchangeRateBtcEur = getCurrentExchangeRateBtcEur()
    currentExchangeRateBtcEurInCents = getCurrentExchangeRateBtcEurInCents()

    # get current balance BTC
    currentBalanceBtc = getCurrentBalanceBtc()
    currentBalanceEur = getCurrentBalanceEur()

    # check if enough EUR to buy
    if currentBalanceEur < AMOUNT_EUR:
        raise ValueError( 'buyBtcForEur(): Insufficient balance EUR: ', currentBalanceEur )

    # calculate amount EUR recieved for amount BTC
    amountBtcRecieved = int( round( ( ( AMOUNT_EUR * CURRENCY_EUR_SMALLEST_UNIT ) * ( 1 / currentExchangeRateBtcEur ) ) * CURRENCY_BTC_SMALLEST_STEP ) )

    # calculate new balance BTC
    newBalanceBtc = int(currentBalanceBtc + amountBtcRecieved)

    # calculate new balance EUR
    newBalanceEur = int(currentBalanceEur - AMOUNT_EUR)

    # set new balance EUR
    setNewBalanceBtc( uniqueId, newBalanceBtc )

    # set new balance BTC
    setNewBalanceEur( uniqueId, newBalanceEur )
    
    # log action
    setNewTradeHistoryEntryBtcEur( uniqueId, TRADE_ACTIONS.BUY, amountBtcRecieved, AMOUNT_EUR, currentExchangeRateBtcEurInCents )


############## TRADE

def checkIfSell():

    rateOfLastTradeBtcEur = float( getRateOfLastTradeBtcEur() )
    currentExchangeRateBtcEurInCents = float( getCurrentExchangeRateBtcEurInCents() )

    print '### Rate Comparison: last exchange rate BTC/EUR: ' + str(int(rateOfLastTradeBtcEur)) + ', current exchange rate BTC/EUR: ' + str(int(currentExchangeRateBtcEurInCents)) + ' => percentual difference: ' + str( rateOfLastTradeBtcEur / currentExchangeRateBtcEurInCents )
    # if empty EUR fund, wait for BTC selling point
    if getCurrentBalanceBtc() > 0:
        # if current sell rate is greater than last sell rate by 6 percent, then SELL
        if ( float( rateOfLastTradeBtcEur / currentExchangeRateBtcEurInCents ) >= 1.06 ):
            print '### SELLING NOW -> last exchange rate BTC/EUR: ' + str(int(rateOfLastTradeBtcEur)) + ', current exchange rate BTC/EUR: ' + str(int(currentExchangeRateBtcEurInCents)) + ' => percentual difference: ' + str( rateOfLastTradeBtcEur / currentExchangeRateBtcEurInCents )
            sellBtcForEur( getCurrentBalanceBtc() )

    # if empty BTC fund, wait for EUR selling point
    if getCurrentBalanceEur() > 0:
        # if current buy rate is lesser than last buy rate by 6 percent, then BUY
        if ( float( rateOfLastTradeBtcEur / currentExchangeRateBtcEurInCents ) <= 0.94 ):
            print '### BUYING NOW -> last exchange rate BTC/EUR: ' + str(int(rateOfLastTradeBtcEur)) + ', current exchange rate BTC/EUR: ' + str(int(currentExchangeRateBtcEurInCents)) + ' => percentual difference: ' + str( rateOfLastTradeBtcEur / currentExchangeRateBtcEurInCents )
            buyBtcForEur( getCurrentBalanceEur() )


############################################################################# RUN

# Compare exchange rate and execute algorithm
def check():
    # log current BTC/EUR exchange rate
    setNewExchangeRateHistoryEntryEur( getCurrentExchangeRateBtcEurInCents() )
    checkIfSell()
    # print '### Current exchange rate BTC/EUR: ' + str(getCurrentExchangeRateBtcEur())

# Execute checkRates repeatedly
def watchMode(sc):
    check()
    watchScheduler.enter( watchSchedulerDelay, 1, watchMode, (sc,) )

# Start AutoTrader watch mode
def startWatchMode():
    watchScheduler.enter( watchSchedulerDelay, 1, watchMode, (watchScheduler,) )
    watchScheduler.run()


############################################################################# INIT

print '######################### AutoTrader v1.0.0'
print '### Runs in mode:', runMode

# check files
checkFileExist( filePathExchangerateHistoryBtcEur )
checkFileExist( filePathTradeHistoryBtcEur )
checkFileExist( filePathWalletEur )
checkFileExist( filePathWalletBtc )

##### Reset to initial values
if runMode == 'dev':
    resetHistories()
    resetWallets()
    # setNewBalanceBtc( 0.1962 )
    uniqueId = str(getUniqueId())
    setNewBalanceBtc( uniqueId, 0 )
    setNewBalanceEur( uniqueId, 100000 )

# get current wallet balances
print '### Current balance of BTC:', getCurrentBalanceBtc()
print '### Current balance of EUR:', getCurrentBalanceEur()

# Init successful
print '### AutoTrader successfully initialized and running'

# Start watch mode
startWatchMode()
