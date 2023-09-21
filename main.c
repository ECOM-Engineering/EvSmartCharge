/*! @addtogroup CONTROL
@{*/

////////////////////////////////////////////////////////////////////////////////
/*! @file        main.c
//  @brief       Includes main() and basic initial functions
//  @author      Klaus Mezger
//
*///////////////////////////////////////////////////////////////////////////////

//#define _USE_CAN //symbol defined in Eclipse build configuration
//todo ERROR in jsmn.c, da json file nicht vollständig


#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>

#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <limits.h>

//== module headers ==
#include "jsmn.h"
#include "NET_TLS/GetSSLdata.h"
#include "Parser.h"
#include "SysData.h"
#include "CloudAccess.h"
#include "scheduler.h"

//#include "HexConversions.h"
#include "version.h"
#include "terminal.h"
#include "CAN.h"
#include "Logfile.h"


//== local defines
#define MAX_FILENAME            64
#define CONSOLE_FORMAT_FILE     "WPL25_console.csv"
#define CAN_TIMER               10 //seconds

//==local typedefs

//== module global variables

//== functions

///////////////////////////////////////////////////////////////////////////////
/*! @brief      Read parameter definitions from csv file
//  @param[in]  *RefFile            parameter description
//  @param[in]  ParamArraySize     size of par description array
//  @param[out] *ParamDef           see #sParam_t
//  @return     line number, 0 if not found
//
//
*//////////////////////////////////////////////////////////////////////////////

int16_t getParamDef(FILE *RefFile, sParam_t *ParamDefArray, uint16_t ParamArraySize)
{
  int16_t   found;
  sParam_t  *ParamDef;
  char      RefFileLine[PARAM_LINE_LEN];
  char      HexStr[8];
  char      *token;
  float     temp;
  char      *dummy;
  uint32_t   i;

  memset(HexStr, 0, 8);
  strcpy(HexStr, "0x");

  found = -1;
  fseek(RefFile, 0 , SEEK_SET);

  //skip 1st line (column names)
  fgets(RefFileLine, PARAM_LINE_LEN, RefFile);

  while (fgets(RefFileLine, PARAM_LINE_LEN, RefFile) != NULL)
  {
      if (strstr(RefFileLine, HexStr) != NULL)
      {
          found++;
      }
      else
      {
          break;
      }

      if (found >= 0) //parse parameter definition
      {

           ParamDef = &ParamDefArray[found];
          i = sizeof(sParam_t);
          memset(ParamDef, 0, i);

          token = strtok(RefFileLine, ",");           //column 1: Param ID hex
          if (token) strcpy(ParamDef->xParamIndex, token);
          ParamDef->ParamIndex = (uint16_t)strtol(ParamDef->xParamIndex, &dummy, 16);

          token = strtok(NULL, ",");                  //column 2: CAN hex
          if (token) strcpy(ParamDef->xCAN_ID, token);
          ParamDef->CAN_ID = (uint16_t)strtol(ParamDef->xCAN_ID, &dummy, 16);

          token = strtok(NULL, ",");                        //column 3
          if (token) strcpy(ParamDef->ParamName, token);

          token = strtok(NULL, ",");                        //column 4
          if (token) ParamDef->ParamFormat = (uint8_t)atoi(token);

          token = strtok(NULL, ",");                        //column 5
          if (token) ParamDef->ParamType = (uint8_t)atoi(token);

          token = strtok(NULL, ",");                        //column 6
          if (token) ParamDef->selectionLetter = token[0];

          token = strtok(NULL, ",");                        //column 7
          if (token)
          {
              temp = strtof(token, &dummy);
              ParamDef->LimitLo = (uint16_t)(temp * 10);
          }

          token = strtok(NULL, ",");                        //column 8
          if (token)
          {
              temp = strtof(token, &dummy);
              ParamDef->LimitHi = (uint16_t)(temp * 10);
          }
      }
  }

  return (found + 1);
}

