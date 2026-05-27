"""High level API based on 'Renault API'

    Uses Renault  https://renault-api.readthedocs.io/en/latest/endpoints.html
"""

import requests
import urllib.parse
import json
import const

# 'FR' replaced by 'CH' (Switzerland
# File Operations partly removed



def encodeURIComponent(s):
    return urllib.parse.quote(s)


class Zoe:

    def __init__(self, myRenaultUser, myRenaultPass):
        self.myRenaultUser = myRenaultUser
        self.myRenaultPass = myRenaultPass
        self.gigyaURL = const.C_GIGYA_URL
        self.gigyaAPI = const.C_GIGYA_API_ID
        self.kamareonURL = const.C_KAMERON_URL
        self.kamareonAPI = const.C_KAMERON_API
        self.vin = const.C_RENAULT_VIN
        self.country = const.C_RENAULT_COUNTRY

    def getStatus(self, endpoint, version = "2"):
        url = self.kamareonURL + '/commerce/v1/accounts/' + self.account_id + '/kamereon/kca/car-adapter/v' + version + '/cars/' + self.VIN + '/' + endpoint + '?country=' + self.country
        headers = {"x-gigya-id_token": self.gigyaJWTToken, "apikey": self.kamareonAPI, "Content-type": "application/vnd.api+json"}
        response = requests.get(url, headers=headers, timeout=20)
        print('endpoint response:', endpoint, response)  # mez
#        return json.loads(response.text)
        temp = json.loads(response.text)
        temp['status_code'] = response.status_code
        return temp

    def loadFromFile(self, filename):
        try:
            with open(filename, "r") as f:
                return f.read()
        except:
            return None

    def saveToFile(self, data, filename):
        with open(filename, "w") as f:
            f.write(data)

    def getPersonalInfo(self):
        # Save the result to a file, to avoid being annoyed by renault server quota limits.
        data = None
        data = self.loadFromFile("firststep.dta")
        if data is None:
            url = self.gigyaURL + '/accounts.login?loginID=' + encodeURIComponent(self.myRenaultUser) + '&password=' + encodeURIComponent(self.myRenaultPass) + '&include=data&apiKey=' + self.gigyaAPI
            response = requests.get(url, timeout=20)
            print("response step1", response)
            data = response.text
            self.saveToFile(data, "firststep.dta")
        self.gigyaCookieValue = json.loads(data)["sessionInfo"]["cookieValue"]
        self.gigyaPersonID = json.loads(data)["data"]["personId"]

        data = None
#        data = self.loadFromFile("secondstep.dta")  # this request must be actual (from day to day ?)
        if data is None:
            url = self.gigyaURL + '/accounts.getJWT?oauth_token=' + self.gigyaCookieValue + '&login_token=' + self.gigyaCookieValue + '&expiration=' + "87000" + '&fields=data.personId,data.gigyaDataCenter&ApiKey=' + self.gigyaAPI
            response = requests.get(url, timeout=20)
            print("response step2", response)
            data = response.text
            self.saveToFile(data, "secondstep.dta")
        self.gigyaJWTToken = json.loads(data)["id_token"]

        # Save the result to a file, to avoid being annoyed by renault server quota limits.
        data = None
        data = self.loadFromFile("thirdstep.dta")
        if data is None:
            url = self.kamareonURL + '/commerce/v1/persons/' + self.gigyaPersonID + '?country=CH'
            headers = {"x-gigya-id_token": self.gigyaJWTToken, "apikey": self.kamareonAPI}
            response = requests.get(url, headers=headers, timeout=10) # error happens here
            print("response step3", response)
            data = response.text
            self.saveToFile(data, "thirdstep.dta")
        self.account_id = json.loads(data)["accounts"][0]["accountId"]

        #Save the result to a file, to avoid being annoyed by renault server quota limits.
        data = None
        self.VIN = const.C_RENAULT_VIN

    def batteryStatus(self):
        return self.getStatus("battery-status")

    def location(self):
        return self.getStatus("location", "1")

    def googleLocation(self):
        loc = self.location()
        lat = str(loc["data"]["attributes"]["gpsLatitude"])
        lon = str(loc["data"]["attributes"]["gpsLongitude"])
        return "https://www.google.com/maps/search/" + lat + "+" + lon
    
    def chargingSettings(self):
        return self.getStatus("charging-settings", "1")
    
    def cockpit(self):
        return self.getStatus("cockpit", "1")
    
    def hvacStatus(self):
        return self.getStatus("hvac-status", "1")
