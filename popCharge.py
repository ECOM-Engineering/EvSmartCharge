import PySimpleGUI as sg
import const
import sysSettings


def popCharge(batteryLevel=20, currentLimit = 16, file = const.C_DEFAULT_SETTINGS_FILE):
    """
    Function reads settings file and writes back if there are changes by the operator

    :param batteryLevel:    actual level in %
    :param currentLimit:    max allowed charge current
    :param file:            json file containing manual settings under key 'manual'
    :param currentSet:      charge current in A
    :return:                Dict {'manual': {'cancelled', 'currentSet', 'chargeLimit', '3_phases'}}
    """
    try:
        settings = sysSettings.readSettings(file)
        manualSettings = settings['manual']
    except:
        settings = sysSettings.defaultSettings
#       sysSettings.writeSettings(file, settings)
        manualSettings = settings['manual']

    done = False
    chargeLimit = manualSettings['chargeLimit']
    currentSet = manualSettings['currentSet']
    phaseSet = manualSettings['phaseSet']
    phases = manualSettings['3_phases']
    layout_popC = [[sg.Text('Battery Level:', pad=0)],
                   [sg.ProgressBar(100, orientation='h', size=(20, 10), key='-BATT_LEVEL BAR-', bar_color=('lightgreen','grey')),
                                    sg.Text(batteryLevel, key='-BATT_LEVEL DISP-', pad=0), sg.Text('%')],
                   [sg.Text('Charge Limit:', pad=0)],
                   [sg.Slider(k='-CHARGE LIMIT-', default_value=chargeLimit, range=(20, 100), orientation='h',
                              s=(25, 10), tick_interval=20), sg.Text('%')],
                   [sg.Text('Charge Current:', pad=0)],
                   [sg.Slider(k='-CURRENT-', default_value=currentSet, range=(6, currentLimit), orientation='h',
                              s=(25, 10), tick_interval=currentLimit / 8), sg.Text('A')],
                   [sg.Radio('1 Phase', "RADIO1", default=not (phases)),
                    sg.Radio('3 Phases', "RADIO1", k='-3_PHASES-', default=phases)],
                   [sg.HSeparator(pad=(0, 1))],
                   #    [sg.Frame('', [[sg.Button('Cancel'), sg.Button('Charge!', focus=True)]])]]
                   [sg.Button('Cancel'), sg.Button('Charge!', focus=True)]]

    # test global padding    popWin = sg.Window('Manual Charge Options',  layout_popC, element_padding=0)
    popWin = sg.Window('Manual Charge Options', layout_popC)
#    p = popWin['battLevel']
    if phaseSet == False:
        sg.Radio.visible = False
    while True:
        ev2, val2 = popWin.read(100)
        popWin['-BATT_LEVEL BAR-'].UpdateBar(batteryLevel)
        popWin['-BATT_LEVEL DISP-'].update(batteryLevel)
        if ev2 == sg.WIN_CLOSED or ev2 == 'Cancel':
            done = False
            break
        if ev2 == 'Charge!':
            manualSettings['cancelled'] = False
            manualSettings['currentSet'] = int(val2['-CURRENT-'])
            manualSettings['3_phases'] = val2['-3_PHASES-']
            manualSettings['chargeLimit'] = val2['-CHARGE LIMIT-']
            done = True
            break

    #    print(manualSettings)
    popWin.close()
    settings['manual'] = manualSettings
    sysSettings.writeSettings(file, settings)
    return done

if __name__ == "__main__":
    result = popCharge()
    print(result)