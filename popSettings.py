# import PySimpleGUI as sg
import FreeSimpleGUI as sg
import os.path

import sysSettings
import const

sg.theme("SystemDefault")
sg.set_options(button_color=('#000000','#cecece'), auto_size_buttons=False, button_element_size=(10,1))

def popSettings(batteryLevel=40, file=const.C_DEFAULT_SETTINGS_FILE, pop_location=(100,100)):
    """
    Function reads settings file and writes back if there are changes by the operator

    :param batteryLevel: actuel SoC in %
    :param file:  json file for settings
    :return: False, if  cancelled
    """

    if os.path.isfile(const.C_DEFAULT_SETTINGS_FILE):
        settings = sysSettings.readSettings(const.C_DEFAULT_SETTINGS_FILE)
    else:  # this is for test only, should never happen
        settings = sysSettings.defaultSettings
        sysSettings.writeSettings(const.C_DEFAULT_SETTINGS_FILE, settings)

    pvSettings = settings['pv']

    done = False
    chargeLimit = pvSettings['chargeLimit']
    max_I_1Ph = pvSettings['max_1_Ph_current']
    min_I_3Ph = pvSettings['min_3_Ph_current']
    phases = pvSettings['allow_3_phases']
    layout_popC = [[sg.Text('Battery Level:', pad=0)],
                   [sg.ProgressBar(100, orientation='h', size=(20, 10), key='battLevel',
                                   bar_color=('lightgreen', 'grey')), sg.Text(batteryLevel, key='-battLevel-', pad=0),
                    sg.Text('%')],
                   [sg.Text('Charge Limit:', pad=0)],
                   [sg.Slider(k='-CHARGE LIMIT-', default_value=chargeLimit, range=(20, 100), orientation='h',
                              enable_events=True,
                              s=(25, 10), tick_interval=20, disable_number_display=False), sg.Text('%')],
                   [sg.HSeparator(pad=(0, 10))],
                   [sg.Input(max_I_1Ph, key='-MAX_I_1_PH-', size=(2, 1), border_width=2),
                    sg.Text('Max. 1 Phase Current:')],
                   [sg.Checkbox('   Allow 3 Phases', key='-allow_3_phases-', pad=((4, 0), (8, 0)), default=phases)],
                   [sg.Input(min_I_3Ph, key='-MIN_I_3_PH-', size=(2, 1), border_width=2,
                             disabled_readonly_background_color='Grey'), sg.Text("Min. 3 Phase Current")],
                   [sg.HSeparator(pad=(0, 10))],
                   #    [sg.Frame('', [[sg.Button('Cancel'), sg.Button('Charge!', focus=True)]])]]
                   [sg.Button('Cancel', size=12), sg.Button('Store!', size=12, focus=True)]]

    # test global padding    popWin = sg.Window('Manual Charge Options',  layout_popC, element_padding=0)
    popWin = sg.Window('PV Options', layout_popC, location=pop_location, modal=True, icon=const.C_LOGO)
    #    p = popWin['battLevel']

    while True:
        ev2, val2 = popWin.read(100)
        popWin['battLevel'].UpdateBar(batteryLevel)
        if ev2 == sg.WIN_CLOSED or ev2 == 'Cancel':
#            pvSettings['cancelled'] = True
            break
        if ev2 == 'Store!':
            pvSettings['max_1_Ph_current'] = int(val2['-MAX_I_1_PH-'])
            pvSettings['min_3_Ph_current'] = int(val2['-MIN_I_3_PH-'])
            pvSettings['allow_3_phases'] = val2['-allow_3_phases-']
            pvSettings['chargeLimit'] = val2['-CHARGE LIMIT-']
            done = True
            break

        #        if ev2 == '-CHARGE LIMIT-':  # prevent limit lower than actuaöl battery level
        #            if val2['-CHARGE LIMIT-'] < batteryLevel:
        #                popWin['-CHARGE LIMIT-'].update(batteryLevel)
        #    print(manualSettings)

        # noinspection PySimplifyBooleanCheck
        if val2['-allow_3_phases-'] == True:
            popWin['-MIN_I_3_PH-'].update(disabled=False)
        else:
            popWin['-MIN_I_3_PH-'].update(disabled=True)

    if done:
        settings['pv'] = pvSettings
        sysSettings.writeSettings(file, settings)

    popWin.close()
    return done


if __name__ == "__main__":
    result = popSettings()
    print(result)
