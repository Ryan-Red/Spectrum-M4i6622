#
# **************************************************************************
#
# Based on Spectrum's Example: simple_rep_single.py
#
# **************************************************************************
#



from pyspcm import *
from spcm_tools import *
import math
import sys
import numpy as np
import time
import multiprocessing
from Functions.functions import *




class M4i6622:
    def __init__(self, address=b'/dev/spcm0',channelNum = 4):
        
        #Connect the Card
        self.hCard = spcm_hOpen (create_string_buffer (address))
        


        self.lSetChannels = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_CHCOUNT, byref (self.lSetChannels))

        self.lBytesPerSample = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (self.lBytesPerSample))


        #Read the Card Type, it's function and Serial Number
        self.lCardType = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_PCITYP, byref (self.lCardType))
        self.lSerialNumber = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_PCISERIALNO, byref (self.lSerialNumber))
        self.lFncType = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_FNCTYPE, byref (self.lFncType))


        Valid = self.checkCard()
        if Valid == False:
            exit()

        self.SampleRate = MEGA(600)

        if ((self.lCardType.value & TYP_SERIESMASK) == TYP_M4IEXPSERIES) or ((self.lCardType.value & TYP_SERIESMASK) == TYP_M4XEXPSERIES):
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, self.SampleRate)
        else:
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(1))
        spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKOUT,   0)

        # setup the mode
        self.qwChEnable = uint64 (1)
        self.llMemSamples = int64 (KILO_B(1024*16))
        self.llLoops = int64 (0) # loop continuously

        #putting the card in Continous mode
        spcm_dwSetParam_i32 (self.hCard, SPC_CARDMODE,    SPC_REP_STD_CONTINUOUS)

        #activating all 4 channels (changing the way the output is read)
        spcm_dwSetParam_i64 (self.hCard, SPC_CHENABLE,    CHANNEL0 | CHANNEL1 | CHANNEL2 | CHANNEL3)

        #Getting the total memory size to know how long the buffer should be
        spcm_dwSetParam_i64 (self.hCard, SPC_MEMSIZE,     self.llMemSamples)

        #Setting up the infinite loop
        spcm_dwSetParam_i64 (self.hCard, SPC_LOOPS,       self.llLoops)

        self.channelNum = channelNum

        if self.channelNum == 1:
            #Enable the outputs for all 4 channels
            spcm_dwSetParam_i64 (self.hCard, SPC_ENABLEOUT0,  1)

        if self.channelNum == 4:
            #Enable the outputs for all 4 channels
            spcm_dwSetParam_i64 (self.hCard, SPC_ENABLEOUT0,  1)
            spcm_dwSetParam_i64 (self.hCard, SPC_ENABLEOUT1,  1)
            spcm_dwSetParam_i64 (self.hCard, SPC_ENABLEOUT2,  1)
            spcm_dwSetParam_i64 (self.hCard, SPC_ENABLEOUT3,  1)

        #Getting total number of channels recognized by the software (4 in our case) and getting the amount of bytes per sample
        self.lSetChannels = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_CHCOUNT,     byref (self.lSetChannels))
        self.lBytesPerSample = int32 (0)
        spcm_dwGetParam_i32 (self.hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (self.lBytesPerSample))


        # setup the trigger mode
        # (SW trigger, no output)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ORMASK,      SPC_TMASK_SOFTWARE)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_ANDMASK,     0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ORMASK0,  0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ORMASK1,  0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ANDMASK0, 0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIG_CH_ANDMASK1, 0)
        spcm_dwSetParam_i32 (self.hCard, SPC_TRIGGEROUT,       0)

        spcm_dwSetParam_i64 (self.hCard, SPC_TRIG_DELAY,       0)

        lChannel0 = int32 (0)
        lChannel1 = int32 (0)
        lChannel2 = int32 (0)
        lChannel3 = int32 (0)


        #Setting up the max amplitude of each output
        if self.channelNum == 1:
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP0 + lChannel0.value * (SPC_AMP1 - SPC_AMP0), int32 (2500))
            spcm_dwSetParam_i32 (self.hCard, SPC_FILTER0, int32(1) )

        else:
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP1 + lChannel1.value * (SPC_AMP1 - SPC_AMP0), int32 (2500))
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP2 + lChannel2.value * (SPC_AMP1 - SPC_AMP0), int32 (2500))
            spcm_dwSetParam_i32 (self.hCard, SPC_AMP3 + lChannel3.value * (SPC_AMP1 - SPC_AMP0), int32 (2500))

            spcm_dwSetParam_i32 (self.hCard, SPC_FILTER0, int32(1) )
            spcm_dwSetParam_i32 (self.hCard, SPC_FILTER1, int32(1) )



    def checkCard(self):
        """
        Function that checks if the card used is indeed an M4i.6622-x8 or is compatible with AO.
        """

        #Check if Card is connected
        if self.hCard == None:
            print("no card found...\n")
            return False

        #Getting the card Name to check if it's supported.
        sCardName = szTypeToName (self.lCardType.value)
        if self.lFncType.value == SPCM_TYPE_AO:
            print("Found: {0} sn {1:05d}\n".format(sCardName,self.lSerialNumber.value))
            return True
        else:
            print("Code is for an M4i.6622 Card.\nCard: {0} sn {1:05d} is not supported.\n".format(sCardName,lSerialNumber.value))
            return False


    def setSoftwareBuffer(self):
        """
        Function to set up the SoftwareBuffer, no arguments required.
        """
        # setup software buffer
        print(self.llMemSamples.value, self.lBytesPerSample.value, self.lSetChannels.value)
        self.qwBufferSize = uint64 (self.llMemSamples.value * self.lBytesPerSample.value * self.lSetChannels.value) # total size of the buffer

        # we try to use continuous memory if available and big enough
        self.pvBuffer = c_void_p ()
        self.qwContBufLen = uint64 (0)




    def calculate(self):
        """
        Calculate is a function that calculates the data, stores it in the buffer and then uploads the buffer. Functions function0 to function3 are the functions 
        used in data generation, for channels 0 to 3 respectively. To use this function pass in all 4 functions (even if they are 0 functions). 
        Timeout is the time you want for the timeout, in milliseconds.
        
        In the future, will add the ability to pass in a list of functions corresponding to the amount of channels you want to use.
        """
        try:
            #Calculating the amount of samples that can be added to the buffer
            qwSamplePos = 0
        

            self.pvBuffer = (c_int16 * self.qwBufferSize.value)(*self.buffer)


            #Define the buffer for transfer and start the DMA transfer
            print("Starting the DMA transfer and waiting until data is in board memory\n")
            spcm_dwDefTransfer_i64 (self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32(0), self.pvBuffer, uint64 (0), self.qwBufferSize)
            spcm_dwSetParam_i32 (self.hCard, SPC_DATA_AVAIL_CARD_LEN, self.qwBufferSize)
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
            print("... data has been transferred to board memory\n")

            

            
            return 0
        except KeyboardInterrupt:
            #it is also possible to stop the process before a timeout using a keyboard interrupt (Contrl+C in Windows)
            return -1

    def startCard(self):

        # We'll start and wait until the card has finished or until a timeout occurs
        try:
 


            spcm_dwSetParam_i32 (self.hCard, SPC_TIMEOUT, 0)
            sys.stdout.write("\nStarting the card and waiting for ready interrupt\n(continuous and single restart will have timeout)\n")
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)
            if dwError == ERR_TIMEOUT:
                print("timeout has elapsed")

        except KeyboardInterrupt:
            #it is also possible to stop the process before a timeout using a keyboard interrupt (Contrl+C in Windows)
            return -1

    def setupCard(self,function0, function1, function2, function3):
        self.genBuffer(function0, function1, function2, function3)
        self.calculate()
        return 0

    def getVal(self):

        return self.llMemSamples.value
    
    def genBuffer(self,function0, function1, function2, function3):
        val = self.getVal()

        #Creating and populating the buffer.
        rangeA = np.arange(0,(int)(val/4),1)
        vect0 = function0(rangeA).astype(int)     
        vect1 = function1(rangeA).astype(int)
        vect2 = function2(rangeA).astype(int)            
        vect3 = function3(rangeA).astype(int)
        self.buffer = np.column_stack((vect0, vect1, vect2, vect3)).flatten()
        return 0



    def stop(self):
        """
        Command to stop the Card. To use card again, need to reinitialize 
        """
        #send the stop command
        try:
            
            
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_DATA_STOPDMA)
            print(dwError)
            print("Card has been Stopped")
            spcm_vClose (self.hCard)
            return 0
        except Exception as e:
            print("Exception",str(e), " has occured")
            return -1

