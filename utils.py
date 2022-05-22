import io
import os
from datetime import datetime
import csv
import const
import timers
import charger
import access

# window = evsGUI.window
# def printMsg(text=''):
#     window['-MESSAGE-'].update(text)

# todo: PV power must remain for x minutes before decision
# OK todo: use minimum charge time / pause time
# OK todo: set charger aws only once
# todo: night charging solution (charge < x%; manual intervention via remotecontrol ...)
# OK todo: Override local  decisions with remote control

charge = charger.Charger(const.C_CHARGER_WIFI_URL, const.C_CHARGER_API_VERSION)

class SysData:  # kind of C structure
    """All data used for signal processing and display."""

    chargerAPIversion = 0
    carPlugged = False
    batteryLevel = 0    # % from Renault server car API
    batteryLimit = 0    # %
    solarPower = 0      # kw from Solar Inverter Cloud
    pvToGrid = 0        # kW from Solar Inverter Cloud
    chargePower = 0.0   # kW  from go-eCharger Wallbox
    currentL1 = 0       # A  from go-eCharger Wallbox
    voltageL1 = 0       # V  from go-eCharger Wallbox
    chargeActive = False  # from go-eCharger
    measuredPhases = 0  # 1 | 3 number of measuredPhases
    actPhases = 0       # actual charger psm setting (C_CHARGER_x_PHASE)
    actCurrSet = 0      # actual charger setting
    reqPhases = 0       # requested phase by user or PV situation
    calcPvCurrent_1P = 0  # calculated 1 phase current, limited to max. setting
    calcPvCurrent_3P = 0  # calculated 3 phase current, if pvToGrid > minimum 3 phase current
    setCurrent       = 0
    chargerState = "?"
    carState = "---"
    pvHoldTimer = timers.EcTimer()
    phaseHoldTimer = timers.EcTimer()
    scanTimer = timers.EcTimer()
    pvScanTimer = timers.EcTimer()
    carScanTimer = timers.EcTimer()
    carErrorCounter = 0 # increment if eror during car data read
    pvError = 0
    chargerError = 0

class ChargeModes:  # kind of enum
    """Constants defining system state."""
    UNPLUGGED = 0
    IDLE = 1
    PV_INIT = 2
    PV_EXEC = 3
    FORCE_REQUEST = 4
    FORCED = 5
    STOPPED = 6
    EXTERN = 7
    LIMIT_REACHED = 8
    CAR_ERROR = 9
    CHARGER_ERROR = 10
    PV_ERROR = 11

sysData = SysData()

def processChargerData(sysData):
    """
    Converts charger data into sysData format
    :param sysData: data record similar to C structure
    :return: updated sysData
    """
    chargerData = charge.get_charger_data()
    print('Charger Data:', chargerData)
    if(chargerData['statusCode'] != 200):
        sysData.chargerError = chargerData['statusCode']
        return sysData
    else:
        sysData.chargerError = 0

    sysData.chargerAPIversion = chargerData['apiVer']
    sysData.carPlugged = False
    sysData.chargePower = 0
    if int(chargerData['car']) > 1: # car is plugged
        sysData.carPlugged = True
        if sysData.chargerAPIversion == 1:
            sysData.chargePower = chargerData['nrg'][11] / 100  # original value is in 10W
            sysData.currentL1 = chargerData['nrg'][4] / 10      # original alue is in 0.1A
            if chargerData['nrg'][4] > 10: sysData.chargeActive = True
            else: sysData.chargeActive = False
        else:  # API V2
            sysData.chargePower = chargerData['nrg'][11] / 1000 # original value is in W
            sysData.actPhases = chargerData['psm']
            sysData.currentL1 = chargerData['nrg'][4]     # original value is in 1A
            if chargerData['frc'] == 2: sysData.chargeActive = True # True while charging
            else: sysData.chargeActive = False

        sysData.voltageL1 = chargerData['nrg'][0]
        if chargerData['nrg'][6] > 1:  # current on L3, if charging with 3 measuredPhases
            sysData.measuredPhases = 3
        else:
            sysData.measuredPhases = 1

        sysData.actCurrSet = chargerData['amp']

    sysData.chargerState = const.C_CHARGER_STATUS_TEXT[int(chargerData['car'])]
    return sysData


