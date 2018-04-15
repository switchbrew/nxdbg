.PHONY: all

all: mainwindow_gen.py

mainwindow_gen.py: mainwindow.ui
	pyuic4 $^ > $@
