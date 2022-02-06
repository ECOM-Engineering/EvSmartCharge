# EvSmartCharge 'ESC-1'

**This file and project under construction**

## Purpose

A smart EV vehicle charging software solution using as much of free solar power as available.  It uses remainig solar power besides other higher priority power consumers like heatpumps and other household equipment.



## Preconditions

Default configuration:

- [Renault ZOE](https://de.renault.ch/elektroautos/renault-zoe.html) Version from 2020++

- [go-eCharger]([go-eCharger HOME – go-e - Smarte Ladestation und Ladetechnik für Elektroautos](https://go-e.co/produkte/go-echarger-home/)) Wallbox Version CM-03 with API V2 
  (older version vithout 1/ 2 phase switch only). 11kW or 22kW

- [SolarEdge](https://www.solaredge.com/homeowner-new) photovoltaic installation.

-  WiFi and Internet connection 



Layered software archictecture allows adapting to different configurations and equipment.

## Functionality

ECS-1 is a Phyton software running on different systems including Raspberry-Pi computers. 



## Open Source Thanks

This software may be reused and adapted under respecting the MIT License. It is based in parts on other open source projects:

[pysmplegui ]([PySimpleGUI](https://pysimplegui.readthedocs.io/en/latest/)) graphical interface tool

[go-eCharger API]([GitHub - goecharger/go-eCharger-API-v2: New API specification for V3 go-eCharger](https://github.com/goecharger/go-eCharger-API-v2)) WLAN or Internet access to the go-eCharger Wallbox

[SolarEdge API](https://www.solaredge.com/sites/default/files/se_monitoring_api.pdf)

[zozo ]([GitHub - niosega/zozo: Python API to query Renault Zoe information](https://github.com/niosega/zozo)) Renault Zoe Server Access API  




