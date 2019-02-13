import struct
import sys
import time

from ant.core import message
from ant.core.constants import *
from ant.core.exceptions import ChannelError

# Transmitter for Stride (Foot Pod) Sensor
class StrideSensorTx(object):
    CHANNEL_PERIOD = 8134
    DEVICE_TYPE = 0x7C
    FREQUENCY = 57
    NAME = 'C:SDM'

    class StrideData:
        def __init__(self):
            pass

    def __init__(self, antnode, sensor_id):
        self.antnode = antnode

        self.page1 = SDM_Page1()
        self.page80 = SDM_Page80()
        self.page81 = SDM_Page81()

        self.dataPageCount = 0
        self.commonPageCount = 0

        # Get the channel
        self.channel = antnode.getFreeChannel()
        try:
            self.channel.name = StrideSensorTx.NAME
            self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_TRANSMIT)
            self.channel.setID(StrideSensorTx.DEVICE_TYPE, sensor_id, 0)
            self.channel.setPeriod(StrideSensorTx.CHANNEL_PERIOD)
            self.channel.setFrequency(StrideSensorTx.FREQUENCY)
        except ChannelError as e:
            print "Channel config error: "+e.message

        #self.strideData = StrideSensorTx.StrideData()

    def open(self):
        self.channel.open()

    def close(self):
        self.channel.close()

    def unassign(self):
        self.channel.unassign()

    def update(self, strides, distance, speed):
        self.page1.update(strides, distance, speed)

        if self.dataPageCount < 64:                 # 0-63
            payload = self.page1.getMessage()
        else:                                       # 64
            if self.commonPageCount < 2:            # 0-1
                payload = self.page80.getMessage()
            else:                                   # 2-3
                payload = self.page81.getMessage()

            self.commonPageCount = (self.commonPageCount + 1) % 4

        self.dataPageCount = (self.dataPageCount + 1) % 65

        print payload.encode('hex')

        ant_msg = message.ChannelBroadcastDataMessage(self.channel.number, data=payload)
        sys.stdout.write('+')
        sys.stdout.flush()
        self.antnode.driver.write(ant_msg.encode())


class SDM_Page1(object):
    def __init__(self):
        self.dataPageNumber = 0x01
        self.time_fractional = 0x00 # 1/200 second
        self.time_integer = 0x00 # seconds
        self.distance_integer = 0x00 # meters
        self.distance_fractional = 0x00 # Upper Nibble, 1/16 meter
        self.instantaneous_speed_integer = 0x00 # Lower Nibble, meters/second
        self.instantaneous_speed_fractional = 0x00 # 1/256 meters/second
        self.stride_count = 0x00 # Accumulated strides
        self.update_latency = 0x00 # The time elapsed between the last speed and distance computation and the
                                   # transmission of this message. 1/32 second

    def update(self, strides, distance, speed):
        self.stride_count = int(strides) & 0xff
        self.distance_integer = int(distance) & 0xff
        self.distance_fractional = int((distance % 1) * 16)
        self.instantaneous_speed_integer = int(speed) & 0xff
        self.instantaneous_speed_fractional = int((speed % 1) * 256)

    def getMessage(self):
        #01 00 00 1f 60 00 9d 00
        return struct.pack("<BBBBBBBB", self.dataPageNumber, self.time_fractional, self.time_integer, self.distance_integer,
                           ((self.distance_fractional & 0x0f) << 4) | (self.instantaneous_speed_integer & 0x0f),
                           self.instantaneous_speed_fractional, self.stride_count, self.update_latency)


# class SDM_Page2(object):


# class SDM_Page3(object):


# class SDM_Page16(object):


# class SDM_Page22(object):


class SDM_Page80(object):
    def __init__(self):
        self.dataPageNumber = 0x50
        self.hardwareRevision = 0x01
        self.manufacturerId_LSB = 0x01
        self.manufacturerId_MSB = 0x00
        self.modelNumber_LSB = 0xff
        self.modelNumber_MSB = 0xff

    def getMessage(self):
        return struct.pack("<BBBBBBBB", self.dataPageNumber, 0xff, 0xff, self.hardwareRevision, self.manufacturerId_LSB,
                           self.manufacturerId_MSB, self.modelNumber_LSB, self.modelNumber_MSB)


class SDM_Page81(object):
    def __init__(self):
        self.dataPageNumber = 0x51
        self.softwareVersion = 0x01
        self.serialNumber = 0xffffffff

    def getMessage(self):
        return struct.pack("<BBBBL", self.dataPageNumber, 0xff, 0xff, self.softwareVersion, self.serialNumber)