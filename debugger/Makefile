all: mainwindow_gen.py
	python2 MainWindow.py

mainwindow_gen.py: mainwindow.ui
	pyuic4 $^ > $@
