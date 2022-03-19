import const
import timers
import charger

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
    batteryLevel = 0  # % from Renault server car API
    solarPower = 0  # kw from Solar Inverter Cloud
    pvToGrid = 0  # kW from Solar Inverter Cloud
    chargePower = 0.0  # W  from go-eCharger Wallbox
    currentL1 = 0  # A  from go-eCharger Wallbox
    voltageL1 = 0  # V  from go-eCharger Wallbox
    chargeActive = False  # from go-eCharger
    measuredPhases = 0  # 1 | 3 number of measuredPhases
    actPhases = 0  # actual charger psm setting (C_CHARGER_x_PHASE)
    actCurrSet = 0  # actual charger setting
    reqPhases = 0  # requested phase by user or PV situation
    calcPvCurrent_1P = 0  # calculated 1 phase current, limited to max. setting
    calcPvCurrent_3P = 0  # calculated 3 phase current, if pvToGrid > minimum 3 phase current
    carState = "Vehicle Unplugged"
    pvHoldTimer = timers.EcTimer()
    phaseHoldTimer = timers.EcTimer()
    carErrorCounter = 0 # increment if eror during car data read

class ChargeModes:  # kind of enum
    """Constants defining system state."""
    UNPLUGGED = 0
    IDLE = 1
    PV = 2
    FORCED = 3
    EXTERN = 4
    STOPPED = 5
    FORCE_REQUEST = 6
    CAR_ERROR = 7  # todo if car data read error suspend charging

def processChargerData(sysData):
    """
    Converts charger data into sysData format
    :param sysData: data record similar to C structure
    :return: True, if car is plugged
    """
    chargerData = charge.get_charger_data()
    print('Charger Data:', chargerData)
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
        else:
            sysData.chargePower = chargerData['nrg'][11] / 1000 # original value is in W
            sysData.actPhases = chargerData['psm']
            sysData.currentL1 = chargerData['nrg'][4]     # original alue is in 1A
            if chargerData['frc'] == 2: sysData.chargeActive = True # True while charging
            else: sysData.chargeActive = False
        # V1                SysData.currentL1 = chargerData['nrg'][4] / 100
        sysData.voltageL1 = chargerData['nrg'][0]
        if chargerData['nrg'][6] > 1:  # current on L3, if charging with 3 measuredPhases
            sysData.measuredPhases = 3
        else:
            sysData.measuredPhases = 1

        sysData.actCurrSet = chargerData['amp']


    sysData.carState = const.C_CHARGER_STATUS_TEXT[int(chargerData['car'])]

    return sysData


def calcChargeCurrent(sysData, maxCurrent_1P, minCurrent_3P):
    """
     Calculate optimal charge current depending on solar power

    :param sysData:         data record similar to C structure
    :param maxCurrent_1P:   [A] upper limit for 1 phase
    :param minCurrent_3P:   [A] minimum used for switch overr to 3 phases
    :return sysData:        updatad data record
    """

    solarChargeCurrent = 0
    sysData.reqPhases = const.C_CHARGER_1_PHASE

    newPower = sysData.chargePower + sysData.pvToGrid - const.C_PV_MIN_REMAIN  # calculation in kW

    if sysData.voltageL1 > 0:
        solarChargeCurrent = newPower * 1000 / sysData.voltageL1

    if solarChargeCurrent > maxCurrent_1P:
        sysData.calcPvCurrent_1P = int(maxCurrent_1P)  # limit 1 phase current
        if solarChargeCurrent >= (minCurrent_3P * 3):  # switch to 3 phase request
            sysData.calcPvCurrent_3P = int(solarChargeCurrent / 3)
            sysData.reqPhases = const.C_CHARGER_3_PHASES
    else:
        sysData.calcPvCurrent_1P = int(solarChargeCurrent)

    #    if solarChargeCurrent > const.C_CHARGER_MAX_CURRENT:
    #        solarChargeCurrent = const.C_CHARGER_MAX_CURRENT

    return sysData


def evalChargeMode(chargeMode, sysData, settings):
    """ State machine depending on realtime data and user intervention

    :param chargeMode:  enum like construct defined as class ChargeModes
    :param sysData: C structure like record defined as class SysData
    :param settings: dictionary from PV_Manager.json file
    :return: processed charge mode
    """
    new_chargeMode = chargeMode
    pvSettings = settings['pv']
    manualSettings = settings['manual']
    pvAllow3phases = pvSettings['allow_3_phases']

    calcChargeCurrent(sysData, pvSettings['max_1_Ph_current'], pvSettings['min_3_Ph_current'])

    if sysData.carPlugged:
        if chargeMode == ChargeModes.UNPLUGGED:
            new_chargeMode = ChargeModes.IDLE  # recover processing
    else:
        new_chargeMode = ChargeModes.UNPLUGGED

    if chargeMode == ChargeModes.FORCE_REQUEST:
        if sysData.batteryLevel < manualSettings['chargeLimit']:
            if manualSettings['3_phases']:
                sysData.reqPhases = const.C_CHARGER_3_PHASES
            else:
                sysData.reqPhases = const.C_CHARGER_1_PHASE

            if sysData.phaseHoldTimer.read() == 0:
