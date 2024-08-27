"""Read an write charge settings from and to json file."""
import json

defaultSettings = {'manual': {'currentSet': 12, 'chargeLimit': 80, '3_phases': False, 'phaseSet': True},
                   'pv': {'max_1_Ph_current': 14, 'min_3_Ph_current': 8, 'chargeLimit': 80, 'allow_3_phases': False}}


def writeSettings(file="", settingsDict=None):
    """
    writes dictionary to json formatted file.

    :param file: name of setting json file
    :param settingsDict: name of dictionary containing actual settings
    :return: ---
    """
    if settingsDict is None:
        settingsDict = {}
    with open(file, "w") as write_file:
        json.dump(settingsDict, write_file, indent=4)


def readSettings(file=""):
    """
    reads dictionary from json formatted file.

    :param file:
    :return:
    """
    with open(file) as readFile:
        return json.load(readFile)
