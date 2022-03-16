# -*- coding: utf-8 -*-

import const
import time
import access
import timers
from requests import ConnectionError
import requests

# API V1 see: https://github.com/goecharger/go-eCharger-API-v1
# API V2 see: https://github.com/goecharger/go-eCharger-API-v2

class Charger:
    url = ''

    def __init__(self, url, api_version = 2, timeout =15):
        """
        ini function at instantiation of this class 

        :param url:         WiFi or cloud url of charger
        :param api_version: API version (series CM-02: 1, series CM-03: 2)
        :param timeout:     optional seconds. Default = 15
        """

        if url is None or url == '':
            raise ValueError("Please set charger url")

        self.url = url
        self.api_version = api_version
        self.timeout = timeout

        if self.api_version == 2:
            self.chargerData = {'car': 0, 'amp': 0, 'frc': 0, 'nrg': 15 * [0], 'fsp': 'true', 'psm': 1,
                     'wh': 0, 'dwo': 0, 'acs': 0, 'err': -1}
        else:
            self.chargerData = {'car': 0, 'amp': 0, 'nrg': 15 * [0], 'pha': 0, 'dwo': 0, 'ast': 1, 'err': -1}

    def get_charger_data(self):
        """
        Get relevant data from charger

        :return: dictionary containing actual charger status
        """
        print('\nObtaining charger data ...')
        if self.api_version == 2:
            filter=''
            pos = 0
            for keys in self.chargerData:
                filter = filter + ',' + keys
                command =  '/api/status' + '?' + filter
        else:
            command = const.C_CHARGER_GET_STATUS

        try:
            response = requests.get(self.url + command, timeout=self.timeout)
            statusCode = response.status_code
            if statusCode == 200:
                jsonData = response.json()
                for key in self.chargerData:
                     self.chargerData[key] = jsonData[key]
            else:
                self.chargerData['statusCode'] = statusCode

        except ConnectionError:
            self.chargerData['statusCode'] = -1
            print('CONNECTION ERROR!')
        except:
            self.chargerData['statusCode'] = -2
            print('JSON ERROR')

        self.chargerData['apiVer'] = self.api_version
        self.chargerData['statusCode'] = statusCode
        return self.chargerData


    def __set_charger_param(self, param, value):
        """
        INTERNAL function set a single parameter of the charger

        :param param: string: charger parameter to be set
        :param value: integer: value to be set
        :return: dictionary . On communication error: -1 or html status
        """

        value = str(value)
        if self.api_version == 2:
            command = self.url + '/api/status?'  + param + "=" + value
        else:
            command=  self.url + '/mqtt?payload=' + param + "=" + value

        print('\nSetting charger Data', command)
        try:
            response = requests.get(command, timeout=self.timeout)
            status = response.status_code

        except ConnectionError:
            status = -1

        return status


    def start_charging(self):
        """
        Starts charging with previously set current

        :return: html status, 200 is OK
        """

        if self.api_version == 1:
            status = self.__set_charger_param('alw', 1)
        else:
            status = self.__set_charger_param('acs', 0)  # authenticate
            if status == 200:
                status = self.__set_charger_param('frc', 2)  # start charger
        return status


    def stop_charging(self, authenticate = 1):
        """
        Stops charger and enables authentication

        :return:  html status, 200 is OK
        """
        if self.api_version == 1:
            status = self.__set_charger_param('alw', 0)
        else:
            status = self.__set_charger_param('frc', 1)
            if status == 200:
              status = self.__set_charger_param('acs', authenticate)  # authenticate in order to prevent automatic start

        return status


    def set_current(self, current):
        """
        Set charging current im Ampere

        :param current: value as integer
        :return:  html status, 200 is OK
        """
        if self.api_version == 1:
            param = 'amx'
        else:
            param = 'amp'

        status = self.__set_charger_param(param, current)
        return status

    def set_phase(self, phase):
        """

        :param phase: value 1 or 3. Only valid for API version 2 (charger series CM-03)
        :return:  html status, 200 is OK, -1 if command not recognized
        """
        if self.api_version == 1:
            status = -1
            print("phase command not supported in go-e charger CM01 and CM02")

        else:
            if phase == 1:
                value = 1
            else:
                value = 2
            status = self.__set_charger_param('psm', value)

        return status


# test
if __name__ == "__main__":

    go = Charger("http://192.168.0.30", 2)
#    go = Charger("http://192.168.0.11", 1)

    # go = Charger(const.C_CHARGER_WIFI_URL, 2)

    status = go.set_current(8)
    print('set_current() status =', status)

    status = go.get_charger_data()
    print('ecReadChargerData() status =', status)

    status = go.set_phase(1)
    print('set_phase status =', status)

    status = go.start_charging()
    print('START status =', status)

    wait = 5
    print('SLEEPING ... ', wait)
    time.sleep(wait)

    status = go.stop_charging()
    print('STROP status =', status)

#
# go = Charger("http://192.168.0.11", 1)
# status = go.set_current(8)
# print('status =', status)
#
# status = go.ecReadChargerData()
#
# status = go.set_phase(1)
# print(status)