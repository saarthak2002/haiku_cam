#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>

// https://github.com/nopnop2002/Raspberry-ili9225spi
#include "ili9225.h"

#define _DEBUG_ 0
#define WAIT sleep(5)

int ReadTFTConfig(char *path, int *width, int *height, int *offsetx, int *offsety) {
    FILE *fp;
    char buff[128];
  
    fp = fopen(path,"r");
    if(fp == NULL) return 0;
    while (fgets(buff,128,fp) != NULL) {

        if (buff[0] == '#') continue;
        if (buff[0] == 0x0a) continue;
        
        if (strncmp(buff, "width=", 6) == 0) {
            sscanf(buff, "width=%d height=%d",width,height);
        } 
        else if (strncmp(buff, "offsetx=", 8) == 0) {
            sscanf(buff, "offsetx=%d",offsetx);
        }
        else if (strncmp(buff, "offsety=", 8) == 0) {
            sscanf(buff, "offsety=%d",offsety);
        }
    }
    fclose(fp);
    return 1;
}


int main(int argc, char **argv) {
    int i;
    int screenWidth = 0;
    int screenHeight = 0;
    int offsetx = 0;
    int offsety = 0;
    char dir[128];
    char cpath[128];

    strcpy(dir, argv[0]);
    for(i=strlen(dir);i>0;i--) {
        if (dir[i-1] == '/') {
          dir[i] = 0;
          break;
        }
    }

    strcpy(cpath,dir);
    strcat(cpath,"tft.conf");

    if (ReadTFTConfig(cpath, &screenWidth, &screenHeight, &offsetx, &offsety) == 0) {
        printf("%s Not found\n",cpath);
        return 0;
    }

    if(_DEBUG_) {
        printf("Your TFT resolution is %d x %d.\n",screenWidth, screenHeight);
        printf("Your TFT offsetx    is %d.\n",offsetx);
        printf("Your TFT offsety    is %d.\n",offsety);
    }

    // Load in the fonts
    FontxFile fx32G[2];
    FontxFile fx24G[2];
    FontxFile fx16G[2];
    Fontx_init(fx32G,"/home/saarthak/ili9225spi_rpi/fontx/ILGH32XB.FNT","./fontx/ILGZ32XB.FNT"); // 16x32Dot Gothic
    Fontx_init(fx24G,"/home/saarthak/ili9225spi_rpi/fontx/ILGH24XB.FNT","./fontx/ILGZ24XB.FNT"); // 12x24Dot Gothic
    Fontx_init(fx16G,"/home/saarthak/ili9225spi_rpi/fontx/ILGH16XB.FNT","./fontx/ILGZ16XB.FNT"); // 8x16Dot Gothic

    lcdInit(screenWidth, screenHeight, offsetx, offsety);
    lcdReset();
    lcdSetup();

    uint16_t color;
    unsigned char utf8[64];;
    
    lcdFillScreen(BLACK);
    color = WHITE;
    lcdSetFontDirection(DIRECTION0);

    uint16_t xpos = 215;
    uint16_t ypos = 160;
    uint16_t f_width = 8;
    uint16_t f_height = 16;

    if(strcmp(argv[1], "load") == 0) {
        lcdDrawUTF8String(fx16G, ypos, xpos-5, "Generating your Haiku...", color);
        return 0;
    }

    if(strcmp(argv[1], "ip") == 0) {
        lcdDrawUTF8String(fx16G, ypos, xpos-5, argv[2], color);
        lcdDrawUTF8String(fx16G, 20, xpos-5, "Ready!", color);
        return 0;
    }

    if(strcmp(argv[1], "ready") == 0) {
        lcdDrawUTF8String(fx24G, 100, 146, "Ready!", color);
        return 0;
    }

    if(strcmp(argv[1], "qr") == 0) {
        int ROWS = 132;
        int COLS = 132;
        char *qr_array = argv[2];
        size_t length = 0;
        while (qr_array[length] != '\0') {
            length++;
        }

        int *binaryArray = (int *)malloc(length * sizeof(int));
        for (size_t i = 0; i < length; i++) {
            binaryArray[i] = qr_array[i] - '0';
        }

        uint16_t xpos_qr = 176;
        uint16_t ypos_qr = 150;
        
        for(size_t i=0;i<ROWS;i++) {
            for(size_t j=0;j<COLS;j++) {
                int px_val = binaryArray[i*ROWS+j];
                if(px_val == 0) {
                    lcdDrawPixel(ypos_qr, xpos_qr, WHITE);
                }
                xpos_qr = xpos_qr - 1;
            }
            ypos_qr = ypos_qr - 1;
            xpos_qr = 176;
        }
   
        free(binaryArray);
        return 0;
    }

    for(int i=1; i<4;i++) {
        char *token;
        token = strtok(argv[i], " ");
        while (token != NULL) {

            if((xpos - (f_width * strlen(token))) > 215) {
                ypos = ypos - f_height;
                xpos = 215;
            }

            lcdDrawUTF8String(fx16G, ypos, xpos, token, color);

            xpos = xpos - (f_width * strlen(token));

            // Get the next token
            token = strtok(NULL, " ");
            if(token != NULL) {
                xpos = xpos - f_width;
                lcdDrawUTF8String(fx16G, ypos, xpos, " ", color);
            }
        }
        ypos = ypos - f_height;
        xpos = 215;
    }

    WAIT;
    lcdDrawUTF8String(fx16G, 20, 215, "Showing QR Code soon...", color);

    return 0;
}