def calcChargeCurrent(sysData, chargeMode, maxCurrent_1P, minCurrent_3P):
    """
     Calculate optimal charge current depending on solar power

    :param sysData:         data record similar to C structure
    :param chargeMode:
    :param maxCurrent_1P:   [A] upper limit for 1 phase
    :param minCurrent_3P:   [A] minimum used for switch overr to 3 phases
    :return sysData:        updatad data record
    """

    calc_free_current = 0

    # todo: correct for external charge: calc depending on chargeMode AND pvToGrid

    if chargeMode == ChargeModes.IDLE:
        newPower = sysData.pvToGrid - const.C_PV_MIN_REMAIN
    else:
        newPower = sysData.chargePower + sysData.pvToGrid - const.C_PV_MIN_REMAIN  # calculation in kW

    if sysData.voltageL1 > 0:
        calc_free_current = newPower * 1000 / sysData.voltageL1  # calc_free_current ersetzen durch Power?

# TEST!!!    calc_free_current = 9

    sysData.calcPvCurrent_3P = 0
    sysData.calcPvCurrent_1P = 0
    sysData.setCurrent = 0
    if calc_free_current > maxCurrent_1P:  #
        sysData.calcPvCurrent_1P = int(maxCurrent_1P)  # limit 1 phase current
    else:
        sysData.calcPvCurrent_1P = int(calc_free_current)

    if calc_free_current >= (minCurrent_3P * 3):  # switch to 3 phase request
        sysData.calcPvCurrent_3P = int(calc_free_current / 3)
        sysData.reqPhases = const.C_CHARGER_3_PHASES
        sysData.setCurrent = sysData.calcPvCurrent_3P
    else:
        sysData.reqPhases = const.C_CHARGER_1_PHASE
        sysData.setCurrent = sysData.calcPvCurrent_1P

    return sysData


def evalChargeMode(chargeMode, sysData, settings):
    """ State machine depending on realtime data and user intervention

    :param chargeMode:  enum like construct defined as class ChargeModes
    :param sysData: C structure like record defined as class sysData
    :param settings: dictionary from PV_Manager.json file
    :return: processed charge mode
    """

    sysData.scanTimer.set(const.C_SYS_IDLE_SCAN_TIME)  # sets the cyclic timing
    new_chargeMode = chargeMode  #stay in mode if nothing happened
    pvSettings = settings['pv']
    manualSettings = settings['manual']
    pvAllow3phases = pvSettings['allow_3_phases']

######## Cyclic Suppport Functions
#### Get Charger data
    sysData = processChargerData(sysData)
    if sysData.chargerError == 0:
        if sysData.carPlugged == False:
            chargeMode = ChargeModes.IDLE
            new_chargeMode = ChargeModes.UNPLUGGED
    else:
        chargeMode = ChargeModes.CHARGER_ERROR

#### Read battery level from car data
    if sysData.carScanTimer.read() == 0:
        sysData.carScanTimer.set(const.C_SYS_CAR_CLOCK)
        carData = access.ec_GetCarData()
        print('Car data:', carData)
        sysData.batteryLevel = carData['batteryLevel']
        if sysData.batteryLevel < 0:
            sysData.carErrorCounter = sysData.carErrorCounter + 1
            print('ERROR Reading Car Data, count =', sysData.carErrorCounter)
        else:
            sysData.carErrorCounter = 0

#### Read Solar data and charge decision
    if sysData.pvScanTimer.read() == 0:
        sysData.pvScanTimer.set(const.C_SYS_PV_CLOCK)
        pvData = access.ec_GetPVData(tout=20)
        if pvData['statusCode'] == 200:
            sysData.pvError = 0
            sysData.pvToGrid = round(pvData['PowerToGrid'], 1)
            sysData.solarPower = round(pvData['pvPower'], 1)
            sysData = calcChargeCurrent(sysData, chargeMode, pvSettings['max_1_Ph_current'],
                                        pvSettings['min_3_Ph_current'])
            if chargeMode == ChargeModes.IDLE:
                if sysData.calcPvCurrent_1P >= const.C_CHARGER_MIN_CURRENT:
                    if sysData.batteryLevel > 0:  # no error condition
                        if sysData.batteryLevel < sysData.batteryLimit:
                            chargeMode = ChargeModes.PV_EXEC  # set new state
        else:
            sysData.pvError = sysData.pvError + 1

    if chargeMode == ChargeModes.PV_EXEC:
        new_chargeMode = chargeMode  # stay in mode

        #### charge end ctriteria
        if sysData.batteryLevel >= sysData.batteryLimit \
                                or sysData.calcPvCurrent_1P < const.C_CHARGER_MIN_CURRENT:
            charge.stop_charging()
            charge.set_phase(const.C_CHARGER_1_PHASE)
            sysData.chargeActive = False
            new_chargeMode = ChargeModes.IDLE

        #### charging process control
        else:
            if sysData.actPhases == sysData.reqPhases:
                if sysData.actCurrSet != sysData.setCurrent:
                    charge.set_current(sysData.setCurrent)
                if sysData.chargeActive == False:
                    pv_hold = sysData.pvHoldTimer.read()
                    if pv_hold == 0:
                        charge.start_charging()
                        sysData.pvHoldTimer.set(const.C_SYS_MIN_PV_HOLD_TIME)
                    else:
                        print("PV hold time active ", pv_hold, "sec")
            else:  # initiate phase switch
                if sysData.phaseHoldTimer.read() == 0:
                    sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)
                    charge.stop_charging()
                    charge.set_phase(sysData.reqPhases)
                else:
                    print('waiting for phase switch')

