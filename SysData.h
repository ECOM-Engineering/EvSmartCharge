/*
 * AnalyzeWeather.h
 *
 *  Created on: 02.03.2018
 *      Author: Klaus
 */

#ifndef SYSDATA_H_
#define SYSDATA_H_

#define DEBUG_PRINT

//== constants
#define MAX_PATH                256
#define MAX_PARAMS              80
#define PARAM_LINE_LEN          81


#include <time.h>
#include "version.h"

typedef struct {
    /* weatherdata from ini file*/
    char strKeyUTC[100];      //JSON key
    char strKeyURL[150];      //JSON key
    char strKeyClouds[24];    //JSON key
    char strKeyTemp[24];      //JSON key
    char strKeySolar[24];     //JSON key
    char strKeySolarPower[24];//JSON key
    char weatherServer[80];
    char weatherAPI[200];
    int maxClouds;            //maximum clouds for using PV

    /* PV data from ini file */
    char solarServer[80];
    char solarAPI[200];
    char strPV_URL[150];
    float minPower;           //minimum solar power for heating boiler

    /* Boiler Limits from ini file*/
    int boilerDayHigh;
    int boilerDayLow;
    int boilerNightHigh;
    int boilerNightLow;
    int boilerDayIndex;    //CAN ID
    int boilerNightIndex;  //CAN ID

    /* directories */
    char logfilePath[MAX_PATH];   //from ini file
    char workingPath[MAX_PATH];   //from program

    /* weather data read from weather server */
    time_t currentUTC;
    int currentClouds;
    float currentTemp;
    time_t forecastUTC;
    int forecastClouds;
    float forecastTemp;

    /* PV data read from PV cloud server */
    float actualPower;        //from solar Edge

    /* PV results */
    int useSolarPower;  //true: actually enough solar power
    int forecastSun;    //true: expecting enough solar power
 }sSysControl_t;


#endif /* SYSDATA_H_ */
