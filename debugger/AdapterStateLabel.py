# Copyright 2017 plutoo
from Adapter import *
from Utils import *

class AdapterStateLabel(Adapter):
    def __init__(self, label):
        self.label = label

    def onDbgEvent(self, event):
        if event is None:
            self.label.setText('Running')
        else:
            self.label.setText(repr(event))
