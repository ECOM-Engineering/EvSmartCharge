import evsGUI
import time
import os.path
import configparser as CP

import const
import access
import pv_utils
import sysSettings
import popCharge
import popSettings

# todo: reaction o missing car conection
# todo: Car data connection error handling

SIMULATE_PV_TO_GRID = 0

# restore window position
config = CP.ConfigParser()
window = evsGUI.window
window.finalize()  # activate window
config.read(const.C_INI_FILE)
if (config.has_option('Window', 'position_xy')):
    win_location = config['Window']['position_xy']
    win_location = eval(win_location)  # re-format to tuple(x,y)
else:
    win_location = window.current_location()
x, y = win_location
window.move(x, y)

ChargeModes = pv_utils.ChargeModes

# create objects
chargeMode = ChargeModes.IDLE  # default
oldChargeMode = None  # used for detection of state transitions

sysData = pv_utils.SysData
# sysData.pvHoldTimer = pv_utils.EcTimer()
# sysData.phaseHoldTimer = pv_utils.EcTimer()

# initial of module global variables
t100ms = 0
t1s = -1
ExecImmediate = False
pvData = None
pvChargeOn = False
chargeState = 0
exitApp = False
limit_pos = ''
limit = 0
limit_scale = 67 / 100
forceFlag = False
firstRun = True

# use existing file or create one with default values
if os.path.isfile(const.C_DEFAULT_SETTINGS_FILE):
    settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
else:
    settings = sysSettings.defaultSettings
    sysSettings.writeSettings(const.C_DEFAULT_SETTINGS_FILE, settings)


def printMsg(text=''):
    window['-MESSAGE-'].update(text)


# sysData.phaseHoldTimer = pv_utils.EcTimer()
# sysData.pvHoldTimer = pv_utils.EcTimer()
# sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)  # prevent rapid phase switch

