import time
from M4i6622 import *
from Functions.functions import *


#4 functions to be used
def f0(x):
    return gaussianEnvelope

def f1(x):
    return sin(x,f=1000)

def f2(x):
    return sin(x,f=1000)

def f3(x):
    return x





t0 = time.perf_counter()

M4i = M4i6622(channelNum=4,sampleRate=625)
r = M4i.setSoftwareBuffer()


M4i.setupCard( (f0,f1,f2,f3) )


tf = time.perf_counter() - t0
print("Done")
print("Time elapsed: {0: 10f} s".format(tf))

M4i.startCard()


r = M4i.stop()

print(r)