#### handle manual start
    elif chargeMode == ChargeModes.FORCE_REQUEST:
        if sysData.batteryLevel < manualSettings['chargeLimit']:
            if manualSettings['3_phases']:
                sysData.reqPhases = const.C_CHARGER_3_PHASES
            else:
                sysData.reqPhases = const.C_CHARGER_1_PHASE

            if sysData.phaseHoldTimer.read() == 0:
                if sysData.actPhases != sysData.reqPhases:  # phase switch requested?
                    charge.set_phase(sysData.reqPhases)
                    sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)

                charge.set_current(manualSettings['currentSet'])
                charge.start_charging()
                new_chargeMode = ChargeModes.FORCED
            else:
                print('Phase change request -> wait, hold time', sysData.phaseHoldTimer.read())
        else:
            new_chargeMode = ChargeModes.IDLE
            sysData.chargeActive = False

    elif chargeMode == ChargeModes.FORCED:
        if sysData.batteryLevel >= manualSettings['chargeLimit']:
            new_chargeMode = ChargeModes.IDLE
            print('CHARGE OFF, manual limit reached')
            charge.stop_charging()
            sysData.chargeActive = False
            charge.set_phase(const.C_CHARGER_1_PHASE)

    elif chargeMode == ChargeModes.STOPPED:
        if sysData.phaseHoldTimer.read() == 0:
            new_chargeMode = ChargeModes.IDLE
            print('CHARGE STOPPED by user')
            charge.stop_charging()
            sysData.chargeActive = False
            charge.set_phase(const.C_CHARGER_1_PHASE)
        else:
            print('phaseHoldTimer waiting:', sysData.phaseHoldTimer.read())

    elif chargeMode == ChargeModes.IDLE:
        if sysData.chargePower > 1:
            new_chargeMode = ChargeModes.EXTERN

    elif chargeMode == ChargeModes.EXTERN:
        if sysData.chargePower < 1:
            charge.stop_charging(authenticate=1)  # dispite external stop, restore authenticate
            new_chargeMode = ChargeModes.IDLE

    elif chargeMode == ChargeModes.UNPLUGGED:
        if sysData.carPlugged == True:
            new_chargeMode = ChargeModes.IDLE


    if sysData.pvError  >= 2: # continue charging with old data below this limit
        if chargeMode == ChargeModes.PV_EXEC:
            charge.stop_charging()
            new_chargeMode = ChargeModes.IDLE

    if sysData.carErrorCounter >= 2:
        if chargeMode !=  ChargeModes.EXTERN:
            charge.stop_charging()
            new_chargeMode = ChargeModes.IDLE

    if sysData.chargerError == True:
            charge.stop_charging()  #try stopping charger anyway
            new_chargeMode = ChargeModes.IDLE


    return new_chargeMode


def writeLog(sysData, strMessage = "", strMode = "", logpath = const.C_LOG_PATH):
    '''
    Write logfile on event or mode change

    :param sysData: object of class SysData
    :param logpath: full path including filew nane
    :return: characters written
    '''

    now = datetime.now()
    date = now.date()
    strDate = date.strftime('%Y-%m-%d')
    strTime = now.strftime('%H:%M:%S')
    logDict = {"Date": strDate, "Time": strTime, "CarState": sysData.carState, "Actual Mode": strMode, "Message": strMessage,
               "BattLevel": sysData.batteryLevel, "Batt Limit": sysData.batteryLimit, "Pwr2Grid": sysData.pvToGrid,
               "Charge Power": sysData.chargePower, "Phases": sysData.actPhases, "Charge Active": sysData.chargeActive}
    if not os.path.isfile(logpath):
        header = []
        for keys in logDict:
            header.append(keys)
        logfile = open(logpath, 'w')
        writer = csv.DictWriter(logfile, header)
        chars = writer.writeheader()

    logfile = open(logpath, 'a', newline='')
    writer = csv.DictWriter(logfile,logDict)
    chars = writer.writerow(logDict)
    logfile.close()
    return chars
