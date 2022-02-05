# todo: replace charger IP address with constant
# todo: replace charger token with constant

# Renault ZOE constants
C_RENAULT_USER = "klaus2@bluewin.ch"
C_RENAULT_PASS = "Mez2-privat"
C_GIGYA_URL = "https://accounts.eu1.gigya.com"
C_GIGYA_API_ID = "3_UyiWZs_1UXYCUqK_1n7l7l44UiI_9N9hqwtREV0-UYA_5X7tOV-VKvnGxPBww4q2"
C_KAMERON_URL = "https://api-wired-prod-1-euw1.wrd-aws.com"
C_KAMERON_API = "Ae9FDWugRxZQAGm3Sxgk7uJn6Q4CGEA2"
C_RENAULT_VIN = "VF1AG000067847292"

C_RENAULT_BATT_MAX = 95  # % of max
C_RENAULT_BATT_MIN = 20  # % of max


# Weather constants
C_WEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast?q=arbon,ch&&units=metric&APPID="
C_WEATHER_API_KEY = "e00176e559c6b27d5df2fe21d8cd26e0"

# V1 / V2  Charger constants
C_CHARGER_API_VERSION = 2
C_CHARGER_NAME = "go-echarger"
# V1 C_CHARGER_WIFI_URL = "http://192.168.0.11"
C_CHARGER_WIFI_URL = "http://192.168.0.30/api"
C_CHARGER_GET_STATUS = "/status"
# V1 C_CHARGER_SET_PARAM = "/mqtt?payload="
C_CHARGER_SET_PARAM = "/set?"
# V1 C_CHARGER_CLOUD_URL = "https://api.go-e.co/api_status?token=ad5bce7889"
C_CHARGER_CLOUD_URL = "https://074368.api.v3.go-e.io/api/status?token=8UftBYBv29MufyIQbPDeRIBNG1KSLJSS"
C_CHARGER_MIN_CURRENT = 7
C_CHARGER_MAX_CURRENT = 15
C_CHARGER_MAX_POWER = 11
C_CHARGER_STATUS_TEXT = ("No Charger access", "No vehicle", "Charging", "Waiting for Vehicle ", "Connected, finished")
#C_CHARGER_START_CMD = "alw"    # 1: charge
C_CHARGER_START_CMD = "frc"     # 2: force, 1:stop
C_CHARGER_3_PHASES = "2"        # parameter psm
C_CHARGER_1_PHASE = "1"        # parameter psm



# PV constants
C_SOLAR_URL = "https://monitoringapi.solaredge.com/site/601283/currentPowerFlow.json?api_key=UBXKIEOBRR64GNOQ6G43M3BQBFSNES8H"
C_PV_MIN_REMAIN = 0.1

# System costants - Timing
C_SYS_BASE_CLOCK = 1            # seconds
C_SYS_FORECAST_REQ_TIME = 19    #time of day
C_SYS_FORECAST_TIME = (14, 1)   #time od day, delta day

C_SYS_PV_CLOCK = 20             # seconds
C_SYS_CAR_CLOCK = 60            # seconds
C_SYS_CHARGER_CLOCK = 10
C_SYS_MIN_PV_HOLD_TIME = 60     # seconds
C_SYS_MIN_PHASE_HOLD_TIME = 60  # seconds


C_DEFAULT_SETTINGS_FILE = "./PV_Manager.json"

