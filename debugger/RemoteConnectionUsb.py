# Copyright 2018 plutoo
from RemoteConnection import *

class RemoteConnectionUsb(RemoteConnection):
    def __init__(self):
        RemoteConnection.__init__(self)

        self.dev = usb.core.find(idVendor=0x057e, idProduct=0x3000)
        if self.dev is None:
            raise Exception('Device not found')

        self.dev.set_configuration()
        self.cfg = self.dev.get_active_configuration()
        self.intf = self.cfg[(0,0)]

        self.ep_in = usb.util.find_descriptor(
            self.intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)
        assert self.ep_in is not None

        self.ep_out = usb.util.find_descriptor(
            self.intf,
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        assert self.ep_out is not None

    def read(self, size):
        data = ""
        while size != 0:
            tmp_data = self.ep_in.read(size)
            tmp_data = ''.join([chr(x) for x in tmp_data])
            size -= len(tmp_data)
            data+= tmp_data
        return data

    def write(self, data):
        size = len(data)
        tmplen = 0;
        while size != 0:
            tmplen = self.ep_out.write(data)
            size -= tmplen
            data = data[tmplen:]

