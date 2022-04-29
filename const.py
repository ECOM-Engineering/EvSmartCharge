import configparser as CP

configFile = "./evs.cfg"
config = CP.ConfigParser()
try:
    config.read(configFile)

    C_RENAULT_COUNTRY = config['RENAULT_CAR']['country']
    C_RENAULT_USER = config['RENAULT_CAR']['user']
    C_RENAULT_PASS = config['RENAULT_CAR']['pass']
    C_RENAULT_VIN = config['RENAULT_CAR']['VIN']
    C_RENAULT_BATT = int(config['RENAULT_CAR']['battery'])

    C_GIGYA_URL = config['RENAULT_SERVER']['gigya_url']
    C_GIGYA_API_ID = config['RENAULT_SERVER']['gigya_api_id']
    C_KAMERON_URL = config['RENAULT_SERVER']['kameron_url']
    C_KAMERON_API = config['RENAULT_SERVER']['kameron_api']

    C_CHARGER_API_VERSION = int(config['CHARGER']['api_version'])
    C_CHARGER_WIFI_URL = config['CHARGER']['wifi_url']
    C_CHARGER_NAME = config['CHARGER']['name']
    C_CHARGER_MIN_CURRENT = int(config['CHARGER']['min_current'])
    C_CHARGER_MAX_CURRENT = int(config['CHARGER']['max_current'])
    C_CHARGER_MAX_POWER = int(config['CHARGER']['max_power'])

    C_SOLAR_URL = config['PV_CONSTANTS']['solar_url']
    C_PV_MIN_REMAIN = float(config['PV_CONSTANTS']['pv_min_remain'])

except:
    print("error in config file")


C_CAR_STATE = ["Car Unpluged", "Car Ready", "Car Charging"]
C_CHARGER_STATUS_TEXT = ("0:Error", "1: Idle", "2: Charging", "3: WaitCa", "4: Completeç, 5: Error")
#C_CHARGER_STATUS_TEXT = ("No Charger access", "Vehicle unplugged", "Charging", "Awaiting command", "Ready")
C_CHARGER_3_PHASES = 2         # parameter psm value 3 phase
C_CHARGER_1_PHASE = 1          # parameter psm value 1 phase

# ----------------   System costants - Timing -----------------------
C_SYS_BASE_CLOCK = 1            # seconds
C_SYS_FORECAST_REQ_TIME = 19    # time of day
C_SYS_FORECAST_TIME = (14, 1)   # time od day, delta day
C_SYS_PV_CLOCK = 50              # seconds
C_SYS_CAR_CLOCK = 120            # seconds
C_SYS_CHARGER_CLOCK = 20
C_SYS_MIN_PV_HOLD_TIME = 180    # seconds
C_SYS_MIN_PHASE_HOLD_TIME = 60  # seconds

C_MAX_CAR_CONNECTION_ERRORS = 2 # stop charging after X consecutive errors


C_DEFAULT_SETTINGS_FILE = "./PV_Manager.json"
C_INI_FILE = "./evsGUI.ini"


# ----------------   GUI Constants ----------------------------------
C_BATT_COLORS = ["#F70000", "#DE4A00", "#009F59", "#00B259", "#00FF7F"]
C_BLINK_OK_COLOR = '#CCCCCC'   # light grey
C_BLINK_ERROR_COLOR = '#E10032'  # red
C_LOGO = b'iVBORw0KGgoAAAANSUhEUgAAABQAAAAeCAYAAAAsEj5rAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2Nh\
          cGUub3Jnm+48GgAAAcBJREFUSImtlr1Lw0AYxp+0qTGpi7h0dHJx08mhgyBCC51c7OBSdHIRHOp/4CbYqVBwk44dFAVBECz+B10EQSpFLS0\
          p0g/bJPc6tKZJemnSj2e75L3fvc9zdyFQ40ruaxdhzEkBgJKSqDzXE0vrcwICAK0FDfakxpTUnIAAgWQIlJk1gsDoo9ki4ACBWSJwAU4fgS\
          vQgp4oAh9AYJIIBDUuNwEgtLETlI8vJV5R5+LoVyu9sMGUfFdvn0Qe0OLViiZ5MYxAZFXgLisplueUlERls54IHKzcNEuuQKtap9sdQ62Si\
          VC/yV5hRpBevm9feQKNWoVYrUK8dyYSJENARo0rW9YIuMBQdE9Es0EAQMxA7/FaH4O2RcAFyofnC2a5rnkAAWsEXKBWLOjUbfcHhjGe5RAX\
          2Mmle14Z2iW8GsG+ZZ8Heyws39Xb0f8jxO1QiqVE1voxx1qxoLNq2daxAKFDBH/HRto/W7CO2XuJsWrZEubQonOuCTQ+36h3m9V4C7Dqh6W\
          7wdW741898y57yc2ia4ceOFeLTvnYZfsuesm1Q78WfQL9W3SKY3kyi04NP7BTWnQBTm9xRI24kp3nz9If3278UQPZrKUAAAAASUVORK5CYII='


# ----------------  Weather constants (not used yet) -----------------------------
# C_WEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast?q=arbon,ch&&units=metric&APPID="
# C_WEATHER_API_KEY = "e00176e559c6b27d5df2fe21d8cd26e0"





