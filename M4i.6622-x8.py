#
# **************************************************************************
#
# Based on Spectrum's Example: simple_rep_fifo.py
#
# **************************************************************************
#



from pyspcm import *
from spcm_tools import *
import math
import sys
import numpy as np
import time

def vCalcNewData (pnBuffer, lNumCh, llSamplePos, llNumSamples):
    for lChIdx in range (0, lNumCh):
        for i in range (0, llNumSamples, 1):
            # calculate a sample and put the calculated value into the correct position in the DMA buffer
            pnBuffer[i * lNumCh + lChIdx] = int16(int(32767** math.sin (2.*math.pi* i/(10000))))





class M4i6622:
    def __init__(self, ReplayLength=16384, Loops=1, address=b'/dev/spcm0'):
        
        #Connect the Card
        self.hCard = spcm_hOpen (create_string_buffer (address))
        
        Valid = self.checkCard()
        if Valid == False:
            exit()

        self.lMemsize = int32(ReplayLength)  # replay length is set to whatever was put in ReplayLength
        spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE, CHANNEL0) # only one channel activated
        spcm_dwSetParam_i32 (self.hCard, SPC_CARDMODE, SPC_REP_STD_SINGLE) # set the standard single replay mode
        spcm_dwSetParam_i64 (self.hCard, SPC_MEMSIZE, self.lMemsize) # replay length
        spcm_dwSetParam_i64 (self.hCard, SPC_LOOPS, Loops) # replay memsize "Loops" times

        self.lSetChannels = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_CHCOUNT, byref (self.lSetChannels))

        self.lBytesPerSample = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (self.lBytesPerSample))
        
        

    def checkCard(self):

        #Check if Card is connected
        if self.hCard == None:
            print("no card found...\n")
            return False

        #Read the Card Type, it's function and Serial Number
        self.lCardType = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_PCITYP, byref (self.lCardType))
        self.lSerialNumber = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_PCISERIALNO, byref (self.lSerialNumber))
        self.lFncType = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_FNCTYPE, byref (self.lFncType))

        sCardName = szTypeToName (self.lCardType.value)
        if self.lFncType.value == SPCM_TYPE_AO:
            print("Found: {0} sn {1:05d}\n".format(sCardName,self.lSerialNumber.value))
            return True
        else:
            print("Code is for an M4i.6622 Card.\nCard: {0} sn {1:05d} is not supported.\n".format(sCardName,lSerialNumber.value))
            return False


    def setSoftwareBuffer(self,NotifySize=128*1024,BufferSize=32*1024*1024):

        # setup software buffer
        self.lNotifySize_bytes = int32(NotifySize) # Buffer to notify size of the packet
        self.qwBufferSize = uint64 (BufferSize) # total size of the buffer

        # we try to use continuous memory if available and big enough
        self.pvBuffer = c_void_p ()
        self.qwContBufLen = uint64 (0)
        try:
            spcm_dwGetContBuf_i64 (self.hCard, SPCM_BUF_DATA, byref(self.pvBuffer), byref(self.qwContBufLen))
            print("ContBuf length: {0:d}\n".format(self.qwContBufLen.value))
            if self.qwContBufLen.value >= self.qwBufferSize.value:
                print("Using continuous buffer\n")
            else:
                self.pvBuffer = pvAllocMemPageAligned (self.qwBufferSize.value)
                print("Using buffer allocated by user program\n")

            return 0
        except Exception as e:
            print("Exception",str(e), " occured")
            return -1





    def calculate(self, channel=0):

        try:
            qwSamplePos = 0
            self.lNumAvailSamples = (self.qwBufferSize.value // self.lSetChannels.value) // self.lBytesPerSample.value
            self.pnBuffer = cast (self.pvBuffer, ptr16)

            print("inb4")
            vCalcNewData (cast (self.pvBuffer, ptr16), self.lSetChannels.value, qwSamplePos, self.lNumAvailSamples)


            # we define the buffer for transfer and start the DMA transfer
            print("Starting the DMA transfer and waiting until data is in board memory\n")
            spcm_dwDefTransfer_i64 (self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, self.lNotifySize_bytes, self.pvBuffer, uint64 (0), self.qwBufferSize)
            spcm_dwSetParam_i32 (self.hCard, SPC_DATA_AVAIL_CARD_LEN, self.qwBufferSize)
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
            print("... data has been transferred to board memory\n")


            # now we start the generation and wait for the interrupt that signalizes the end
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)
            return 0
        except KeyboardInterrupt:
            return -1

    def stop(self):
        # send the stop command
        try:
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_DATA_STOPDMA)
            print(dwError)
            print("Card has been Stopped")
            spcm_vClose (self.hCard)
            return 0
        except Exception as e:
            print("Exception",str(e), " has occured")
            return -1



M4i = M4i6622(Loops=10)

r = M4i.setSoftwareBuffer()


r = M4i.calculate(channel = 0)

time.sleep(10)

if r == 0:
    r = M4i.stop()

print(r)
