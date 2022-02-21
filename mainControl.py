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

ChargeModes = pv_utils.ChargeModes

# create objects
chargeMode = ChargeModes.IDLE  # default
oldChargeMode = chargeMode  # used for detection of state transitions

sysData = pv_utils.SysData
#sysData.pvHoldTimer = pv_utils.EcTimer()
#sysData.phaseHoldTimer = pv_utils.EcTimer()

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




def printMsg(text=''):
    window['-MESSAGE-'].update(text)


#sysData.phaseHoldTimer = pv_utils.EcTimer()
#sysData.pvHoldTimer = pv_utils.EcTimer()
# sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)  # prevent rapid phase switch

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
        if t1s % 2 == 0:  #blink life sign
            evsGUI.SetLED(window, '-LED_MSG-', '#CCCCCC')
        else:
            evsGUI.SetLED(window, '-LED_MSG-', 'grey')

        # read charger data
        if (t1s % const.C_SYS_CHARGER_CLOCK) == 0 or ExecImmediate == True:
            window.finalize()
            printMsg('Reading charger data')
            print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
            pv_utils.ecGetChargerData(sysData)
#            ExecImmediate = False

        # read solar data
        if (t1s % const.C_SYS_PV_CLOCK) == 0 or ExecImmediate == True:
            print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
            window.finalize()
            printMsg('Reading photovoltaic data')
            pvData = access.ec_GetPVData(tout=20)
            if SIMULATE_PV_TO_GRID > 0:
                pvData['PowerToGrid'] = SIMULATE_PV_TO_GRID
            sysData.solarPower = round(pvData['pvPower'], 1)
            sysData.pvToGrid = round(pvData['PowerToGrid'], 1)
            if sysData.carPlugged:
#                chargeMode = evalChargeMode(chargeMode, sysData, settings)
                ExecImmediate = False

        # read car data
        if (t1s % const.C_SYS_CAR_CLOCK) == 0:
            #            ExecImmediate = False
            if True: # sysData.carPlugged:
                print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
                window.finalize()
                printMsg('Reading car data')
                carData = access.ec_GetCarData()
                print('Car data:', carData)
                batteryLevel = carData['batteryLevel']
                sysData.batteryLevel = carData['batteryLevel']

        if sysData.carPlugged and forceFlag == True:
            done = popCharge.popCharge(batteryLevel=batteryLevel)
            if done:
                settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
                limit = int(settings['manual']['chargeLimit'] * 67 / 100)
                chargeMode = ChargeModes.FORCE_REQUEST
                ExecImmediate = True
            forceFlag = False

        if sysData.carPlugged:
            chargeMode = pv_utils.evalChargeMode(chargeMode, sysData, settings)

    # ---------------------------------------- update display elements -------------------------------------------
    if sysData.carPlugged: # and t1s == 1:  # first run
        window['Force Charge'].update(disabled=False)
        window['Stop Charge'].update(disabled=False)
        limit = int(settings['pv']['chargeLimit'] * 67 / 100)
        limit_pos = limit * ' ' + '▲'

    if chargeMode != oldChargeMode or ExecImmediate == True:
        oldChargeMode = chargeMode
        if chargeMode == ChargeModes.PV:
            limit_pos = limit * ' ' +  '▲'
            printMsg('Switching to SOLAR charge ...')
            print('SOLAR CHARGE')
            evsGUI.SetLED(window, '-LED_SOLAR-', 'yellow')
            window['-chargeBar-'].update(bar_color= ('yellow','#9898A0'))

        elif chargeMode == ChargeModes.FORCED:
            limit = int(settings['pv']['chargeLimit'] * 67 / 100)
            limit_pos = limit * ' ' +  '▲'
#            print('FORCED CHARGE')
            printMsg('Switching to FORCED charg ...')
            evsGUI.SetLED(window, '-LED_FORCED-', 'white')
            window['-chargeBar-'].update(bar_color= ('white','#9898A0'))

        elif chargeMode == ChargeModes.EXTERN:
            limit_pos = ''
            print('EXTERN CHARGE')
            printMsg('EXTERNAL CHARGE was initiated')
            evsGUI.SetLED(window, '-LED_EXTERN-', 'blue')
            window['-chargeBar-'].update(bar_color= ('blue','#9898A0'))

        elif chargeMode == ChargeModes.IDLE:
            limit = int(settings['manual']['chargeLimit'] * 67 / 100)
            limit_pos = limit * ' ' + '▲'
            print('IDLE, waiting for event')
            evsGUI.SetLED(window, '-LED_SOLAR-', 'grey')
            evsGUI.SetLED(window, '-LED_FORCED-', 'grey')
            evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')

    # display limit sign after first run
    if (t1s > 0):
        limit_pos = limit * ' ' + '▲'  # place limit sign

    window['-battBar-'].update(current_count=sysData.batteryLevel)
    window['-LIMIT_VAL-'].update(limit_pos)
    window['-batt-'].update(sysData.batteryLevel)
    window['-CHARGE_STATE-'].update(sysData.carState)

    window['-solarBar-'].update(current_count=sysData.solarPower)
    window['-solar-'].update(sysData.solarPower)

    window['-chargeBar-'].update(current_count=int(sysData.chargePower / 1000))
    window['-charge-'].update(sysData.chargePower / 1000)
    window['-chargeCurr-'].update(sysData.currentL1)
    window['-measuredPhases-'].update(sysData.measuredPhases)

    window['-toGridBar-'].update(current_count=sysData.pvToGrid)
    window['-toGrid-'].update(sysData.pvToGrid)

    if t1s == 0: # place LEDs on first run
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
