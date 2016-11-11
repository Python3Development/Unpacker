from PyQt5 import QtGui, QtCore, QtWidgets

PROVIDER = QtWidgets.QFileIconProvider()


# Image
def icon(name):
    return QtGui.QIcon(':/img/{}'.format(name))


def file_icon(file):
    return PROVIDER.icon(QtCore.QFileInfo(file))


