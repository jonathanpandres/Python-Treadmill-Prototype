#!/usr/bin/env python
import time

from ant.core import driver
from ant.core import node

from StrideSensorTx import StrideSensorTx

# ANT+ network key
# TODO: Put the real ANT+ Network Key In Here
NETKEY = '\x00\x00\x00\x00\x00\x00\x00\x00'

antnode = None
strideSensor = None

strides = 0
distance = 0

try:
    # Initialize
    print "Initialize ANT"
    stick = driver.USB2Driver(None)
    antnode = node.Node(stick)
    antnode.start()

    key = node.NetworkKey('N:ANT+', NETKEY)
    antnode.setNetworkKey(0, key)

    print "Initialize Stride"
    strideSensor = StrideSensorTx(antnode, 1)
    strideSensor.open()

    print "Main wait loop"
    while True:
        try:
            time.sleep(.25)
            strideSensor.update(strides, distance, 2.68224)

            strides += 180 / 60 / 4
            distance += 2.68224 / 4
        except (KeyboardInterrupt, SystemExit):
            break

except Exception as e:
    print "Exception: "+repr(e)
finally:
    if strideSensor:
        print "Closing stride sensor"
        strideSensor.close()
        strideSensor.unassign()
    if antnode:
        print "Stopping ANT node"
        antnode.stop()
