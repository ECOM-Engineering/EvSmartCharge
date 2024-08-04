# from typing import Dict, Union

import FreeSimpleGUI as sg
import requests
import socket
import os
from charger import search_charger
x=sg.version

#b64Logo=b"iVBORw0KGgoAAAANSUhEUgAAAA4AAAAQCAYAAAAmlE46AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAMNJREFUKJGVkr0NwjAUhO9ZGYCCGRLZmYIRmAYoyQAUiAkYgIaCMhUNveMmI1BQUCBEdDT8JWDjXGf7fXfvJINab2lMjp5SEBmB3NOYJdN0GAsKjTm/TuQJSi0ArMTaazixZSMDkAXIA7Uexyd2RZYQmUpV2XDil62/fzixnd7qHw++VYOch1f1SeSSRA93Vv0PkjeIrNE0hTh3fF6HQbKEUhOxtuo++cAawEyc2/k822CPL5c8gJ89gmKeb5hlWdTwh+56AWOaUxHtDQAAAABJRU5ErkJggg=="
b64Logo=b'iVBORw0KGgoAAAANSUhEUgAAABoAAAAeCAYAAAAy2w7YAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAqlJREFUSIm11U9IFGEYBvDnnf3njFmrXoog8iBBRyGIKEiQYHcriQjqUiB0qKBLsIZetEtQKCUI/aGTVIiQQuWGFQhZRJFE4aGDFJpIy7azq7s7uzsz39tBGFcdd3fW9rnNzPd8v/mYb2agBpXny4Ft+1HlSAC3mpJ4r4bkgaVTdY1VhABm9oDRYeaMr8mQcpnPwFUVqCD1gvlWIqN8SoRq26oJrYR5H7MYS4TkkcSxmqbqQZaHANzSl3hAvs0nUVc1CAAY7CXCpaQpT6sBpYN7SncqgiyQsQvEA4nP8mQyIB+sGrQqokVIeK0G5aH4CXlPuTVSg3IKADwtbS75yl2f3SCt/2JWn/kgNpRBGRDuqOlMf9MkssUgt1WqqYW0cy/ZjvIptucZrIDRVa/IF+JB9NaPa08J4KJQYdLXWjVTjVoFVv/YlldB7CbggRpQzseZwg2v0t/KgszYAovYQtHJ7ULEh0E8pQaVYbchdddNpKJFIc+R026kEgwALEzk3z42HHgSwOcMjxlUg3JfjLXB5ghy1mbwHmp3Kd1Pata32NCRbPenHS6uIDQLiXtsV6RPjRqcy6wcmGblxkqYTcraQtrDznwlz2hNCEkw+mKcGWyOIGcLbTECoGG3XsZm8AU63CK9ZB3rU6OGiM6VXCGB3glQuGE8/X39NXvo7HXvmlv8NSNEdG7Th0XAbwHc8I9nSr+w5uIs51/c0+0Giei8bdnJJ8ja3o5CYDDGhIGuxgltvpyK881AmJYEwjsi2kcntbJ/E0RYBNNV/wHtqFMEKGNFBMoL5kf+Wq2XRpBCxClRBkSECHQRbpjI/qxs+lIQ0Q8Cdfpfpt9sFdgMUiWim9uVzH0awZY/chsgItIZPOTyunu3jy7//Z+AFTUkP0se9zVXZfKC/AOggCeZWmV4NwAAAABJRU5ErkJggg=='

def popSearchCharger():
    """ Search based on local wifi ip of the host. """

    ip_address = 'http://' + find_IP()
    lastDot = ip_address.rfind('.')
    ip_root = ip_address[:lastDot + 1 ]
    foundIP = '?'

    layout_popC = [[sg.Text('SEARCH CHARGER IN LOCAL WIFI NET')],
                   [sg.Text('WiFi root:', size=10), sg.Input(ip_root, size=30, disabled=True )],
                   [sg.Text('Serching at:', size=10),
                    sg.Multiline(key='-ACTUAL_IP-',size=(30,5),no_scrollbar = True, autoscroll = True,
                                 reroute_stdout = True, write_only = True, auto_refresh = True,background_color='lightgrey')],
                   [sg.Text('Found:', size=10), sg.Input('---', size=30,key='-FOUND_IP-', disabled=True )],
                   [sg.Button('SEARCH!', size=10, focus=True), sg.Button('EXIT', size=10)]]

    # test global padding    popWin = sg.Window('Manual Charge Options',  layout_popC, element_padding=0)

    popWin = sg.Window('Search Charger IP', layout_popC, icon=b64Logo)
    while True:
        ev2, val2 = popWin.read()
        if ev2 == sg.WIN_CLOSED or ev2 == 'EXIT':
           #    print(manualSettings)
            break
        if ev2 == 'SEARCH!':
            foundIP = search_charger(ip_root)
            popWin['-FOUND_IP-'].update(foundIP)

    popWin.close()

    return foundIP

def find_IP_root():
    hostname = socket.gethostname()
    print("hostname:", hostname)
    ip_address = socket.gethostbyname(hostname)
    print("IP:", ip_address)
    lastDot = ip_address.rfind('.')
    ip_root = ip_address[:lastDot + 1 ]
    return ip_root


def find_IP():
    status = os.popen("sudo ifconfig wlan0").read()
    print("status:", status)

    items = status.split()
    ip_pos = items.index('inet') + 1
    ip = items[ip_pos]
    print("My local wlan IP is:", ip)
    return(ip)

if __name__ == "__main__":
    find_IP()

if __name__ == "__main__": popSearchCharger()
