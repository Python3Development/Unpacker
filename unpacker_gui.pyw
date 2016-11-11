import os
import sys
from time import time
from PyQt5 import QtWidgets, QtGui, QtCore
from unpacker import resources, util, view

RED = QtGui.QBrush(QtCore.Qt.red)


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.__setup()
        self.__menu()
        self.__layout()
        self.setWindowTitle('Unpacker')
        self.setWindowIcon(util.icon('app.png'))
        self.resize(800, 600)

    # region Setup
    def __setup(self):
        self.__dir = None
        self.__root_dir = None

    def __menu(self):
        # Status Bar
        self.__status_bar = self.statusBar()
        font = QtGui.QFont()
        font.setPointSize(7)
        self.__status_bar.setFont(font)

        # Menu Bar
        menu_bar = self.menuBar()

        # Menu Actions
        action_import = QtWidgets.QAction(util.icon('folder.png'), '&Import', self)
        action_import.setShortcut('Ctrl+I')
        action_import.triggered.connect(lambda: self.__import(QtWidgets.QFileDialog.getExistingDirectory(parent=self)))

        action_quit = QtWidgets.QAction(util.icon('close.png'), '&Exit', self)
        action_quit.setShortcut('Shift+F4')
        action_quit.triggered.connect(QtWidgets.qApp.quit)

        # Menu
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(action_import)
        file_menu.addSeparator()
        file_menu.addAction(action_quit)

    def __layout(self):
        parent = QtWidgets.QWidget()
        self.setCentralWidget(parent)

        # Tree Layout
        tree_layout = QtWidgets.QHBoxLayout()

        self.__tree_widget = view.RTreeWidget(parent)
        tree_layout.addWidget(self.__tree_widget)

        self.__projection_tree_widget = view.RTreeWidget(parent)
        tree_layout.addWidget(self.__projection_tree_widget)

        # Button Layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(QtWidgets.QLabel('Tiers:', parent))

        self.__tier_spin_box = QtWidgets.QSpinBox(parent)
        self.__tier_spin_box.setFixedWidth(40)
        self.__tier_spin_box.setMinimum(1)
        self.__tier_spin_box.valueChanged.connect(self.__handle_spin_box_value_change)
        button_layout.addWidget(self.__tier_spin_box)

        self.__all_tiers_checkbox = QtWidgets.QCheckBox('All', parent)
        self.__all_tiers_checkbox.stateChanged.connect(self.__handle_check_box_state_change)
        button_layout.addWidget(self.__all_tiers_checkbox)

        button_layout.addSpacerItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding))

        self.__unpack_button = QtWidgets.QPushButton('Unpack', parent)
        self.__unpack_button.clicked.connect(self.__handle_unpack_button_click)
        button_layout.addWidget(self.__unpack_button)

        root_layout = QtWidgets.QVBoxLayout(parent)
        root_layout.addLayout(tree_layout)
        root_layout.addLayout(button_layout)
    # endregion

    # region Handlers
    def __handle_spin_box_value_change(self, value):
        if self.__dir:
            self.__projection_tree_widget.clear()
            self.__repopulate_projection_tree_tiers(self.__tree_widget.invisibleRootItem(), value)

    def __handle_check_box_state_change(self, state):
        checked = (state == QtCore.Qt.Checked)
        self.__tier_spin_box.setSpecialValueText('All' if checked else None)
        self.__tier_spin_box.setDisabled(checked)
        if self.__dir:
            self.__repopulate_projection_tree(checked)

    def __handle_unpack_button_click(self):
        if self.__dir:
            self.__status_bar.showMessage('Processing')
            self.__execute()
    # endregion

    # region Methods
    def __import(self, dir_):
        if dir_:
            self.__dir = dir_
            self.__populate()
            self.__repopulate_projection_tree(self.__all_tiers_checkbox.isChecked())

    # Tree
    def __populate(self):
        self.__tree_widget.clear()
        self.__build_tree_recursive(self.__dir, self.__tree_widget.invisibleRootItem())

    def __build_tree_recursive(self, path, parent):
        item = self.__add_tree_item(path, parent, os.path.basename(path))
        for f in os.scandir(path):
            if f.is_dir():
                self.__build_tree_recursive(f.path, item)
            else:
                self.__add_tree_item(f.path, item, os.path.basename(f.path), False)

    # Projection Tree
    def __repopulate_projection_tree(self, all_):
        self.__projection_tree_widget.clear()
        if all_:
            self.__repopulate_projection_tree_all(self.__tree_widget.invisibleRootItem())
        else:
            self.__repopulate_projection_tree_tiers(self.__tree_widget.invisibleRootItem(),
                                                    self.__tier_spin_box.value())

    def __repopulate_projection_tree_tiers(self, parent_, tiers):
        for i in range(parent_.childCount()):
            child_ = parent_.child(i)
            if child_.childCount() > 0 and tiers != 0:
                self.__repopulate_projection_tree_tiers(child_, tiers - 1)
            else:
                clone = child_.clone()
                self.__check_projection_conflict(clone)
                self.__projection_tree_widget.invisibleRootItem().addChild(clone)

    def __repopulate_projection_tree_all(self, parent_):
        for i in range(parent_.childCount()):
            child_ = parent_.child(i)
            if child_.childCount() > 0:
                self.__repopulate_projection_tree_all(child_)
            else:
                clone = child_.clone()
                self.__check_projection_conflict(clone)
                self.__projection_tree_widget.invisibleRootItem().addChild(clone)

    def __check_projection_conflict(self, child):
        for i in range(self.__projection_tree_widget.invisibleRootItem().childCount()):
            child_ = self.__projection_tree_widget.invisibleRootItem().child(i)
            if child_.text(0) == child.text(0):
                child.setForeground(0, RED)
    # endregion

    # region Helpers
    def __add_tree_item(self, file, parent, title, dir_=True):
        item = QtWidgets.QTreeWidgetItem(parent, [title])
        item.setIcon(0, util.file_icon(file))
        if dir_:
            item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
        return item
    # endregion

    # region Script
    def __execute(self):
        if self.__dir and os.path.exists(self.__dir):
            self.__root_dir = os.path.dirname(self.__dir)
            start = time()
            if self.__all_tiers_checkbox.isChecked():
                self.__unpack_all(self.__dir)
            else:
                self.__unpack(self.__dir, self.__tier_spin_box.value())
            self.__dir = None
            self.__status_bar.showMessage('Done in {:.2f} s'.format(time() - start))

    def __unpack_all(self, path):
        for f in os.scandir(path):
            if f.is_dir():
                self.__unpack_all(f.path)
            else:
                self.__move_up(f.path)
        # EAFP (Easier to Ask Forgiveness than Permission)
        try:
            # Try to delete (empty) directory
            os.rmdir(path)
        except OSError:
            # Means directory wasn't empty
            print('Failed: {} not empty'.format(path))

    def __unpack(self, path, tier):
        for f in os.scandir(path):
            if f.is_dir() and tier != 1:
                self.__unpack(f.path, tier - 1)
            else:
                self.__move_up(f.path)
        # EAFP (Easier to Ask Forgiveness than Permission)
        try:
            # Try to delete (empty) directory
            os.rmdir(path)
        except OSError:
            # Means directory wasn't empty
            print('Failed: {} not empty'.format(path))

    def __move_up(self, file):
        file_name = os.path.basename(file)
        try:
            os.rename(file, os.path.join(self.__root_dir, file_name))
        except OSError:
            print('Failed: {} already exists'.format(self.__root_dir + file_name))

    # endregion
    pass


# region Exception Hook
sys._excepthook = sys.excepthook

def my_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = my_exception_hook
# endregion


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    try:
        sys.exit(app.exec_())
    except:
        pass
