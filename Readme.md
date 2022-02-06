# EvSmartCharge 'ESC-1'

**This file and project under construction**

## Purpose

A smart EV vehicle charging software solution using as much of free solar power as available.  It uses remainig solar power besides other higher priority power consumers like heatpumps and other household equipment.

## Preconditions

Default configuration:

- [Renault ZOE](https://de.renault.ch/elektroautos/renault-zoe.html) Version from 2020++

- [go-eCharger](https://go-e.co/produkte/go-echarger-home/) Wallbox Version CM-03 with API V2 
  (older version vithout 1/ 2 phase switch only). 11kW or 22kW

- [SolarEdge](https://www.solaredge.com/homeowner-new) photovoltaic installation.

- WiFi and Internet connection 

Layered software archictecture allows adapting to different configurations and equipment.

## Functionality

ECS-1 is a Phyton software running on different systems including Raspberry-Pi computers. 

## Open Source Thanks

This software may be reused and adapted under respecting the MIT License. It is based in parts on other open source projects:

[pysmplegui](https://pysimplegui.readthedocs.io/en/latest/) graphical interface tool

[go-eCharger API V2](https://github.com/goecharger/go-eCharger-API-v2)  WLAN or Internet access to the go-eCharger Wallbox

[SolarEdge API](https://www.solaredge.com/sites/default/files/se_monitoring_api.pdf)

https://github.com/niosega/zozo) Renault Zoe Server Access API  

[zozo](https://github.com/niosega/zozo) Renault ZOE server access library


