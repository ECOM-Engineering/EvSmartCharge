import PySimpleGUI as sg
import const

#todo replace limit text limit sign by graph
#sg.theme('DarkBlue3')
#sg.theme('SystemDefault')
#sg.theme("SystemDefaultForReal")

sg.theme_progress_bar_border_width(1)
barRelief = 'RELIEF_SUNKEN RELIEF'

sg.SetOptions(button_element_size=(11, 1),auto_size_buttons=False, font=('Helvetica', 11, ))

batLevelBar = sg.ProgressBar(100, orientation='h', size=(25, 14), key='-battBar-',
                             relief=barRelief, bar_color=('spring green', '#9898A0'))
chargePwrBar = sg.ProgressBar(const.C_CHARGER_MAX_POWER, orientation='h', size=(25, 14), key='-chargeBar-',
                              relief=barRelief, bar_color=('#00BFFF', '#9898A0'))
solarPwrBar = sg.ProgressBar(6, orientation='h', size=(25, 14), key='-solarBar-',
                             relief=barRelief, bar_color=('yellow', '#9898A0'))
solarPwr2GridBar = sg.ProgressBar(6, orientation='h', size=(25, 14), key='-toGridBar-',
                                  relief=barRelief, bar_color=('yellow', '#9898A0'))
messageText = sg.Text('Initializing ...', key='-MESSAGE-', size=50, text_color='#FDFDFF',
                      background_color ='#64778D', border_width=1)

battDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-batt-')
solarDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-solar-')
chargeDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-charge-')
chargeCurrentDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-chargeCurr-')
phasesDisp = sg.Text(0, size=(3, 1), pad=(0, 0), justification='right', key='-measuredPhases-')
toGridDisp = sg.Text(0, size=(4, 1), pad=(0, 0), justification='right', key='-toGrid-')

def LEDIndicator(key=None, radius=30):
    return sg.Graph(canvas_size=(radius, radius),
                    graph_bottom_left=(-radius, -radius),
                    graph_top_right=(radius, radius),
                    pad=(0, 0), key=key)


def SetLED(win, key, color):
    graph = win[key]
    graph.erase()
    graph.draw_circle((0, 0), 12, fill_color=color, line_color='black')


#for test only
limit_sign = '▲'
limit_val = 67  # corresponds to 100%

col1 =  [
        [sg.Frame(title='Battery Level', size=(500, 80),
         layout=[
         [batLevelBar, battDisp, sg.Text('% ', pad=0), sg.Text('---', key='-CHARGE_STATE-', pad=8, size=(17, 1))],
         [sg.Text(limit_val * ' ' + limit_sign, font=("Arial", 12, "bold"), key='-LIMIT_VAL-', pad=(0, 0), text_color='green1')]])
#         [battLimit, sg.Text("Limit", pad=(10, 0, 0))]])
         ],
        [sg.Text("")],

        [sg.Frame(title='Charging Power', size=(500,80), layout=[
        [chargePwrBar, chargeDisp, sg.Text('kW', pad=0), chargeCurrentDisp, sg.Text('A', pad=0), phasesDisp, sg.Text('Phase')],
        [LEDIndicator('-LED_SOLAR-'),  sg.Text('Solar     ', pad=0),
         LEDIndicator('-LED_FORCED-'), sg.Text('Forced    ', pad=0),
         LEDIndicator('-LED_EXTERN-'), sg.Text('Extern', pad=0)]])],
        [sg.Text("")],

        [sg.Frame(title='Solar Power',  size=(500,75), layout=[
        [solarPwrBar, solarDisp, sg.Text('kW', pad=0), sg.Text('PV total power')],
        [solarPwr2GridBar, toGridDisp, sg.Text('kW', pad=0), sg.Text('PV power to grid')]])],
        [sg.Text("")],  # empty line
        [sg.Frame(title='Messages', size=(500,50), layout=[
        [messageText, sg.Stretch(), LEDIndicator('-LED_MSG-')]])]]
#       [sg.Text('Initializing ...', key='-MESSAGE-', size=53, text_color ='grey10', background_color ='light grey')]])]]

layout = [[sg.Column(col1)],
          [sg.Button('Force Charge', disabled=True), sg.Button('Stop Charge', disabled=True),
           sg.Button('PV-Settings'), sg.Button('Quit')]
          ]

# create window`
window = sg.Window('ECOM EVS-1 Smart Solar Charging', layout, icon=const.C_LOGO)


def testLayout():
    while 1:
        event, values = window.read(timeout=200)
        if event == 'Quit' or event == sg.WIN_CLOSED:
            quit()
        window['-battBar-'].UpdateBar(50)
        SetLED(window,'-LED_SOLAR-', 'grey')
        SetLED(window,'-LED_FORCED-', 'white')
        SetLED(window,'-LED_EXTERN-', 'grey')
        SetLED(window,'-LED_MSG-', 'grey')

if __name__ == "__main__":
    testLayout()
    window.close()






