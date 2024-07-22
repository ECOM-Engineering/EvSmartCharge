# from typing import Dict, Union

import FreeSimpleGUI as sg
import requests
import socket
from charger import search_charger
x=sg.version

manualSettings = {'cancelled': True, 'currentSet': 10, 'chargeLimit': 90, '3_phases': False}

#b64Logo=b"iVBORw0KGgoAAAANSUhEUgAAAA4AAAAQCAYAAAAmlE46AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAMNJREFUKJGVkr0NwjAUhO9ZGYCCGRLZmYIRmAYoyQAUiAkYgIaCMhUNveMmI1BQUCBEdDT8JWDjXGf7fXfvJINab2lMjp5SEBmB3NOYJdN0GAsKjTm/TuQJSi0ArMTaazixZSMDkAXIA7Uexyd2RZYQmUpV2XDil62/fzixnd7qHw++VYOch1f1SeSSRA93Vv0PkjeIrNE0hTh3fF6HQbKEUhOxtuo++cAawEyc2/k822CPL5c8gJ89gmKeb5hlWdTwh+56AWOaUxHtDQAAAABJRU5ErkJggg=="
b64Logo=b'iVBORw0KGgoAAAANSUhEUgAAABoAAAAeCAYAAAAy2w7YAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAqlJREFUSIm11U9IFGEYBvDnnf3njFmrXoog8iBBRyGIKEiQYHcriQjqUiB0qKBLsIZetEtQKCUI/aGTVIiQQuWGFQhZRJFE4aGDFJpIy7azq7s7uzsz39tBGFcdd3fW9rnNzPd8v/mYb2agBpXny4Ft+1HlSAC3mpJ4r4bkgaVTdY1VhABm9oDRYeaMr8mQcpnPwFUVqCD1gvlWIqN8SoRq26oJrYR5H7MYS4TkkcSxmqbqQZaHANzSl3hAvs0nUVc1CAAY7CXCpaQpT6sBpYN7SncqgiyQsQvEA4nP8mQyIB+sGrQqokVIeK0G5aH4CXlPuTVSg3IKADwtbS75yl2f3SCt/2JWn/kgNpRBGRDuqOlMf9MkssUgt1WqqYW0cy/ZjvIptucZrIDRVa/IF+JB9NaPa08J4KJQYdLXWjVTjVoFVv/YlldB7CbggRpQzseZwg2v0t/KgszYAovYQtHJ7ULEh0E8pQaVYbchdddNpKJFIc+R026kEgwALEzk3z42HHgSwOcMjxlUg3JfjLXB5ghy1mbwHmp3Kd1Pata32NCRbPenHS6uIDQLiXtsV6RPjRqcy6wcmGblxkqYTcraQtrDznwlz2hNCEkw+mKcGWyOIGcLbTECoGG3XsZm8AU63CK9ZB3rU6OGiM6VXCGB3glQuGE8/X39NXvo7HXvmlv8NSNEdG7Th0XAbwHc8I9nSr+w5uIs51/c0+0Giei8bdnJJ8ja3o5CYDDGhIGuxgltvpyK881AmJYEwjsi2kcntbJ/E0RYBNNV/wHtqFMEKGNFBMoL5kf+Wq2XRpBCxClRBkSECHQRbpjI/qxs+lIQ0Q8Cdfpfpt9sFdgMUiWim9uVzH0awZY/chsgItIZPOTyunu3jy7//Z+AFTUkP0se9zVXZfKC/AOggCeZWmV4NwAAAABJRU5ErkJggg=='
#b64Logo = b'iVBORw0KGgoAAAANSUhEUgAAAAwAAAAOCAYAAAAbvf3sAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAO1JREFUKJGNz69Lg1EUxvHveZ0aBINZ28p7GYLJ7J/gn7B3KwprgiCCQ7AoBrHOH2CxmwSLRTCIZSrCMNiWdeCY3sd0BcfuuE8853zO4aAiv1K9kpOYDGwF7+9UdQdqlGcTAACTGGv0ptqq5etq/tWjIGQO2T7v7lZVt5wCQpbIuFHNXai+OJ8CQBhiFf/9oMJtqVGeBjAV7jOK/m94A3biF0bdxL5KCYM94IiZwaEdd/pxYAh0iU1sW6vdDeUYeMSzYWcv98ONYdDF2GPh+dya+FGbAhggWtjPrp28fox7qITpGrJNO33qjBsM+QXm+0kImC1DaAAAAABJRU5ErkJggg=='
# todo: function parameter replace with manualSettings ??

def popSearchCharger():
    """ Search based on local wifi ip of the host. """

    find_IP_root()
    ip_root = 'http://' + find_IP_root()
    foundIP = '?'

    layout_popC = [[sg.Text('CHARGER NOT FOUND at!', pad=0), sg.Text(' 2nd Text')],
                   [sg.Text('WiFi root:', size=10), sg.Input(ip_root + 'xxx', size=30, disabled=True )],
                   [sg.Text('Serching at:', size=10),
                    sg.Multiline(key='-ACTUAL_IP-',size=(30,5),no_scrollbar = True, autoscroll = True,
                                 reroute_stdout = True, write_only = True, auto_refresh = True,background_color='lightgrey')],
                   [sg.Text('Found:', size=10), sg.Input('---', size=30,key='-FOUND_IP-', disabled=True )],
                   [sg.Button('SEARCH!', size=10, focus=True), sg.Button('EXIT', size=10)]]

    # test global padding    popWin = sg.Window('Manual Charge Options',  layout_popC, element_padding=0)

    popWin = sg.Window('Search Charger IP', layout_popC, icon=b64Logo)
    while True:
        ev2, val2 = popWin.read(100)
        if ev2 == sg.WIN_CLOSED or ev2 == 'EXIT':
           #    print(manualSettings)
            break
        if ev2 == 'SEARCH!':
            foundIP = search_charger(ip_root)
            popWin['-FOUND_IP-'].update(foundIP)

    popWin.close()

    return foundIP

# def search_charger(ip_root, tout = 0.3):
#     retval = "-1"
#     command = "/api/status?filter=fna"
#     for i in range(1, 250):
#         ip = ip_root + str(i)
#         try:
#             print(ip)
#             response = requests.get(ip + command, timeout=(tout))
#             statusCode = response.status_code
#             if statusCode == 200:
#                 print("IP found:", ip, end =" ")
#                 retval = ip
#                 break
#         except:
#             continue
#     return retval

def find_IP_root():
    hostname = socket.gethostname()
    print("hostname:", hostname)
    ip_address = socket.gethostbyname(hostname)
    print("IP:", ip_address)
    lastDot = ip_address.rfind('.')
    ip_root = ip_address[:lastDot + 1 ]
    return ip_root

if __name__ == "__main__": popSearchCharger()
