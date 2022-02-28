import json
import PySimpleGUI as sg

# default
# defaultSettings = {'manual':{'cancelled': True, 'currentSet': 12, 'chargeLimit': 80, '3_phases': False, 'phaseSet': True},
#                  'pv': {'currentSet': 8, 'chargeLimit': 80, '3_phases': False}}
defaultSettings = {'manual': {'currentSet': 12, 'chargeLimit': 80, '3_phases': False, 'phaseSet': True},
                   'pv': {'max_1_Ph_current': 14, 'min_3_Ph_current': 8, 'chargeLimit': 80, 'allow_3_phases': False}}


def writeSettings(file="", settingsDict=None):
    if settingsDict is None:
        settingsDict = {}
    with open(file, "w") as write_file:
        json.dump(settingsDict, write_file, indent=4)


def readSettings(file=""):
    with open(file) as readFile:
        return json.load(readFile)
