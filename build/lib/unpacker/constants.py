from PyQt5 import QtCore, QtGui


class Color(object):
    RED = QtGui.QBrush(QtCore.Qt.red)
    GREEN = QtGui.QBrush(QtCore.Qt.darkGreen)
    GRAY = QtGui.QBrush(QtCore.Qt.gray)
    BLUE = QtGui.QBrush(QtCore.Qt.blue)


class String(object):
    FILE = 'File'
    DIRECTORY = 'Directory'
