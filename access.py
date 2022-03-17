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
     ec_GetCarData()
    # print("API Version =", const.C_CHARGER_API_VERSION)
    # ecReadChargerData()
    # ecSetChargerData("amp", "8")

#    ecSetChargerData("alw", "0")  # 1 : start charging
#    ec_GetPVData()
