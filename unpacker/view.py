from PyQt5 import QtWidgets


class RTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)

    def contextMenuEvent(self, event):
        position = event.pos()
        item = self.itemAt(position)
        if item and item.childCount() > 0:
            menu = QtWidgets.QMenu()
            if item.isExpanded():
                action = QtWidgets.QAction('Collapse all')
                action.triggered.connect(lambda: self.__collapse_tree(item))
                menu.addAction(action)
            else:
                action = QtWidgets.QAction('Expand all')
                action.triggered.connect(lambda: self.__expand_tree(item))
                menu.addAction(action)
            menu.exec_(self.viewport().mapToGlobal(position))
        return QtWidgets.QTreeWidget.contextMenuEvent(self, event)

    def __expand_tree(self, parent):
        parent.setExpanded(True)
        for i in range(parent.childCount()):
            self.__expand_tree(parent.child(i))

    def __collapse_tree(self, parent):
        for i in range(parent.childCount()):
            self.__collapse_tree(parent.child(i))
        parent.setExpanded(False)
