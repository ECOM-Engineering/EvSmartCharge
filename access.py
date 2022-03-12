from requests import ConnectionError
import requests
import json
from datetime import timedelta, date, datetime, time
import const
from zozo import Zoe

# todo: remove User Info (PW) from zoe.getPersonalInfo()


# noinspection SpellCheckingInspection
def ecGetWeatherForecast(forecast_time=14, days=1, JSON_File=False):
    """
    Get weather forecast from weather service provider.

    :param forecast_time: forecast hour in 24h format
    :param days: days after calling this function
    :param JSON_File: True: generate JSON file from weather API
    :return: weather forecast for the selected day and time
    """

    print('\nObtaining weather data ...')
    description = ''
    temperature = -9999
    clouds = -1
    weatherForecast = {'statusCode': 0, 'forecastDate': 0, 'clouds': 0, 'temp': -9999, 'weather': "?"}
    localDate = date.today()
    forecastDate = localDate + timedelta(days)
    forecastTime = time(forecast_time, 0)
    forecast_local = datetime.combine(forecastDate, forecastTime)
    timestamp = forecast_local.timestamp()

    url = const.C_WEATHER_URL + const.C_WEATHER_API_KEY
    r = requests.get(url, timeout=20)
    status_code = r.status_code
    if status_code == 200:
        jsondict = r.json()
        clouds = -1
        for i in jsondict['list']:
            i_timestamp = i['dt']
            if i_timestamp >= timestamp:
                clouds = i['clouds']['all']
                temperature = i['main']['temp']
                description = i['weather'][0]['description']  # thanks https://stackoverflow.com/a/23306717
                print('weather for:', forecast_local)
                print('clouds:', clouds)
                print('temperature:', temperature)
                print('weather:', description)
                break
        if JSON_File:
            with open("weather.json", 'w') as f:
                json.dump(jsondict, f, indent=4)

    weatherForecast['statusCode'] = status_code
    weatherForecast['forecastDate'] = forecast_local
    weatherForecast['clouds'] = clouds
    weatherForecast['temp'] = temperature
    weatherForecast['weather'] = description
    return weatherForecast


# noinspection SpellCheckingInspection
def ec_GetCarData():
    """
    Get car data from Renault cloud.

    :rtype: dictionary
    """
    print('\nObtaining car data ...')
    carData = {'statusCode': 0, 'batteryLevel': -1, 'plugStatus': 0, 'clima': '---', 'mileage': 0, 'location': "---"}
    try:
        zoe = Zoe(const.C_RENAULT_USER, const.C_RENAULT_PASS)
        zoe.getPersonalInfo()
    # todo: ignore if error    pos = zoe.googleLocation()
        batt = zoe.batteryStatus()
        cockpit = zoe.cockpit()
        carData['statusCode'] = batt['status_code']
        carData['batteryLevel'] = batt['data']['attributes']['batteryLevel']
        carData['plugStatus'] = batt['data']['attributes']['plugStatus']
#        carData['clima'] = hvac['data']['attributes']['hvacStatus']
        carData['mileage'] = cockpit['data']['attributes']['totalMileage']

    except ConnectionError:
        carData['statusCode'] = -1
        print('CONNECTION ERROR!')
    except:
        carData['statusCode']  = -2
        print('JSON ERROR')

#    carData['location'] = pos
#    print('car Data:', carData)
    return carData


# noinspection PyPep8
def ecReadChargerData(url=const.C_CHARGER_WIFI_URL, tout=15):
    """
    Get data from charger from WLAN or Cloud.

    :param url: url to the charger including API keys
    :param tout: timeout [default 5s]
    :return: dictionary containing relevant charger data
    """

    # API V1 see: https://github.com/goecharger/go-eCharger-API-v1
    # API V2 see: https://github.com/goecharger/go-eCharger-API-v2
    print('\nObtaining charger data ...')
# v1    chargerData = {'statusCode': 0, 'car': 0, 'amp': 0, 'amx' : 0, 'nrg': 15 * [0], 'pha': 0, 'dwo': 0, 'err': -1}
    chargerData = {'statusCode': 0, 'car': 0, 'amp': 0, 'amx': 0, 'frc': 0, 'nrg': 15 * [0], 'fsp': 'true', 'psm': 1, 'wh': 0, 'dwo': 0, 'err': -1}
    try:
        response = requests.get(url + const.C_CHARGER_GET_STATUS, timeout=tout)
        statusCode = response.status_code
        chargerData['statusCode'] = statusCode
        if statusCode == 200:
            jsonData = response.json()
            for key in chargerData:
                if key != 'statusCode' and key != 'amx':  # key is not in jsonData
                    chargerData[key] = jsonData[key]
        else:
            chargerData['statusCode'] = statusCode

    except ConnectionError:
        chargerData['statusCode'] = -1
        print('CONNECTION ERROR!')
    except:
        chargerData['statusCode'] = -2
        print('JSON ERROR')

    return chargerData


# noinspection SpellCheckingInspection
def ecSetChargerData(param="amp", value="8", tout=15):
    """
    Set a single parameter of the charger

    :param param: charger parameter to be set
    :param value: value to be set, always as string!
    :param tout: timeout in seconds
    :return: dictionary or error message, if param out of range
    """
    url = const.C_CHARGER_WIFI_URL + const.C_CHARGER_SET_PARAM + param + "=" + value
    print('\nSetting charger Data', url)
    try:
        response = requests.get(url, timeout=tout)
    except ConnectionError:
        response = -1
    return response


def ec_GetPVData(url=const.C_SOLAR_URL, tout=15):
    """
    Get relevant data from PV inverter.

    :param tout: timeout for url access
    :param url: complete url including api key
    :return: PV current flow
    """
    print('\nObtaining PV data ...')
    pvData = {'statusCode': 0, 'pvPower': 0.0, 'LoadPower': 0.0, 'PowerToGrid': -30}
    try:
        r = requests.get(url, tout)
        pvData['statusCode'] = r.status_code
        statusCode = r.status_code
        if statusCode == 200:
            jsondata = r.json()
            jsondata = jsondata['siteCurrentPowerFlow']
            pvData['pvPower'] = jsondata['PV']['currentPower']
            pvData['LoadPower'] = jsondata['LOAD']['currentPower']
            pvData['PowerToGrid'] = pvData['pvPower'] - pvData['LoadPower']
    except ConnectionError:
        pvData['statusCode'] = "exception"

    print(pvData)
    return pvData

# --------  test only -----------
if __name__ == "__main__":

#    ecGetWeatherForecast(forecast_time=14, days=1, JSON_File=False)
#    ec_GetCarData()
    print("API Version =", const.C_CHARGER_API_VERSION)
    ecReadChargerData()
    ecSetChargerData("amp", "8")

#    ecSetChargerData("alw", "0")  # 1 : start charging
#    ec_GetPVData()
