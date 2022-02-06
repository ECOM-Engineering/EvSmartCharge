import time
import const
import access

# todo: PV power must remain for x minutes before decision
# todo: use minimum charge time / pause time
# todo: set charger aws only once
# todo: night charging solution (charge < x%; manual intervention via remotecontrol ...)
# todo: Override local  decisions with remote control

C_ = {}
SIMULATE_PV_TO_GRID = 0


# pvChargeOn = False
# todo: newcurrent nur setzen. wenn änderung gegenüber istzustand ??

class sysData:  # kind of C structure
    carPlugged = False
    batteryLevel = 0  # %
    solarPower = 0  # kw
    pvToGrid = 0  # kW
    chargePower = 0  # W
    currentL1 = 0  # A
    voltageL1 = 0
    chargeActive = False
    measuredPhases = 0  # 1 | 3 measured number of measuredPhases
    actPhases = "0"  # actual charger psm setting (C_CHARGER_x_PHASE)
    reqPhases = "0"
    calcPvCurrent_1P = 0  # calculated 1 phase current, limited to max. setting
    calcPvCurrent_3P = 0  # calculated 3 phase current, if pvToGrid > minimum 3 phase current
    pvHoldTimer = 'none'
    phaseHoldTimer = 'none'
    carState = "?"


def ecGetChargerData(sysData):
    chargerData = access.ecReadChargerData()
    print('Charger Data:', chargerData)
    sysData.carPlugged = False
    if int(chargerData['car']) > 1:
        sysData.carPlugged = True
        # V1                sysData.chargePower = chargerData['nrg'][11] / 100  # original value is in 10W
        sysData.chargePower = chargerData['nrg'][11]  # original value
        # V1                sysData.currentL1 = chargerData['nrg'][4] / 100
        sysData.currentL1 = chargerData['nrg'][4]
        sysData.voltageL1 = chargerData['nrg'][0]
        if chargerData['nrg'][6] > 1:  # current on L3, if charging with 3 measuredPhases
            sysData.measuredPhases = 3
        else:
            sysData.measuredPhases = 1

        sysData.actPhases = str(chargerData['psm'])
        sysData.chargeActive = chargerData['frc'] == 2
        sysData.carState = const.C_CHARGER_STATUS_TEXT[int(chargerData['car'])]

    return sysData.carPlugged


def calcChargeCurrentOld(sysData):
    """ Calculate optimal charge current depending on solar power. """

    solarChargeCurrent = 0
    # V1    actualPower = (chargerData['nrg'][11]) / 100
    actualPower = sysData.chargePower / 1000  # convert to kW
    newPower = actualPower + sysData.pvToGrid - const.C_PV_MIN_REMAIN  # calculation in kW
    if sysData.voltageL1 > 0:
        solarChargeCurrent = newPower * 1000 / sysData.voltageL1
    if solarChargeCurrent > const.C_CHARGER_MAX_CURRENT:
        solarChargeCurrent = const.C_CHARGER_MAX_CURRENT

    return int(solarChargeCurrent)


def calcChargeCurrent(sysData, maxCurrent_1P, minCurrent_3P):
    """ Calculate optimal charge current depending on solar power. """

    solarChargeCurrent = 0
    sysData.reqPhases = const.C_CHARGER_1_PHASE

    # V1    actualPower = (chargerData['nrg'][11]) / 100
    actualPower = sysData.chargePower / 1000  # convert to kW
    newPower = actualPower + sysData.pvToGrid - const.C_PV_MIN_REMAIN  # calculation in kW

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


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class EcTimer:
    def __init__(self):
        self._start_time = None

    def set(self, timePeriod):
        self._start_time = timePeriod + time.perf_counter()

    def read(self):
        if self._start_time is not None:
            remain = self._start_time - time.perf_counter()
            if remain < 0:
                remain = 0
        else:
            remain = 0
        return remain

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def elapsed(self):
        if self._start_time is not None:
            elapsed_time = time.perf_counter() - self._start_time
            print(f"Elapsed time: {elapsed_time:0.4f} seconds")
            return elapsed_time

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")