///////////////////////////////////////////////////////////////////////////////
/*! @brief      Read and parse system parameters from ini.json file
//  @param[in]  *RefFile            file handle to ini.json
//  @param[out] *sSysControl
//  @return     number of tokens read. < 0 on error
//
//
*//////////////////////////////////////////////////////////////////////////////
int fGetSystemIni(const char *iniFile, sSysControl_t *sSysControl)
{
       int i, j;
       char weatherServer[128];
       char weatherAPI[200];
       char solarServer[128];
       char solarAPI[200];

    /* get key parameters */
    i = ParseIniFile(iniFile, "station_1", sSysControl);
    j = strcspn(sSysControl->strKeyURL, "/");  //length of server name
    if (j < sizeof(weatherServer))
    {
      strncpy(weatherServer,sSysControl->strKeyURL, j);
      weatherServer[j] = 0; //terminate
    }
    else return -1;
    strcpy(weatherAPI, &sSysControl->strKeyURL[j]);

    /* get PV keys from ini file */
    j = strcspn(sSysControl->strPV_URL, "/");  //length of server name
    if (j < sizeof(solarServer))
    {
      strncpy(solarServer,sSysControl->strPV_URL, j);
      solarServer[j] = 0; //terminate
    }
    else return -1;
    strcpy(solarAPI, &sSysControl->strPV_URL[j]);

    strcpy(sSysControl->weatherServer, weatherServer);
    strcpy(sSysControl->weatherAPI, weatherAPI);
    strcpy(sSysControl->solarServer, solarServer);
    strcpy(sSysControl->solarAPI, solarAPI);

    return i;
}



/** @brief Helper function similar to kbhit() from win32 not available in linux */
int kbhit(void)
{
  struct termios oldt, newt;
  int ch;
  int oldf;

  tcgetattr(STDIN_FILENO, &oldt);
  newt = oldt;
  newt.c_lflag &= ~(ICANON | ECHO);
  tcsetattr(STDIN_FILENO, TCSANOW, &newt);
  oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
  fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);

  ch = getchar();

  tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
  fcntl(STDIN_FILENO, F_SETFL, oldf);

  if(ch != EOF)
  {
    ungetc(ch, stdin);
    return 1;
  }

  return 0;
}

///////////////////////////////////////////////////////////////////////////////
/*! @brief      setting up and main control loop
//  @param[in]  n.a.
//  @param[out] n.a.
//  @return     number of tokens read. < 0 on error
//
//  <b>important: define symbol _USE_CAN for use with target.</b>
*//////////////////////////////////////////////////////////////////////////////

