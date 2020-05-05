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

# random signal frequencies for up to four channels in Hertz
# if you change these you might want to change SPC_SAMPLERATE, too
adSignalFrequency_Hz = [ 35000, 11723, 27000, 9800 ]

def vCalcNewData (pnBuffer, lNumCh, llSamplePos, llNumSamples):
    for lChIdx in range (0, lNumCh):
        for i in range (0, llNumSamples, 1):
            # calculate a sample and put the calculated value into the correct position in the DMA buffer
            pnBuffer[i * lNumCh + lChIdx] = int16(int(32767*i)) # * math.sin (2.*math.pi*(llSamplePos + i)/(10000))))


class M4i6622:
    def __init__(self, ReplayLength=16384, Loops=1):
        
        #Connect the Card
        self.hCard = spcm_hOpen (create_string_buffer (b'/dev/spcm0'))
        
        Valid = self.checkCard()
        if Valid == False:
            exit()

        self.lMemsize = int32(ReplayLength)  # replay length is set to whatever was put in ReplayLength
        spcm_dwSetParam_i32 (self.hCard, SPC_CHENABLE, CHANNEL0) # only one channel activated
        spcm_dwSetParam_i32 (self.hCard, SPC_CARDMODE, SPC_REP_STD_SINGLE) # set the standard single replay mode
        spcm_dwSetParam_i64 (self.hCard, SPC_MEMSIZE, self.lMemsize) # replay length
        spcm_dwSetParam_i64 (self.hCard, SPC_LOOPS, Loops) # replay memsize "Loops" times

        self.lSetChannels = int32 (0)
        spcm_dwGetParam_i32 (hCard, SPC_CHCOUNT, byref (self.lSetChannels))

        self.lBytesPerSample = int32 (0)
        spcm_dwGetParam_i32 (hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (self.lBytesPerSample))
        
        

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
        spcm_dwGetParam_i32 (self.hCard, SPC_FNCTYPE, byref (lFncType))

        sCardName = szTypeToName (lCardType.value)
        if lFncType.value == SPCM_TYPE_AO:
            print("Found: {0} sn {1:05d}\n".format(sCardName,lSerialNumber.value))
            return True
        else:
            print("Code is for an M4i.6622 Card.\nCard: {0} sn {1:05d} is not supported.\n".format(sCardName,lSerialNumber.value))
            return False


    def setSoftwareBuffer(self,NotifySize=128*1024,BufferSize=32*1024*1024,):

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




    def vCalcNewData(self, channel=0):
        for i in range (0, llNumSamples, 1):
            # calculate a sample and put the calculated value into the correct position in the DMA buffer
            pnBuffer[i * 4 + channel] = int16(int(32767*i)) # * math.sin (2.*math.pi*(llSamplePos + i)/(10000))))
    
    def calculate(self):
        while True:
            try:
                qwSamplePos = 0
                lNumAvailSamples = (qwBufferSize.value // lSetChannels.value) // lBytesPerSample.value
                vCalcNewData (cast (pvBuffer, ptr16), lSetChannels.value, qwSamplePos, lNumAvailSamples)


                # we define the buffer for transfer and start the DMA transfer
                print("Starting the DMA transfer and waiting until data is in board memory\n")
                spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, lNotifySize_bytes, pvBuffer, uint64 (0), qwBufferSize)
                spcm_dwSetParam_i32 (hCard, SPC_DATA_AVAIL_CARD_LEN, qwBufferSize)
                spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
                print("... data has been transferred to board memory\n")


                # now we start the generation and wait for the interrupt that signalizes the end
                spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)

            except KeyboardInterrupt:
                return -1

    def stop(self):
        # send the stop command
        try:
            dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_DATA_STOPDMA)
            print(dwError)
            spcm_vClose (hCard)
            return 0
        except Exception as e:
            print("Exception",str(e), " has occured")
            return -1



M4i = M4i6622()

r = M4i.setSoftwareBuffer()

if r == 0:
    r = M4i.calculate()

if r == 0:
    r = M4i.stop()

