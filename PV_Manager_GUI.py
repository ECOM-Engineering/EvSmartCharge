import time

import PySimpleGUI as sg
import const
import access
import pv_utils
import sysSettings
import popCharge
import popSettings

sg.SetOptions(button_element_size=(11, 1), auto_size_buttons=False, font=('Arial', 10))

batLevelBar = sg.ProgressBar(100, orientation='h', size=(20, 14), key='-battBar-', bar_color=('spring green', 'grey'))
chargePwrBar = sg.ProgressBar(const.C_CHARGER_MAX_POWER, orientation='h', size=(20, 14),
                              key='-chargeBar-', bar_color=('blue', 'grey'))
solarPwrBar = sg.ProgressBar(6, orientation='h', size=(20, 14), key='-solarBar-', bar_color=('yellow', 'grey'))
solarPwr2GridBar = sg.ProgressBar(6, orientation='h', size=(20, 14), key='-toGridBar-', bar_color=('yellow', 'grey'))


battDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-batt-')
solarDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-solar-')
chargeDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-charge-')
chargeCurrentDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-chargeCurr-')
phasesDisp = sg.Text(0, size=(3, 1), pad=(0, 0), justification='right', key='-measuredPhases-')
toGridDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-toGrid-')


def LEDIndicator(key=None, radius=30):
    return sg.Graph(canvas_size=(radius, radius),
                    graph_bottom_left=(-radius, -radius),
                    graph_top_right=(radius, radius),
                    pad=(0, 0), key=key)


def SetLED(win, key, color):
    graph = win[key]
    graph.erase()
    graph.draw_circle((0, 0), 15, fill_color=color, line_color='black')


col1 = [[sg.Text('Battery Level')],
        [batLevelBar, battDisp, sg.Text('% ', pad=0), sg.Text('---', key='-CHARGE_STATE-', pad=8, size=(17, 1)),
         sg.Stretch(), LEDIndicator('-LED_BAT')],
        [sg.Text('Charge Power')],
        [chargePwrBar, chargeDisp, sg.Text('kW', pad=0), chargeCurrentDisp, sg.Text('A', pad=0),
         phasesDisp, sg.Text('Phase'), sg.Stretch(), LEDIndicator('-LED_CHARGE-')],
        [sg.Text('Solar Power')],
        [solarPwrBar, solarDisp, sg.Text('kW', pad=0), sg.Text('PV total power')],
        [solarPwr2GridBar, toGridDisp, sg.Text('kW', pad=0), sg.Text('PV power to grid')],
        [sg.Text("")]  # empty line
        ]

layout = [[sg.Column(col1)],
          [sg.Button('Force Charge', disabled=True), sg.Button('Stop Charge', disabled=True),
           sg.Button('PV-Settings'), sg.Button('Quit')]
          ]

# create window`
window = sg.Window('ECOM PV Manager', layout)
batt_bar = window['-battBar-']
solar_bar = window['-solarBar-']
charge_bar = window['-chargeBar-']
toGrid_bar = window['-toGridBar-']


# ------------------------------------- data acquisition -------------------------------------

SIMULATE_PV_TO_GRID = 0

class ChargeModes:  # kind of enum
    IDLE = 0
    PV = 1
    FORCED = 2
    EXTERN = 3
    STOPPED = 4
    FORCE_REQUEST = 5

chargeMode = ChargeModes.IDLE  # default
oldChargeMode = chargeMode
phases = 1
oldPhases = phases

sysData = pv_utils.sysData
sysData.pvHoldTimer = pv_utils.EcTimer()
sysData.phaseHoldTimer = pv_utils.EcTimer()

t100ms = 0
t1s = -1
ExecImmediate = False
pvData = None
pvChargeOn = False
chargeState = 0
exitApp = False
forceFlag = 'IDLE'

try:
    settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
except:
    settings = sysSettings.defaultSettings
    sysSettings.writeSettings(const.C_DEFAULT_SETTINGS_FILE, settings)
#manualSettings = settings['manual']
#pvSettings = settings['pv']


