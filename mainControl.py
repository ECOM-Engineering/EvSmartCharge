import evsGUI
import time
import os.path

import const
import access
import pv_utils
import sysSettings
import popCharge
import popSettings

window=evsGUI.window

SIMULATE_PV_TO_GRID = False

class ChargeModes:  # kind of enum
    """Constants defining system state."""
    IDLE = 0
    PV = 1
    FORCED = 2
    EXTERN = 3
    STOPPED = 4
    FORCE_REQUEST = 5


# create objects
chargeMode = ChargeModes.IDLE  # default
oldChargeMode = chargeMode  # used for detection of state transitions

sysData = pv_utils.SysData
sysData.pvHoldTimer = pv_utils.EcTimer()
sysData.phaseHoldTimer = pv_utils.EcTimer()

# initial of module global variables
t100ms = 0
t1s = -1
ExecImmediate = False
pvData = None
pvChargeOn = False
chargeState = 0
exitApp = False
batteryLevel = 0
limit_pos = ''
limit = 0
forceFlag = False


if os.path.isfile(const.C_DEFAULT_SETTINGS_FILE):
    settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
else:
    settings = sysSettings.defaultSettings
    sysSettings.writeSettings(const.C_DEFAULT_SETTINGS_FILE, settings)


def evalChargeMode(chargeMode, sysData, settings):
    """ State machine depending on realtime data and user intervention

    :param chargeMode:  enum like construct defined as class ChargeModes
    :param sysData: C structure like record defined as class SysData
    :param settings: dictionary from PV_Manager.json file
    :return: processed charge mode
    """

    pvSettings = settings['pv']
    manualSettings = settings['manual']
    pvAllow3phases = pvSettings['3_phases']

    pv_utils.calcChargeCurrent(sysData,
                               pvSettings['max_1_Ph_current'], pvSettings['min_3_Ph_current'])
    freeSolarCurrent = sysData.calcPvCurrent_1P
    print('CHARGE-MODE ACTUAL:', chargeMode, end='')

    if chargeMode == ChargeModes.FORCE_REQUEST:
        if sysData.batteryLevel < manualSettings['chargeLimit']:
            if manualSettings['3_phases'] == True:
                sysData.reqPhases = const.C_CHARGER_3_PHASES
            else:
                sysData.reqPhases = const.C_CHARGER_1_PHASE

            if sysData.phaseHoldTimer.read() == 0:
                access.ecSetChargerData("acs", "0")  # authenticate

                if sysData.actPhases != sysData.reqPhases:  # phase switch requested?
                    access.ecSetChargerData("psm", sysData.reqPhases)
                    sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)

                access.ecSetChargerData("amp", str(manualSettings['currentSet']))
                access.ecSetChargerData("frc", "2")  # ON
                chargeMode = ChargeModes.FORCED
            else:
                print('Phase change request -> wait, hold time', sysData.phaseHoldTimer.read())
        else:
            chargeMode = ChargeModes.IDLE

    if chargeMode == ChargeModes.FORCED:
        if sysData.batteryLevel >= manualSettings['chargeLimit']:
            chargeMode = ChargeModes.IDLE
            print('CHARGE OFF, manual limit reached')
            access.ecSetChargerData("acs", "0", 5)  # authentication
            access.ecSetChargerData("frc", "1", tout=10)  # OFF
            access.ecSetChargerData("psm", const.C_CHARGER_1_PHASE, tout=10)

    #    elif chargeMode == ChargeModes.STOPPED:
    if chargeMode == ChargeModes.STOPPED:
        chargeMode = ChargeModes.IDLE
        print('CHARGE STOPPED by user')
        access.ecSetChargerData("frc", "1", tout=10)  # OFF
        access.ecSetChargerData("psm", const.C_CHARGER_1_PHASE, tout=10)  #
        access.ecSetChargerData("acs", "1", 5)  # authentication required

    #    elif chargeMode == ChargeModes.IDLE:
    if chargeMode == ChargeModes.IDLE:
        if freeSolarCurrent >= const.C_CHARGER_MIN_CURRENT and sysData.batteryLevel < pvSettings['chargeLimit']:
            if sysData.pvHoldTimer.read() == 0:
                sysData.pvHoldTimer.set(const.C_SYS_MIN_PV_HOLD_TIME)
                chargeMode = ChargeModes.PV
                print('Charge ON. Current', int(freeSolarCurrent))
                access.ecSetChargerData("acs", "0", tout=10)  # authenticate
                access.ecSetChargerData("amp", str(int(freeSolarCurrent)))
                access.ecSetChargerData("frc", "2", tout=10)  # ON

        elif sysData.chargePower > 1000:
            chargeMode = ChargeModes.EXTERN

    #    elif chargeMode == ChargeModes.PV:
    if chargeMode == ChargeModes.PV:
        if freeSolarCurrent < const.C_CHARGER_MIN_CURRENT or sysData.batteryLevel >= pvSettings['chargeLimit']:
            if sysData.pvHoldTimer.read() == 0:
                chargeMode = ChargeModes.IDLE
                print('Charge OFF')
                access.ecSetChargerData("frc", "1", tout=10)  # OFF
                access.ecSetChargerData("acs", "1", 5)  # authentication required
                sysData.pvHoldTimer.set(const.C_SYS_MIN_PV_HOLD_TIME)
        else:
            access.ecSetChargerData("amp", str(freeSolarCurrent))  # addpt to actual level and continue  PV
            print('Current 1P:', sysData.calcPvCurrent_1P, ' 3P: ', sysData.calcPvCurrent_3P, 'PhaseRequest',
                  sysData.reqPhases)
            if sysData.phaseHoldTimer.read() == 0 and pvAllow3phases:
                if sysData.actPhases != sysData.reqPhases:  # phase switch requested?
                    access.ecSetChargerData("psm", sysData.reqPhases)
                    # SysData.actPhases = SysData.reqPhases  #should be done at read charger data
                    sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)
    elif chargeMode == ChargeModes.EXTERN:
        if sysData.chargePower == 0:
            chargeMode = ChargeModes.IDLE
            print('External Charge OFF')

    print(' NEW:', chargeMode)
    return chargeMode


