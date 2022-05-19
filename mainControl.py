import evsGUI
import time
import os.path
import configparser as CP

import const
import access
import timers
import utils
import sysSettings
import popCharge
import popSettings

SIMULATE_PV_TO_GRID = 0

# restore window position
config = CP.ConfigParser()
window = evsGUI.window
window.finalize()  # activate window
config.read(const.C_INI_FILE)
if (config.has_option('Window', 'position_xy')):
    win_location = config['Window']['position_xy']
    win_location = eval(win_location)  # re-format to tuple(x,y)
else:  # last location will be stored at exit
    win_location = window.current_location()
x, y = win_location
window.move(x, y)

evsGUI.SetLED(window, '-LED_SOLAR-', 'grey')
evsGUI.SetLED(window, '-LED_FORCED-', 'grey')
evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')
evsGUI.SetLED(window, '-LED_CHARGER-', 'grey')
evsGUI.SetLED(window, '-LED_CAR-', 'grey')
evsGUI.SetLED(window, '-LED_PV-', 'grey')

ChargeModes = utils.ChargeModes

# create objects
chargeMode = ChargeModes.IDLE  # default
oldChargeMode = None  # used for detection of state transitions
sysData = utils.SysData
go_e = utils.charge
chargeLogTimer = timers.EcTimer()


# initial of module global variables
t100ms = 0
t1s = -1
ExecImmediate = False
pvData = None
pvChargeOn = False
chargeState = 0
exitApp = False
limit_pos = ''
limit = int(0)
limit_scale = 67 / 100
forceFlag = False
firstRun = True
messageTxt = ''



# use existing file or create one with default values
if os.path.isfile(const.C_DEFAULT_SETTINGS_FILE):
    settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
else:
    settings = sysSettings.defaultSettings
    sysSettings.writeSettings(const.C_DEFAULT_SETTINGS_FILE, settings)

def printMsg(item="", value=""):
    text = f'{item} {value}'
    window['-MESSAGE-'].update(text)
    return text

messageTxt = printMsg('Power ON')
utils.writeLog(sysData, strMessage=messageTxt, strMode=chargeMode)
go_e.stop_charging()

