/* 
 * File:   utils.h
 * Author: Klaus
 *
 * Created on 19. Januar 2018, 10:18
 */

#ifndef VERSION_H
#define	VERSION_H

#include <stdint.h>
#include <stdio.h>

#include <linux/can.h>
#include <linux/can/raw.h>
#include <stdbool.h>
#include "CAN.h"
#include "SysData.h"

#define V_String "Build "
#define C_HDR_STR "HeatPump Interface Build " __DATE__"\r\n"
#define C_BUILD_DATE __DATE__


#endif	/* VERSION_H */