sysData.phaseHoldTimer = pv_utils.EcTimer()
sysData.pvHoldTimer = pv_utils.EcTimer()
sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)  # prevent early phase switch

# ------------------------------------------------ this is the main control loop -------------------------------------
while not exitApp:
    # cyclic check for user action
    event, values = window.read(timeout=100)
    if event == 'Quit' or window.was_closed():
        access.ecSetChargerData("frc", "1", 5)  # switch charging OFF
        access.ecSetChargerData("psm", const.C_CHARGER_1_PHASE)
        access.ecSetChargerData("acs", "1", 5)  # authentication required
        exitApp = True
    elif event == 'Force Charge':
        forceFlag = True

    elif event == 'Stop Charge':
        if chargeMode == ChargeModes.FORCED or chargeMode == ChargeModes.EXTERN:
            chargeMode = ChargeModes.STOPPED
            ExecImmediate = True
    elif event == 'PV-Settings':
        done = popSettings.popSettings(batteryLevel=batteryLevel)
        if done:
            settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
            limit = int(settings['pv']['chargeLimit'] * 67 / 100)


    # MAIN LOOP ------------------------------------------------------------------------------------------------------
    # main time division for 1s base tick
    t100ms += 1
    if t100ms > 10:
        t1s += 1
        t100ms = 0
        print('.', end='')
        # read charger data
        if (t1s % const.C_SYS_CHARGER_CLOCK) == 0 or ExecImmediate == True:
            print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
            pv_utils.ecGetChargerData(sysData)
            ExecImmediate = False

        # read car data
        if (t1s % const.C_SYS_CAR_CLOCK) == 0:
            #            ExecImmediate = False
            if True: # sysData.carPlugged:
                print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
                carData = access.ec_GetCarData()
                print('Car data:', carData)
                batteryLevel = carData['batteryLevel']
                sysData.batteryLevel = carData['batteryLevel']

        # read solar data
        if (t1s % const.C_SYS_PV_CLOCK) == 0:
            print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
            pvData = access.ec_GetPVData(tout=20)
            if SIMULATE_PV_TO_GRID > 0:
                pvData['PowerToGrid'] = SIMULATE_PV_TO_GRID
            sysData.solarPower = round(pvData['pvPower'], 1)
            sysData.pvToGrid = round(pvData['PowerToGrid'], 1)
            if sysData.carPlugged:
                chargeMode = evalChargeMode(chargeMode, sysData, settings)

        if sysData.carPlugged and forceFlag == True:
            done = popCharge.popCharge(batteryLevel=batteryLevel)
            if done:
                settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
                limit = int(settings['manual']['chargeLimit'] * 67 / 100)
                chargeMode = ChargeModes.FORCE_REQUEST
                ExecImmediate = True
            forceFlag = False

    # ---------------------------------------- update display elements -------------------------------------------
    if sysData.carPlugged and t1s == 1:  # first run
        window['Force Charge'].update(disabled=False)
        window['Stop Charge'].update(disabled=False)
        limit = int(settings['pv']['chargeLimit'] * 67 / 100)
        limit_pos = limit * ' ' + '▲'

    if chargeMode != oldChargeMode:
        oldChargeMode = chargeMode
        if chargeMode == ChargeModes.PV:
            limit_pos = limit * ' ' +  '▲'
            print('SOLAR CHARGE')
            evsGUI.SetLED(window, '-LED_SOLAR-', 'yellow')

        elif chargeMode == ChargeModes.FORCED:
            limit = int(settings['pv']['chargeLimit'] * 67 / 100)
            limit_pos = limit * ' ' +  '▲'
            print('FORCED CHARGE')
            evsGUI.SetLED(window, '-LED_FORCED-', 'blue')

        elif chargeMode == ChargeModes.EXTERN:
            limit_pos = ''
            print('EXTERN CHARGE')
            evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')

        elif chargeMode == ChargeModes.IDLE:
            limit = int(settings['manual']['chargeLimit'] * 67 / 100)
            limit_pos = limit * ' ' + '▲'
            print('IDLE, waiting for event')
            evsGUI.SetLED(window, '-LED_SOLAR-', 'grey')
            evsGUI.SetLED(window, '-LED_FORCED-', 'grey')
            evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')

    # display limit sign after first run
    if (t1s > 0):
        limit_pos = limit * ' ' + '▲'
    window['-battBar-'].UpdateBar(sysData.batteryLevel)
    window['-LIMIT_VAL-'].update(limit_pos)
    window['-batt-'].update(sysData.batteryLevel)
    window['-CHARGE_STATE-'].update(sysData.carState)

    evsGUI.solar_bar.UpdateBar(sysData.solarPower)
    window['-solar-'].update(sysData.solarPower)

    evsGUI.charge_bar.UpdateBar(sysData.chargePower / 1000)
    window['-charge-'].update(sysData.chargePower / 1000)
    window['-chargeCurr-'].update(sysData.currentL1)
    window['-measuredPhases-'].update(sysData.measuredPhases)

    evsGUI.toGrid_bar.UpdateBar(sysData.pvToGrid)
    window['-toGrid-'].update(sysData.pvToGrid)

    if t1s == 0:
        evsGUI.SetLED(window, '-LED_SOLAR-', 'grey')
        evsGUI.SetLED(window, '-LED_FORCED-', 'grey')
        evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')


    # if sysData.carPlugged:
    #     evsGUI.SetLED(window, '-LED_BAT', 'spring green')
    # else:
    #     evsGUI.SetLED(window, '-LED_BAT', 'grey')
    #     evsGUI.SetLED(window, '-LED_CHARGE-', 'grey')

# done with loop... need to destroy the window as it's still open
window.close()