# ------------------------------------------------ this is the main control loop -------------------------------------
while not exitApp:
    # cyclic check for user action
    event, values = window.read(timeout=100)
    if event == 'Quit' or window.was_closed():
        go_e.stop_charging()
        messageTxt = "User Exit App"
        utils.writeLog(sysData, strMessage=messageTxt, strMode=chargeMode)
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
            sysData.batteryLimit = limit

    # MAIN LOOP ------------------------------------------------------------------------------------------------------
    # main time division for 1s base tick
    t100ms += 1
    if t100ms > 10:
        if ExecImmediate == True:  # todo: check handling of ExecImmediate
            t1s = -1
            ExecImmediate = False

        t1s += 1
        t100ms = 0
        print('.', end='')
        if t1s % 2 == 0:  # blink life sign
             if chargeMode == ChargeModes.CAR_ERROR:
                 evsGUI.SetLED(window, '-LED_MSG-', const.C_BLINK_ERROR_COLOR)
             else:
                 evsGUI.SetLED(window, '-LED_MSG-', const.C_BLINK_OK_COLOR)
        else:
            evsGUI.SetLED(window, '-LED_MSG-', 'grey')

        if sysData.scanTimer.read() == 0:
            chargeMode = utils.evalChargeMode(chargeMode, sysData, settings)

        if sysData.carPlugged and forceFlag == True:
            done = popCharge.popCharge(batteryLevel=sysData.batteryLevel, pop_location=window.current_location())
            if done:
                settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
                limit = int(settings['manual']['chargeLimit'])
                sysData.batteryLimit = limit
                chargeMode = ChargeModes.FORCE_REQUEST
                ExecImmediate = True
            forceFlag = False

        # ---------------------------------------- update display elements -------------------------------------------
        if firstRun:
            window['Force Charge'].update(disabled=False)
            window['Stop Charge'].update(disabled=False)
            limit = int(settings['pv']['chargeLimit'])
            sysData.batteryLimit = limit
            go_e.set_phase(1)
            firstRun = False


        limit_pos = int(limit_scale * limit) * ' ' + '▲'
        if sysData.batteryLevel >= limit:  # display as full / charge limit reached
            batt_color = (const.C_BATT_COLORS[4], '#9898A0')
            limit_color = 'green1'
        else:
            batt_color = (const.C_BATT_COLORS[(sysData.batteryLevel // 21)], '#9898A0')
            limit_color = 'white'


        # event driven displays
        if chargeMode != oldChargeMode:
#            oldChargeMode = chargeMode
            messageTxt = printMsg(const.C_MODE_TXT[chargeMode])
            utils.writeLog(sysData, messageTxt, chargeMode)

            if chargeMode == ChargeModes.PV_INIT or  chargeMode == ChargeModes.PV_EXEC:
                limit = int(settings['pv']['chargeLimit'])
                print('SOLAR CHARGE')
                evsGUI.SetLED(window, '-LED_SOLAR-', 'yellow')
                window['-chargeBar-'].update(bar_color=('yellow', '#9898A0'))

            elif chargeMode == ChargeModes.FORCED:
                limit = int(settings['manual']['chargeLimit'])
                limit_pos = int(limit_scale * limit) * ' ' + '▲'
                evsGUI.SetLED(window, '-LED_FORCED-', 'white')
                window['-chargeBar-'].update(bar_color=('white', '#9898A0'))

            elif chargeMode == ChargeModes.EXTERN:
                limit = 0
                print('EXTERN CHARGE')
                evsGUI.SetLED(window, '-LED_EXTERN-', 'blue')
                window['-chargeBar-'].update(bar_color=('blue', '#9898A0'))

            elif chargeMode == ChargeModes.IDLE or chargeMode == ChargeModes.UNPLUGGED:
                limit = int(settings['pv']['chargeLimit'])
                sysData.batteryLimit = limit
                limit_pos = int(limit_scale * limit) * ' ' + '▲ '
                print('IDLE, waiting for event ...')
                evsGUI.SetLED(window, '-LED_SOLAR-', 'grey')
                evsGUI.SetLED(window, '-LED_FORCED-', 'grey')
                evsGUI.SetLED(window, '-LED_EXTERN-', 'grey')
                if oldChargeMode == ChargeModes.PV_EXEC or chargeMode == ChargeModes.FORCED:
                    if sysData.batteryLevel >= limit:
                        messageTxt = printMsg(const.C_MODE_TXT[chargeMode] + ' Limit reached!')
                        utils.writeLog(sysData, messageTxt, chargeMode)

            elif chargeMode == ChargeModes.CAR_ERROR:
                messageTxt = printMsg(const.C_MODE_TXT[chargeMode] + 'Count =', sysData.carErrorCounter)
                utils.writeLog(sysData, messageTxt, chargeMode)

            oldChargeMode = chargeMode

        # Cyclic gui refresh
        # if sysData.batteryLevel >= limit:  # display as full / charge limit reached
        #     batt_color = (const.C_BATT_COLORS[4], '#9898A0')
        #     limit_color = 'green1'
        # else:
        #     batt_color = (const.C_BATT_COLORS[(sysData.batteryLevel // 21)], '#9898A0')
        #     limit_color = 'white'

        if sysData.chargerError:
            evsGUI.SetLED(window, '-LED_CHARGER-', 'red')
            print('ERROR reading charger, code:',sysData.chargerError)
        else:
            evsGUI.SetLED(window, '-LED_CHARGER-', 'light green')

        if sysData.pvError:
            evsGUI.SetLED(window, '-LED_PV-', 'red')
        else:
            evsGUI.SetLED(window, '-LED_PV-', 'light green')

        if sysData.carPlugged == True:
            if sysData.carErrorCounter > 0:
                evsGUI.SetLED(window, '-LED_CAR-', 'red')
                sysData.carState = "Error reading car"
            else:
                evsGUI.SetLED(window, '-LED_CAR-', 'light green')
                if chargeMode == ChargeModes.IDLE:
                    sysData.carState = "Car ready"

        else:
            evsGUI.SetLED(window, '-LED_CAR-', 'grey')
            sysData.carState = "Car unplugged"

        if sysData.chargeActive == True:
            if chargeLogTimer.read() == 0:
                sysData.carState = "CAR CHARGING"
                messageTxt = printMsg(const.C_MODE_TXT[chargeMode])
                utils.writeLog(sysData, messageTxt, chargeMode)
                chargeLogTimer.set(const.C_SYS_LOG_INTERVAL)

        window['-battBar-'].update(current_count=sysData.batteryLevel)
        window['-battBar-'].update(bar_color=batt_color)

        window['-LIMIT_VAL-'].update(limit_pos)
        window['-LIMIT_VAL-'].update(text_color=limit_color)
        window['-limit-'].update(limit)
        window['-batt-'].update(sysData.batteryLevel)
        window['-CHARGE_STATE-'].update(sysData.carState)

        window['-solarBar-'].update(current_count=sysData.solarPower)
        window['-solar-'].update(sysData.solarPower)

        window['-chargeBar-'].update(current_count=int(sysData.chargePower))
        window['-charge-'].update(sysData.chargePower)
        window['-chargeCurr-'].update(sysData.currentL1)
        window['-measuredPhases-'].update(sysData.measuredPhases)

        window['-toGridBar-'].update(current_count=sysData.pvToGrid)
        window['-toGrid-'].update(sysData.pvToGrid)


# store last window position
if (event != window.was_closed()):
    win_location = window.current_location()
    iniFile = open(const.C_INI_FILE, 'w')
    config['Window'] = {'position_xy': win_location}
    config.write(iniFile)
    iniFile.close()

window.close()