print(r)





# #
# # **************************************************************************
# # main 
# # **************************************************************************
# #

# # open card
# # uncomment the second line and replace the IP address to use remote
# # cards like in a generatorNETBOX
# hCard = spcm_hOpen (create_string_buffer (b'/dev/spcm0'))
# #hCard = spcm_hOpen (create_string_buffer (b'TCPIP::192.168.1.10::inst0::INSTR'))
# if hCard == None:
#     sys.stdout.write("no card found...\n")
#     exit ()


# # read type, function and sn and check for D/A card
# lCardType = int32 (0)
# spcm_dwGetParam_i32 (hCard, SPC_PCITYP, byref (lCardType))
# lSerialNumber = int32 (0)
# spcm_dwGetParam_i32 (hCard, SPC_PCISERIALNO, byref (lSerialNumber))
# lFncType = int32 (0)
# spcm_dwGetParam_i32 (hCard, SPC_FNCTYPE, byref (lFncType))

# sCardName = szTypeToName (lCardType.value)
# if lFncType.value == SPCM_TYPE_AO:
#     sys.stdout.write("Found: {0} sn {1:05d}\n".format(sCardName,lSerialNumber.value))
# else:
#     sys.stdout.write("This is an example for D/A cards.\nCard: {0} sn {1:05d} not supported by example\n".format(sCardName,lSerialNumber.value))
#     exit ()



# lMemsize = int32(16384)  # replay length is set to 16 kSamples
# spcm_dwSetParam_i32 (hCard, SPC_CHENABLE, CHANNEL0) # only one channel activated
# spcm_dwSetParam_i32 (hCard, SPC_CARDMODE, SPC_REP_STD_SINGLE) # set the standard single replay mode
# spcm_dwSetParam_i64 (hCard, SPC_MEMSIZE, lMemsize) # replay length
# spcm_dwSetParam_i64 (hCard, SPC_LOOPS, 10) # replay memsize 10 times


# lSetChannels = int32 (0)
# spcm_dwGetParam_i32 (hCard, SPC_CHCOUNT, byref (lSetChannels))
# lBytesPerSample = int32 (0)
# spcm_dwGetParam_i32 (hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (lBytesPerSample))




# # setup software buffer
# lNotifySize_bytes = int32(128 * 1024) # 128 kB
# qwBufferSize = uint64 (32*1024*1024) # 32 MByte. For simplicity qwBufferSize should be a multiple of lNotifySize_bytes
# # we try to use continuous memory if available and big enough
# pvBuffer = c_void_p ()
# qwContBufLen = uint64 (0)
# spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
# sys.stdout.write ("ContBuf length: {0:d}\n".format(qwContBufLen.value))
# if qwContBufLen.value >= qwBufferSize.value:
#     sys.stdout.write("Using continuous buffer\n")
# else:
#     pvBuffer = pvAllocMemPageAligned (qwBufferSize.value)
#     sys.stdout.write("Using buffer allocated by user program\n")

# # calculate the data
# # we calculate data for all enabled channels, starting at sample position 0, and fill the complete DMA buffer

# while True:
#     qwSamplePos = 0
#     lNumAvailSamples = (qwBufferSize.value // lSetChannels.value) // lBytesPerSample.value
#     vCalcNewData (cast (pvBuffer, ptr16), lSetChannels.value, qwSamplePos, lNumAvailSamples)


#     # we define the buffer for transfer and start the DMA transfer
#     sys.stdout.write("Starting the DMA transfer and waiting until data is in board memory\n")
#     spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, lNotifySize_bytes, pvBuffer, uint64 (0), qwBufferSize)
#     spcm_dwSetParam_i32 (hCard, SPC_DATA_AVAIL_CARD_LEN, qwBufferSize)
#     spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
#     sys.stdout.write("... data has been transferred to board memory\n")


#     # now we start the generation and wait for the interrupt that signalizes the end
#     spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY);







# # send the stop command
# dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_DATA_STOPDMA)
# print(dwError)
# spcm_vClose (hCard);