int main(int argc, char *argv[]) {
    char        *pchr;
    int         i;
    int         CAN_status;
    int         Can_socket;
    char        messageString[80];

    FILE         *RefFile;
//    char        workingPath[MAX_PATH];
    char         filePath[MAX_PATH + MAX_FILENAME];
    char         pathToLogFile[MAX_PATH];
    uint16_t     paramsFound;
    sParam_t     ParamDefArray[MAX_PARAMS];
    int          retVal;
    int          selectionKey, valueChanged; //keyboard
    sParEdit_t   sParEdit;
    sSysControl_t sSysData;
    eLogType_t    logType;

    char statusString[MAX_STATUS_MSG_LEN] ;
    char infoString[MAX_STATUS_MSG_LEN] ;


    int         secTimer, oldSecTimer, preScaler;
    time_t      utcTime;
    struct tm   *pLocalTime, *pForecastTime;
    char        timeString[20];

    sSchedule_t scheduleList[MAX_LINES];
    int         jobsCount; //number of jobs
    eJob_t      job;
    boilerCmd_t boilerValues;
    int         pvTokensFound;

    memset(statusString, 0, sizeof(statusString));
    memset(infoString, 0, sizeof(infoString));
    memset(messageString, 0, sizeof(messageString));
    memset(sSysData.workingPath, 0, sizeof(sSysData.workingPath));

    pchr = strrchr(argv[0], '/');
    i = pchr - argv[0];

    if(i < MAX_PATH)
        strncpy(sSysData.workingPath, argv[0], i + 1); //strip prog name and get path including '/'
    retVal = 0;
    selectionKey = 0;
    secTimer = 0;
    oldSecTimer = 0;
    preScaler = 0;
    utcTime = time(NULL);
    sSysData.currentUTC = utcTime;


    /* get general in file */
    sprintf(filePath, "%s%s", sSysData.workingPath, "ini.json");
    retVal = fGetSystemIni(filePath ,&sSysData); //basic settings for environment parameters
    if (retVal < 0)
    {
        printf("\r\nError in file ini.json");
        goto PROG_END;
    }

    if(strlen(sSysData.logfilePath) > 0)
        strcpy (pathToLogFile, sSysData.logfilePath);
    else
        strcpy(pathToLogFile, sSysData.workingPath); //default


    /* get console and HP parameter definition*/
    sprintf(filePath, "%s%s", sSysData.workingPath, CONSOLE_FORMAT_FILE);
    RefFile = fopen(filePath, "rb");
    if (RefFile == NULL)
    {
        printf("\r\nSorry, cannot open %s", filePath);
        goto PROG_END;
    }
    paramsFound = getParamDef(RefFile, ParamDefArray, sizeof(ParamDefArray));
    fclose(RefFile);

    memset(scheduleList, 0, sizeof(scheduleList));

    sprintf(filePath, "%s%s", sSysData.workingPath, SCHEDULE_PLAN);
    RefFile = fopen(filePath, "rb");
    if (RefFile == NULL)
    {
        printf("\r\nSorry, cannot open %s", filePath);
        goto PROG_END;
    }
    jobsCount = ParseSchedule(RefFile, scheduleList);
    fclose(RefFile);


#ifdef _USE_CAN
    /* initializes CAN interface */
    puts("\r\n Initializing CAN interface...");
     // for socket and parameters see
     // https://www.kernel.org/doc/html/latest/networking/can.html
     retVal = system("sudo ip link set up can0 type can bitrate 20000");
     if (retVal == 0)
     {
         puts ("SPI CAN controller found");
     }
     else     //SPI device can0 not found --> check USB device
     {
          i = attachUSB_CANdevice("-o -s1 -t hw -S 3000000", "can0", messageString, sizeof(messageString));
           if (i == 0)
              puts(messageString);
          else
              goto CAN_ERROR;
     }
     system("sudo ip link set up can0");
     Can_socket = CANinit();
     if(Can_socket <= 0)
        goto CAN_ERROR;

    printf(" done!");

    CAN_status = CANreadConsoleParams(ParamDefArray, paramsFound);
    if(CAN_status <= 0)
    {
        printf("\r\nERROR: could not read console params");
        goto CAN_ERROR;
    }

    strcpy(statusString,"Start CAN init done");
#endif
    printStatus(statusString);
    format_screen(paramsFound, ParamDefArray);

    utcTime = time(NULL);
    sSysData.currentUTC = utcTime;
    logType = user;
    sprintf(infoString,"power up V. "C_BUILD_DATE"");

    AddLogEntry(ParamDefArray, paramsFound, &sSysData, infoString, logType);

    boilerValues.daySetTemp = sSysData.boilerDayLow;
    boilerValues.nightSetTemp = sSysData.boilerNightLow;


    while(1)
    {
    	if(kbhit())
    	{
    	  selectionKey = getc(stdin);
	      fflush(stdin); //remove remaining '\n'
    	  if(selectionKey == 'x') goto PROG_END;
          valueChanged = parseKeyCommand(selectionKey, paramsFound, ParamDefArray, &sParEdit);
          if (valueChanged > 0)
          {
               printf("writing Parameter 0x%04x value %4.1f",
               sParEdit.ParamIndex, (float)(sParEdit.ParamValue)/10);
#ifdef _USE_CAN
               CAN_status = CANwriteConsoleParam(&sParEdit);
               printf("\r\nParam 0x%04X written",sParEdit.ParamIndex);
#endif
               logType = user;
               sprintf(infoString,"writing Par. 0x%04x value %4.1f",
               sParEdit.ParamIndex, (float)(sParEdit.ParamValue)/10);

               AddLogEntry(ParamDefArray, paramsFound,
               &sSysData, infoString, logType);
          }
    	}
        if(secTimer != oldSecTimer) //1s polling cycle
        {
            oldSecTimer = secTimer;
            utcTime = time(NULL);
            pLocalTime = localtime(&utcTime);

            strftime(timeString, sizeof(timeString)-1,"%F %R", pLocalTime);

            /* job management follows */
            sSysData.currentUTC = utcTime;
            logType = log;
            EvalJob(scheduleList, jobsCount, *pLocalTime);
            for (job = 0; job< jobsCount; job++)
            {
                if(scheduleList[job].jobState == TRIGGERED)
                {
                    ExecJob(&scheduleList[job], &boilerValues, &sSysData); //execute core job
                    switch (job)                                           //manage job depending on jobState
                    {
                        case HP_LOG:
                            if(scheduleList[job].jobState == READY)
                            {
                                pvTokensFound = fGetPVpower(&sSysData);
                                if(pvTokensFound > 0){
                                  logType = log;
                                }
                                else {
                                    logType = error;
                                    sprintf(infoString, "Error reading PV JSON string");
                                    printInfo(infoString);
                                }
                                AddLogEntry(ParamDefArray, paramsFound,
                                &sSysData, "", logType);
                            }
                            scheduleList[job].jobState = IDLE;

                            break;

                        case HP_RESET:
                            if(scheduleList[HP_RESET].jobState == DONE)
                            {
                                scheduleList[HP_ACTIVATION].jobState = IDLE;
                                scheduleList[HP_FORECAST].jobState = IDLE;
                                sSysData.useSolarPower = false;
                                sprintf(statusString, "%s Prepare new forecast", timeString);
                                sprintf(infoString, "--> set boiler d: %d  n: %d",
                                     boilerValues.daySetTemp, boilerValues.nightSetTemp);
                                printStatus(statusString);
                                printInfo(infoString);
                           }
                            break;
                        case HP_ACTIVATION:
                            switch(scheduleList[HP_ACTIVATION].jobState)
                            {
                                case DONE:
                                    scheduleList[HP_RESET].jobState = IDLE;
                                    scheduleList[HP_FORECAST].jobState = IDLE;
                                    sprintf(statusString, "%s solar power: %1.2fkW", timeString, sSysData.actualPower);
                                    if(sSysData.useSolarPower)
                                        sprintf(infoString,"-> Using solar power. Set boiler d: %d  n: %d", boilerValues.daySetTemp, boilerValues.nightSetTemp);
                                     else
                                        sprintf(infoString,"-> PV power not sufficient. Set boiler d: %d  n: %d", boilerValues.daySetTemp, boilerValues.nightSetTemp);
                                    printStatus(statusString);
                                    printInfo(infoString);
                                    break;

                                case FAILED: //server problem
                                    scheduleList[job].jobState = RETRY;
                                    sprintf(statusString, "%s No connection to solar server, retry %d", timeString, scheduleList[job].retry_count);
                                    snprintf(infoString,sizeof(infoString)-1, "No connection %s", sSysData.solarServer);
                                    printStatus(statusString);
                                    printInfo(infoString);
                                    break;

                                case RETRY:
                                    sprintf(statusString, "%s solar power: %1.2fkW -> retry", timeString, sSysData.actualPower);
                                    sprintf(infoString, "retry %d",scheduleList[job].retry_count);
                                    printStatus(statusString);
                                    printInfo(infoString);
                                    break;

                                case TIMED_OUT:
                                    break;

                                default:
                                    break;
                            } //switch jobState

                            break;

                        case HP_FORECAST:
                            pForecastTime = localtime(&sSysData.forecastUTC);
                            strftime(timeString, sizeof(timeString)-1,"%F %R", pForecastTime);
                            switch(scheduleList[HP_FORECAST].jobState)
                            {
                                case DONE:
                                    scheduleList[HP_RESET].jobState = IDLE;
                                     scheduleList[HP_ACTIVATION].jobState = IDLE;
                                     sprintf(statusString, "Forecast for %s: clouds:%02d%%  Temp:%02.1f°C",
                                              timeString, sSysData.forecastClouds,  sSysData.forecastTemp);

                                     if(sSysData.forecastSun)
                                         sprintf(infoString, "Expecting PV power. Set boiler d: %d  n: %d",
                                                 boilerValues.daySetTemp, boilerValues.nightSetTemp);
                                     else
                                         sprintf(infoString, "Using mains power. Set boiler d: %d  n: %d",
                                                 boilerValues.daySetTemp, boilerValues.nightSetTemp);
                                     printStatus(statusString);
                                     printInfo(infoString);

                                    break;

                                case FAILED: //server problem
                                    scheduleList[job].jobState = RETRY;
                                    sprintf(statusString, "Forecast for %s, retry %d: failed", timeString, scheduleList[job].retry_count);
                                    strftime(timeString, sizeof(timeString)-1,"%F %R", pLocalTime);
                                    sprintf(infoString, "%s No connection to weather server", timeString);
                                    printStatus(statusString);
                                    printInfo(infoString);
                                    break;

                                case TIMED_OUT:
                                    break;

                                default:
                                    break;
                                }
                           break;

                        default:
                            break;

                    }

                    if(scheduleList[job].jobState == DONE)
                    {
    #ifdef _USE_CAN
                        /* write to CAN */
                        sParEdit.CAN_ID = 0x180; //todo take from parameter csv file
                        sParEdit.ParamIndex = sSysData.boilerDayIndex;
                        sParEdit.ParamValue = boilerValues.daySetTemp * 10; //scale factor of HP
                        CAN_status = CANwriteConsoleParam(&sParEdit);
                        printf("  done");
                        usleep(500000);
                        if (CAN_status <= 0) goto CAN_ERROR;
                        sParEdit.CAN_ID = 0x180;
                        sParEdit.ParamIndex = sSysData.boilerNightIndex;
                        sParEdit.ParamValue = boilerValues.nightSetTemp * 10; //scale factor of HP
                        CAN_status = CANwriteConsoleParam(&sParEdit);
                        printf("  done");
                        usleep(500000);
                        if (CAN_status <= 0) goto CAN_ERROR;
                        printf("\r\nParameters written to machine");
                        CAN_status = CANreadConsoleParams(ParamDefArray, paramsFound);
                        format_screen(paramsFound, ParamDefArray);
    #endif
                    }
                    /* manage event log entries */
                    switch(scheduleList[job].jobState)
                    {
                        case TRIGGERED:
                        case RETRY: //todo if job == activation, 1st and last retry only
                        case DONE:
                            logType = action;
                            AddLogEntry(ParamDefArray, paramsFound,
                            &sSysData, infoString, logType);

                            break;
                        case TIMED_OUT:
                        case FAILED:
                            logType = error;
                            AddLogEntry(ParamDefArray, paramsFound,
                            &sSysData, infoString, logType);
                            break;
                        default:
                            break;
                    }
                }
            }
            /* timing control */

            if((secTimer % CAN_TIMER) == 0) //10 second rate
            {
#ifdef _USE_CAN
               CAN_status = CANreadConsoleParams(ParamDefArray, paramsFound);
#endif
               format_screen(paramsFound, ParamDefArray);
            }
        }

    	usleep(100000);         //100ms keyscan timebase. Allow other apps.
        preScaler ++;
         if(preScaler >= 10)    //seconds interval
         {
             preScaler = 0;
             secTimer ++;
         }
    }

#ifdef _USE_CAN
    close(Can_socket);
    goto PROG_END;
#endif
 CAN_ERROR:
     logType = error;
     printf("\r\nCAN Error occured \r\n");
     sprintf(infoString,"CAN Error occured: exit program");
     AddLogEntry(ParamDefArray, paramsFound, &sSysData, infoString, logType);
     return -1;

    PROG_END:
     logType = user;
     sprintf(infoString,"manual exit program");
     AddLogEntry(ParamDefArray, paramsFound, &sSysData, infoString, logType);


 return retVal;

}
#ifdef  __cplusplus
}
#endif

/*! @} */ //end of doxygen module group