# ------------------------------------------------ this is the main control loop -------------------------------------
while not exitApp:
    # cyclic check for user action
    event, values = window.read(timeout=100)
    if event == 'Quit' or window.was_closed():
        access.ecSetChargerData("frc", "1", 5)  # switch charging OFF
        access.ecSetChargerData("psm", const.C_CHARGER_1_PHASE)
        access.ecSetChargerData("acs", "1", 5)  # authentication required --> no automatic charge start at car plugging
        exitApp = True

    elif event == 'Force Charge':
        forceFlag = True

    elif event == 'Stop Charge':
        if chargeMode == ChargeModes.FORCED or chargeMode == ChargeModes.EXTERN:
            chargeMode = ChargeModes.STOPPED
            ExecImmediate = True

    elif event == 'PV-Settings':
        done = popSettings.popSettings(batteryLevel=sysData.batteryLevel, pop_location=window.current_location())
        if done:
            settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
            limit = settings['pv']['chargeLimit']

    # MAIN LOOP ------------------------------------------------------------------------------------------------------
    # main time division for 1s base tick
    t100ms += 1
    if t100ms > 10:
        if t1s == -1:  # first run
            evsGUI.SetLED(window, '-LED_SOLAR-', 'grey')
            evsGUI.SetLED(window, '-LED_FORCED-', 'grey')
            evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')

        if ExecImmediate == True:
            t1s = -1
            ExecImmediate = False

        t1s += 1
        t100ms = 0
        print('.', end='')
        if t1s % 2 == 0:  # blink life sign
            evsGUI.SetLED(window, '-LED_MSG-', '#CCCCCC')
        else:
            evsGUI.SetLED(window, '-LED_MSG-', 'grey')

        # read charger data
        if (t1s % const.C_SYS_CHARGER_CLOCK) == 0:
            #            window.finalize()
            printMsg('Reading charger data')
            print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
            sysData = pv_utils.ecGetChargerData(sysData)
        #            ExecImmediate = False

        # read solar data
        if (t1s % const.C_SYS_PV_CLOCK) == 0:
            print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
            printMsg('Reading photovoltaic data')
            #            window.finalize()
            pvData = access.ec_GetPVData(tout=20)
            if SIMULATE_PV_TO_GRID > 0:
                pvData['PowerToGrid'] = SIMULATE_PV_TO_GRID
            sysData.solarPower = round(pvData['pvPower'], 1)
            sysData.pvToGrid = round(pvData['PowerToGrid'], 1)

            if not firstRun:
                ExecImmediate = False

                # Renault server is often down or produces bad or uncomplete json data
                # todo: handle this in pv_utils.evalChargeMode()!!!

                if sysData.batteryLevel < 0:  # todo reaction on multiple errors
                    chargeMode = ChargeModes.CAR_ERROR
                    sysData.carErrorCounter += 1
                    printMsg('ERROR Reading Car Data, count ='  + str(sysData.carErrorCounter))
                    if sysData.carErrorCounter > const.C_MAX_CAR_CONNECTION_ERRORS:
                        printMsg('ERROR Reading Car Data, swithching OFF charger')
                        access.ecSetChargerData("frc", "1")  # switch charging OFF
                        access.ecSetChargerData("psm", const.C_CHARGER_1_PHASE)
                        access.ecSetChargerData("acs", "1")  # authentication required --> no automatic charge start at car plugging
                else:
                    chargeMode = pv_utils.evalChargeMode(chargeMode, sysData, settings)
                    sysData.carErrorCounter = 0

                    # read car data
        if (t1s % const.C_SYS_CAR_CLOCK) == 0:
            #            ExecImmediate = False
            if sysData.carPlugged:
                print('\n' + time.strftime("%y-%m-%d  %H:%M:%S"))
                window.finalize()
                printMsg('Reading car data')
                carData = access.ec_GetCarData()
                print('Car data:', carData)
                sysData.batteryLevel = carData['batteryLevel']

            else:
                sysData.batteryLevel = 0

        if sysData.carPlugged and forceFlag == True:
            done = popCharge.popCharge(batteryLevel=sysData.batteryLevel, pop_location=window.current_location())
            if done:
                settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
                limit = int(settings['manual']['chargeLimit'])
                chargeMode = ChargeModes.FORCE_REQUEST
                ExecImmediate = True
            forceFlag = False

        # if sysData.carPlugged:
        #     chargeMode = pv_utils.evalChargeMode(chargeMode, sysData, settings)

        # ---------------------------------------- update display elements -------------------------------------------
        #    if sysData.carPlugged and t1s == 0:  # first run
        if firstRun:
            window['Force Charge'].update(disabled=False)
            window['Stop Charge'].update(disabled=False)
            firstRun = False

        if limit > 0:
            limit_pos = int(limit_scale * limit) * ' ' + '▲'

        if chargeMode != oldChargeMode:
            oldChargeMode = chargeMode
            if chargeMode == ChargeModes.PV:
                limit = int(settings['pv']['chargeLimit'])
                printMsg('Switching to SOLAR charge ...')
                print('SOLAR CHARGE')
                evsGUI.SetLED(window, '-LED_SOLAR-', 'yellow')
                window['-chargeBar-'].update(bar_color=('yellow', '#9898A0'))

            elif chargeMode == ChargeModes.FORCED:
                limit = int(settings['manual']['chargeLimit'])
                limit_pos = int(limit_scale * limit) * ' ' + '▲'
                #            print('FORCED CHARGE')
                printMsg('Switching to FORCED charg ...')
                evsGUI.SetLED(window, '-LED_FORCED-', 'white')
                window['-chargeBar-'].update(bar_color=('white', '#9898A0'))

            elif chargeMode == ChargeModes.EXTERN:
                limit = 0
                print('EXTERN CHARGE')
                printMsg('EXTERNAL CHARGE was initiated')
                evsGUI.SetLED(window, '-LED_EXTERN-', 'blue')
                window['-chargeBar-'].update(bar_color=('blue', '#9898A0'))

            elif chargeMode == ChargeModes.IDLE or chargeMode == ChargeModes.UNPLUGGED:
                limit = int(settings['pv']['chargeLimit'])
                limit_pos = int(limit_scale * limit) * ' ' + '▲'
                print('IDLE, waiting for event')
                evsGUI.SetLED(window, '-LED_SOLAR-', 'grey')
                evsGUI.SetLED(window, '-LED_FORCED-', 'grey')
                evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')

        if sysData.batteryLevel >= limit - 2:  # display as full / charge limit reached
            batt_color = (const.C_BATT_COLORS[4], '#9898A0')
        else:
            batt_color = (const.C_BATT_COLORS[(sysData.batteryLevel // 21)], '#9898A0')

        window['-battBar-'].update(current_count=sysData.batteryLevel)
        window['-battBar-'].update(bar_color=batt_color)

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

    # if sysData.carPlugged:
    #     evsGUI.SetLED(window, '-LED_BAT', 'spring green')
    # else:
    #     evsGUI.SetLED(window, '-LED_BAT', 'grey')
    #     evsGUI.SetLED(window, '-LED_CHARGE-', 'grey')

if (event != window.was_closed()):
    win_location = window.current_location()
    iniFile = open(const.C_INI_FILE, 'w')
    config['Window'] = {'position_xy': win_location}
    config.write(iniFile)
    iniFile.close()

window.close()