#                access.ecSetChargerData("acs", "0")  # authenticate

                if sysData.actPhases != sysData.reqPhases:  # phase switch requested?
#                    access.ecSetChargerData("psm", sysData.reqPhases)
                    charge.set_phase(sysData.reqPhases)
                    sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)

                charge.set_current(manualSettings['currentSet'])
                charge.start_charging()
                new_chargeMode = ChargeModes.FORCED
            else:
                print('Phase change request -> wait, hold time', sysData.phaseHoldTimer.read())
        else:
            new_chargeMode = ChargeModes.IDLE

    if chargeMode == ChargeModes.FORCED:
        if sysData.batteryLevel >= manualSettings['chargeLimit']:
            new_chargeMode = ChargeModes.IDLE
            print('CHARGE OFF, manual limit reached')
            charge.stop_charging()
            charge.set_phase(const.C_CHARGER_1_PHASE)

    if chargeMode == ChargeModes.STOPPED:
        if sysData.phaseHoldTimer.read() == 0:
            new_chargeMode = ChargeModes.IDLE
            print('CHARGE STOPPED by user')
            charge.stop_charging()
            charge.set_phase(const.C_CHARGER_1_PHASE)
            # access.ecSetChargerData("frc", "1")  # OFF
            # access.ecSetChargerData("psm", const.C_CHARGER_1_PHASE, tout=10)  #
            # access.ecSetChargerData("acs", "1")  # authentication required
        else:
            print('phaseHoldTimer waiting:', sysData.phaseHoldTimer.read())

    #    elif chargeMode == ChargeModes.PV:
    if chargeMode == ChargeModes.PV:
        if sysData.reqPhases == const.C_CHARGER_1_PHASE:
            freeSolarCurrent = sysData.calcPvCurrent_1P
        else:
            freeSolarCurrent = sysData.calcPvCurrent_3P

        if freeSolarCurrent < const.C_CHARGER_MIN_CURRENT or sysData.batteryLevel >= pvSettings['chargeLimit']:
            if sysData.pvHoldTimer.read() == 0:
                new_chargeMode = ChargeModes.IDLE
                print('Solar charge OFF')
                charge.stop_charging()
#                access.ecSetChargerData("frc", "1")  # OFF
#                access.ecSetChargerData("acs", "1")  # authentication required
                sysData.pvHoldTimer.set(const.C_SYS_MIN_PV_HOLD_TIME)
        else:
            if freeSolarCurrent != sysData.actCurrSet:
                charge.set_current(freeSolarCurrent)

            if sysData.phaseHoldTimer.read() == 0 and pvAllow3phases:
                if sysData.actPhases != sysData.reqPhases:  # phase switch requested?
                    charge.set_phase(sysData.reqPhases)
                    print('set phases:', sysData.reqPhases)
                    sysData.phaseHoldTimer.set(const.C_SYS_MIN_PHASE_HOLD_TIME)

    elif chargeMode == ChargeModes.EXTERN:
        if sysData.chargePower < 1:
            new_chargeMode = ChargeModes.IDLE
            print('External Charge OFF')

    if chargeMode == ChargeModes.IDLE:
        freeSolarCurrent = sysData.calcPvCurrent_1P
        if freeSolarCurrent >= const.C_CHARGER_MIN_CURRENT and sysData.batteryLevel < pvSettings['chargeLimit']:
            if sysData.pvHoldTimer.read() == 0:
                sysData.pvHoldTimer.set(const.C_SYS_MIN_PV_HOLD_TIME)
                new_chargeMode = ChargeModes.PV
                print('Charge ON. Current', int(freeSolarCurrent))
                charge.set_current(int(freeSolarCurrent))
                charge.start_charging()
        elif sysData.chargePower > 1:
            new_chargeMode = ChargeModes.EXTERN

    if new_chargeMode != chargeMode:
        print('NEW Mode:', new_chargeMode, 'OLD:', chargeMode)
        if new_chargeMode == ChargeModes.UNPLUGGED:
            charge.stop_charging(1)
            charge.set_phase(1)

    return new_chargeMode

