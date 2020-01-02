#!/usr/bin/python
#This script was written by Darren Tapp and optimized by thephez

from decimal import Decimal
from math import log
from math import factorial as fac
from math import log1p
from math import exp



def binom(x, y):
    try:
        binom = fac(x) // fac(y) // fac(x - y)
    except ValueError:
        binom = 0
    return binom


###This function takes inputs and outputs the probability
#of success in one trial
#pcalc is short for probability calculation
def pcalc(masternodes,quorumsize,attacksuccess,Byznodes):
    SampleSpace = binom(masternodes,quorumsize)
    pctemp=0
    for x in range(attacksuccess, quorumsize+1):
        pctemp = pctemp + binom(Byznodes,x)*binom(masternodes-Byznodes,quorumsize-x)
    #at this juncture the answer is pctemp/SampleSpace
    #but that will produce an overflow error.  We use logarithms to
    #calculate this value
    return 10 ** (log(pctemp,10)- log(SampleSpace,10))

#Takes the probability of success in one trial and outputs the probability of success in 730 septillion trials
#730 septillion trials requires a septillion years of masternode quorum formation.
def ZettaYear(probability):
	trials = 2*365*10 ** 21
	return 1-exp(trials * log1p(-probability))

def MegaYear(probability):
	trials = 2*365*10 ** 6
	return 1-exp(trials * log1p(-probability))



##We evaluate the function pcalc(10,5,3,4)
##print pcalc(10,5,3,4)
##as a test vector
##The answer would be [binom(3,4)*binom(2,6)+(binom(4,4)*binom(1,6)]/binom(10,5)
##[4*15+1*6]/252 = 66/252
##print float(66)/252

##quorum size for ChainLocks
qs = 400
##Number of masternodes
mn = 5000

##Number of Byzantine nodes assuming 5000 nodes
Bft = [500,1000,1500]

##Threshold out of quorum of 400
thresh = 161

for j in range(0,3):
    print "For ", mn, " masternodes with ", Bft[j],"Byzantine the chance of withholding a ChainLock in one trial is ", pcalc(mn,qs,thresh,Bft[j])

##Now change the # threshold
thresh = 240

for j in range(0,3):
    print "For ", mn, " masternodes with ", Bft[j],"Byzantine the chance of producing a malicious ChainLock is ", pcalc(mn,qs,thresh,Bft[j])


#In the case of a smaller number of masternodes
mn=2000

##Number of Byzantine nodes assuming 2000 nodes
Bft = [240,400,600]

##Threshold out of quorum of 400
thresh = 161

for j in range(0,3):
    print "For ", mn, " masternodes with ", Bft[j],"Byzantine the chance of withholding a ChainLock in one trial is ", pcalc(mn,qs,thresh,Bft[j])

##Now change the # threshold
thresh = 240

for j in range(0,3):
    print "For ", mn, " masternodes with ", Bft[j],"Byzantine the chance of producing a malicious ChainLock is ", pcalc(mn,qs,thresh,Bft[j])


print "Security interpretation:"

print "For 5000 masternodes with 1500 Byzantine nodes the chance of producing a malicious ChainLock is ", pcalc(5000,400,240,1500)
print "Which means in a Zettayear the chances of a "
print "malicious chainlock is ", ZettaYear(pcalc(5000,400,240,1500))


print "In an extreme case the chance of quorum control with 40% of nodes:"
print "5000 Masternodes ", pcalc(5000,400,240,2000)
print "2000 Masternodes ", pcalc(2000,400,240,800)
print "In an even more extreme case the chance of quorum control with 50% of nodes:"
print "5000 Masternodes ", pcalc(5000,400,240,2500)
print "2000 Masternodes ", pcalc(2000,400,240,1000)

print MegaYear(pcalc(5000,400,240,2000))
print "For 2000 total nodes with 200 attacking , the chance of withholding a ChainLock is,", pcalc(2000,400,161,200)
