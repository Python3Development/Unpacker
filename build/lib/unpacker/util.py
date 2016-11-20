from PyQt5 import QtGui, QtCore, QtWidgets

PROVIDER = QtWidgets.QFileIconProvider()


# Image
def icon(name):
    return QtGui.QIcon(':/img/{}'.format(name))


def file_icon(file):
    return PROVIDER.icon(QtCore.QFileInfo(file))


# GUI
def tree_item(parent, value, icon_=None, indicator=True, data=None):
    item = QtWidgets.QTreeWidgetItem(parent, [value])
    if icon_:
        item.setIcon(0, icon_)
    if indicator:
        item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
    if data:
        item.setData(0, QtCore.Qt.UserRole, data)
    return item
