# -*- coding: utf-8 -*-
""" Basic library for accessing go-e charger API. """

from json import JSONDecodeError
import requests
from requests import ConnectionError

# API V1 see: https://github.com/goecharger/go-eCharger-API-v1
# API V2 see: https://github.com/goecharger/go-eCharger-API-v2
import const


class Charger:

    def __init__(self, url, api_version=2, timeout=5):
        """
        ini function at instantiation of this class 

        :param url:         Wi-Fi or cloud url of charger
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
                                'wh': 0, 'dwo': 0, 'acs': 0, 'err': -1, 'statusCode': 200}
        else:
            self.chargerData = {'car': 0, 'amp': 0, 'nrg': 15 * [0], 'pha': 0, 'dwo': 0, 'ast': 1, 'err': -1,
                                'statusCode': -1}

    # def __search_charger(self, tout=0.5):
    #     retval = "-1"
    #     command = "/api/status?filter=fna"
    #     for i in range(1, 250):
    #         ip = self.url_root + str(i)
    #         try:
    #             response = requests.get(ip + command, timeout = 0.5)
    #             statusCode = response.status_code
    #             if statusCode == 200:
    #                 print("IP found:", ip)
    #                 retval = ip
    #                 break
    #         except:
    #             continue
    #     return retval

    def get_charger_data(self):
        """
        Get relevant data from charger

        :return: dictionary containing actual charger status
        """
        print('\nObtaining charger data ...')
        command = "/status"
        statusCode = -1
        if self.api_version == 2:
            xfilter = 'filter='
            for keys in self.chargerData:
                xfilter = xfilter + keys + ','
                command = '/api/status' + '?' + xfilter

        try:
            response = requests.get(self.url + command, timeout=self.timeout)
            statusCode = response.status_code
            if statusCode == 200:
                jsonData = response.json()
                for key in self.chargerData:
                    if key in jsonData:
                        self.chargerData[key] = jsonData[key]
            else:
                self.chargerData['statusCode'] = statusCode

        except ConnectionError:
            statusCode = -1
            print('CONNECTION ERROR!')
        except JSONDecodeError:
            statusCode = -2
            print('JSON ERROR')
        except:
            statusCode = -3
            print('UNKNOWN ERROR')

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
        statusCode = self.chargerData['statusCode']
        if statusCode == 200:
            value = str(value)
            if self.api_version == 2:
                command = self.url + '/api/set?' + param + "=" + value
            else:
                command = self.url + '/mqtt?payload=' + param + "=" + value
            print('\nSetting charger Data', command)
            try:
                response = requests.get(command, timeout=self.timeout)
                status_code = response.status_code
            except ConnectionError:
                statusCode = -1

        return statusCode

    def start_charging(self):
        """
        Starts charging with previously set current

        :return: html status, 200 is OK
        """
        if self.api_version == 1:
            status_code = self.__set_charger_param('alw', 1)
            if status_code == 200:
                status_code = self.__set_charger_param('ast', 0)

        else:
            status_code = self.__set_charger_param('acs', 0)  # authenticate
            if status_code == 200:
                status_code = self.__set_charger_param('frc', 2)  # start charger
        return status_code

    def stop_charging(self, authenticate=1):
        """
        Stops charger and enables authentication

        :return:  html status, 200 is OK
        """
        if self.api_version == 1:
            status_code = self.__set_charger_param('alw', 0)
            if status_code == 200:
                status_code = self.__set_charger_param('ast', authenticate)
        else:
            status_code = self.__set_charger_param('frc', 1)
            if status_code == 200:
                # authenticate in order to prevent automatic start
                status_code = self.__set_charger_param('acs', authenticate)
        return status_code

    def set_current(self, current):
        """
        Set charging current im Ampere

        :param current: value as integer
        :return:  html status, 200 is OK
        """

        status_code = -2  # parameter Error
        if self.api_version == 1:
            param = 'amx'
        else:
            param = 'amp'
        if current <= const.C_CHARGER_MAX_CURRENT:
            status_code = self.__set_charger_param(param, current)
        return status_code

    def set_phase(self, phase):
        """
        Switch 1 to 3 phase or vice versa.

        :param phase: value 1 or 3. Only valid for API version 2 (charger series CM-03)
        :return:  html status, 200 is OK, -1 if command not recognized
        """
        if self.api_version == 1:
            status_code = -1
            print("phase command not supported in go-e charger CM01 and CM02")
        else:
            if phase == 1:
                value = const.C_CHARGER_1_PHASE
            else:
                value = const.C_CHARGER_3_PHASES
            status_code = self.__set_charger_param('psm', value)
        return status_code