def evalChargeMode(chargeMode, sysData, settings):
    ''' State machine depending on realtime data and user intervenrion

    :param chargeMode:  enum like construct defined in class ChargeModes
    :param sysData: C structure like record defined in class sysData
    :param settings: data from PV_Manager.json file
    :return: processed charge mode
    '''

    pvSettings = settings['pv']
    manualSettings = settings['manual']
    pv_utils.calcChargeCurrent(sysData,
                               pvSettings['max_1_Ph_current'], pvSettings['min_3_Ph_current'] ) #todo: int()
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

                if sysData.actPhases != sysData.reqPhases: # phase switch requested?
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
           access.ecSetChargerData("acs", "0", 5)   # authentication
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
            print('Current 1P:', sysData.calcPvCurrent_1P,' 3P: ', sysData.calcPvCurrent_3P, 'PhaseRequest', sysData.reqPhases)
            if sysData.actPhases != sysData.reqPhases:  # phase switch requested?
                access.ecSetChargerData("psm", sysData.reqPhases)
                sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)

    elif chargeMode == ChargeModes.EXTERN:
        if sysData.chargePower == 0:
            chargeMode = ChargeModes.IDLE
            print('External Charge OFF')

    print(' NEW:', chargeMode)
    return chargeMode

sysData.phaseHoldTimer = pv_utils.EcTimer()
sysData.pvHoldTimer = pv_utils.EcTimer()
sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME) # prevent early phase switch

# ------------------------------------------------ this is the main control loop -------------------------------------
while not exitApp:
    # cyclic check for user action
    event, values = window.read(timeout=100)
    if event == 'Quit' or event == sg.WIN_CLOSED:
        access.ecSetChargerData("frc", "1", 5)  #switch charging OFF
        access.ecSetChargerData("psm", const.C_CHARGER_1_PHASE)
        access.ecSetChargerData("acs", "1", 5)  #authentication required
        exitApp = True
    elif event == 'Force Charge':
#            manualSettings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)['manual']
            forceFlag = True
    elif event == 'Stop Charge':
        if chargeMode == ChargeModes.FORCED or chargeMode == ChargeModes.EXTERN :
            chargeMode = ChargeModes.STOPPED
            ExecImmediate = True
#        if chargeMode == ChargeModes.FORCED:
#            chargeMode = ChargeModes.IDLE

    elif event == 'PV-Settings':
       done = popSettings.popSettings(batteryLevel=batteryLevel)
       if done:
            pvSettings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)['pv']

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
            #            chargeMode = evalChargeMode(chargeMode, sysData, settings)
            ExecImmediate = False

        # read car data
        if (t1s % const.C_SYS_CAR_CLOCK) == 0:
            #            ExecImmediate = False
            if sysData.carPlugged:
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
            chargeMode = evalChargeMode(chargeMode, sysData, settings)


        if sysData.carPlugged and forceFlag == True:
            done = popCharge.popCharge(batteryLevel=batteryLevel)
            if done:
                settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
                chargeMode = ChargeModes.FORCE_REQUEST
                ExecImmediate = True
            forceFlag = False


    # ---------------------------------------- update display elements -------------------------------------------
    if sysData.carPlugged and t1s == 1: # first run
        window['Force Charge'].update(disabled=False)
        window['Stop Charge'].update(disabled=False)

    if chargeMode != oldChargeMode:
        oldChargeMode = chargeMode
        if chargeMode == ChargeModes.PV:
            print('SOLAR CHARGE')
            SetLED(window, '-LED_CHARGE-', 'yellow')

        elif chargeMode == ChargeModes.FORCED:
            print('FORCED CHARGE')
            SetLED(window, '-LED_CHARGE-', 'white')

        elif chargeMode == ChargeModes.EXTERN:
            print('EXTERN CHARGE')
            SetLED(window, '-LED_CHARGE-', 'blue')

        elif chargeMode == ChargeModes.IDLE:
            print('IDLE, waiting for event')
            SetLED(window, '-LED_CHARGE-', 'grey')

    batt_bar.UpdateBar(sysData.batteryLevel)
    window['-batt-'].update(sysData.batteryLevel)
    window['-CHARGE_STATE-'].update(sysData.carState)

    solar_bar.UpdateBar(sysData.solarPower)
    window['-solar-'].update(sysData.solarPower)

    charge_bar.UpdateBar(sysData.chargePower / 1000)
    window['-charge-'].update(sysData.chargePower / 1000)
    window['-chargeCurr-'].update(sysData.currentL1)
    window['-measuredPhases-'].update(sysData.measuredPhases)

    toGrid_bar.UpdateBar(sysData.pvToGrid)
    window['-toGrid-'].update(sysData.pvToGrid)
    if sysData.carPlugged:
        SetLED(window, '-LED_BAT', 'spring green')
    else:
        SetLED(window, '-LED_BAT', 'grey')
        SetLED(window, '-LED_CHARGE-', 'grey')


# done with loop... need to destroy the window as it's still open
window.close()
