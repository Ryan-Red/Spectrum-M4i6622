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
import mpmath



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

        self.SampleRate = MEGA(200)
        # set samplerate to 1 MHz (M2i) or 50 MHz, no clock output
        if ((self.lCardType.value & TYP_SERIESMASK) == TYP_M4IEXPSERIES) or ((self.lCardType.value & TYP_SERIESMASK) == TYP_M4XEXPSERIES):
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(200))
        else:
            spcm_dwSetParam_i64 (self.hCard, SPC_SAMPLERATE, MEGA(1))
        spcm_dwSetParam_i32 (self.hCard, SPC_CLOCKOUT,   0)

        # setup the mode
        self.qwChEnable = uint64 (1)
        self.llMemSamples = int64 (KILO_B(4*1024))
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
        self.qwBufferSize = uint64 (self.llMemSamples.value * self.lBytesPerSample.value * self.lSetChannels.value) # total size of the buffer

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





    def calculate(self,function0, function1, function2, function3):
        """
        Calculate is a function that calculates the data, stores it in the buffer and then uploads the buffer. Functions function0 to function3 are the functions 
        used in data generation, for channels 0 to 3 respectively. To use this function pass in all 4 functions (even if they are 0 functions). 
        Timeout is the time you want for the timeout, in milliseconds.
        
        In the future, will add the ability to pass in a list of functions corresponding to the amount of channels you want to use.
        """
        try:
            #Calculating the amount of samples that can be added to the buffer
            qwSamplePos = 0
            self.lNumAvailSamples = (self.qwBufferSize.value // self.lSetChannels.value) // self.lBytesPerSample.value
            self.pnBuffer = cast (self.pvBuffer, ptr16)

            #Creating and populating the buffer.
            self.pnBuffer = cast  (self.pvBuffer, ptr16)
            for i in range (0, self.llMemSamples.value, 1):
                if i%4 == 0 or self.channelNum== 1:
                    self.pnBuffer[i] = function0(i)
                elif i%4 == 1 and self.channelNum == 4:
                    self.pnBuffer[i] = function1(i)
                elif i%4 == 2 and self.channelNum == 4:
                    self.pnBuffer[i] = function2(i)
                elif i%4 == 3 and self.channelNum == 4:
                    self.pnBuffer[i] = function3(i)


            #Define the buffer for transfer and start the DMA transfer
            print("Starting the DMA transfer and waiting until data is in board memory\n")
            spcm_dwDefTransfer_i64 (self.hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32(0), self.pvBuffer, uint64 (0), self.qwBufferSize)
            spcm_dwSetParam_i32 (self.hCard, SPC_DATA_AVAIL_CARD_LEN, self.qwBufferSize)
            spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
            print("... data has been transferred to board memory\n")

            


            # We'll start and wait until the card has finished or until a timeout occurs
            spcm_dwSetParam_i32 (self.hCard, SPC_TIMEOUT, 0)
            sys.stdout.write("\nStarting the card and waiting for ready interrupt\n(continuous and single restart will have timeout)\n")
            dwError = spcm_dwSetParam_i32 (self.hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)
            if dwError == ERR_TIMEOUT:
                print("timeout has elapsed")

            
            return 0
        except KeyboardInterrupt:
            #it is also possible to stop the process before a timeout using a keyboard interrupt (Contrl+C in Windows)
            return -1

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



##################################
#                                #
#                                #
############ Test Code ###########
#                                #
#                                #
##################################


def f0(x):

    return Batman(x)


def f1(x):
    return math.floor(1000*(np.sin(x/10)))

def f2(x):
    return x

def f3(x):
    return x


def Batman(x):
    x = (x- 100000)/1000
    if abs(x) < 0.5:
        return math.floor(2.25*400*np.sin(x*300))
    elif abs(x) < 0.75:
        return math.floor(400*(3 * abs(x) + 0.75)*np.sin(x*300))
    elif abs(x) < 1:
        return math.floor(400*(9-8*abs(x))*math.sin(x*300))
    #elif abs(x) > 4 and abs(x) < 7:
    #    return math.floor(1000*(-3*math.sqrt(-(x/7)**2 + 1))*math.sin(x/10))
    elif abs(x) > 3 and abs(x) < 7:
        return math.floor(400*(3*math.pow(-(x/7)**2 + 1,0.5))*math.sin(x*300))
    elif abs(x) > 1 and abs(x) < 3:
        return math.floor(400* (1.5 - 0.5*abs(x) - 6 * math.sqrt(10)/14 *(math.sqrt(3-x**2 + 2 * abs(x)) -2))*math.sin(x*300))

    else:
        return 0
    
def sin_of_exp(x):
    x = 10*x
    return math.floor(1000 * math.sin(math.exp(x)))

def sin_of_ln(x):
    x = 10*x
    if x != 0:
        return math.floor(1000 * math.sin(math.log(x**2)))
    else:
        return 0

def weird_sin(x):
    a = 1000

    if x != a:
        return math.floor((x-a)*math.sin(1/(x-a)))
    else: 
        return 0

def gaussianEnvelope(x):
    x = x
    x0 = 1000
    sigma = 1000
    f = 200000 
    return math.floor(1000*math.exp(-(x-x0)**2 / sigma)*np.sin(x*2*math.pi*f/MEGA(200)))


def gaussianDist(x):
    x = x
    x0 = 1000
    sigma = 1000
    return math.floor(1000*math.exp(-(x-x0)**2 / sigma))

def firstOrderPolynomial(x):
    x = (x-1000)/10000
    return math.floor(x)


def sechEnvelope(x):
    T= 1000
    f = 2000000
    x0 = 100000

    return math.floor(1000*(1/np.cosh((x-x0)/T)**2) * np.sin(x*2*math.pi*f/MEGA(200))) 

def circle(x):
    x = x- 10000

    if abs(x) < 10000:
        return math.floor(1/10 *math.sqrt(10000**2 - x**2)*math.sin(x/3))
    else:
        return 0



def main():


    M4i = M4i6622(channelNum=1)

    r = M4i.setSoftwareBuffer()


    r = M4i.calculate(f0,f1,f2,f3,timeout=500000)
    time.sleep(30)
    print("continue")
    #r = M4i.calculate(f0,f1,f2,f3,timeout=500000)

    r = M4i.stop()

    print(r)
    return 0
main()
