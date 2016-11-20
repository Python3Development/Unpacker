import os
import sys
from time import time
from PyQt5 import QtWidgets, QtGui, QtCore
from unpacker import resources, util, view, constants

ALL_TIERS = -1


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
        self.dir = None
        self.root_dir = None
        self.count = 0

    def __menu(self):
        # Status Bar
        self.status_bar = self.statusBar()
        font = QtGui.QFont()
        font.setPointSize(7)
        self.status_bar.setFont(font)

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

        self.tree_widget = view.RTreeWidget(parent)
        tree_layout.addWidget(self.tree_widget)

        self.projection_tree_widget = view.RTreeWidget(parent)
        tree_layout.addWidget(self.projection_tree_widget)

        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)

        # Action Layout
        action_layout = QtWidgets.QHBoxLayout()
        action_layout.addWidget(QtWidgets.QLabel('Tiers:', parent))

        self.tier_spin_box = QtWidgets.QSpinBox(parent)
        self.tier_spin_box.setFixedWidth(40)
        self.tier_spin_box.setMinimum(1)
        self.tier_spin_box.valueChanged.connect(self.__project)
        action_layout.addWidget(self.tier_spin_box)

        self.all_tiers_checkbox = QtWidgets.QCheckBox('All', parent)
        self.all_tiers_checkbox.stateChanged.connect(self.__handle_check_box_state_change)
        action_layout.addWidget(self.all_tiers_checkbox)

        action_layout.addSpacerItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding))

        self.unpack_button = QtWidgets.QPushButton('Unpack', parent)
        self.unpack_button.clicked.connect(self.__handle_unpack_button_click)
        action_layout.addWidget(self.unpack_button)

        root_layout = QtWidgets.QVBoxLayout(parent)
        root_layout.addLayout(tree_layout)
        root_layout.addWidget(self.progress_bar)
        root_layout.addLayout(action_layout)

    # endregion

    # region Handlers
    def __handle_check_box_state_change(self, state):
        checked = (state == QtCore.Qt.Checked)
        self.tier_spin_box.setSpecialValueText('All' if checked else None)
        self.tier_spin_box.setDisabled(checked)
        self.__project()

    def __handle_unpack_button_click(self):
        if self.dir:
            self.status_bar.showMessage('Unpacking 0/{}'.format(self.count))
            self.__execute()

    # endregion

    # region Methods
    def __import(self, dir_):
        if dir_:
            self.dir = dir_
            self.__populate()
            self.__project()

    # Tree
    def __populate(self):
        self.tree_widget.clear()
        self.__build_tree_recursive(self.dir, self.tree_widget.invisibleRootItem())

    def __build_tree_recursive(self, path, parent):
        item = util.tree_item(parent, os.path.basename(path), util.file_icon(path), data=constants.String.DIRECTORY)
        for f in os.scandir(path):
            if f.is_dir():
                self.__build_tree_recursive(f.path, item)
            else:
                util.tree_item(item, os.path.basename(f.path), util.file_icon(f.path), indicator=False, data=constants.String.FILE)

    # Projection Tree
    def __project(self):
        self.projection_tree_widget.clear()
        if self.all_tiers_checkbox.isChecked():
            self.count = self.__project_tiers(self.tree_widget.invisibleRootItem(), -1)
        else:
            self.count = self.__project_tiers(self.tree_widget.invisibleRootItem(), self.tier_spin_box.value())

    def __project_tiers(self, parent_, tiers):
        count = 0
        for i in range(parent_.childCount()):
            child_ = parent_.child(i)
            if child_.data(0, QtCore.Qt.UserRole) == constants.String.DIRECTORY and tiers != 0:
                count += self.__project_tiers(child_, tiers - 1)
            else:
                clone = child_.clone()
                self.__mark_omission(clone)
                self.projection_tree_widget.invisibleRootItem().addChild(clone)
                count += 1
        return count

    def __mark_omission(self, child):
        for i in range(self.projection_tree_widget.invisibleRootItem().childCount()):
            child_ = self.projection_tree_widget.invisibleRootItem().child(i)
            if child_.text(0) == child.text(0):
                child.setForeground(0, constants.Color.GRAY)
                if 'Duplicate' not in child.text(0):
                    child.setText(0, child.text(0) + ' (Duplicate)')
    # endregion

    # region Script
    def __execute(self):
        if self.dir and os.path.exists(self.dir):
            self.root_dir = os.path.dirname(self.dir)
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, self.count)
            start = time()
            if self.all_tiers_checkbox.isChecked():
                self.__unpack(self.dir, -1)
            else:
                self.__unpack(self.dir, self.tier_spin_box.value())
            self.status_bar.showMessage('Done in {:.2f} s'.format(time() - start))
            self.dir = None
            self.tree_widget.clear()
        else:
            self.status_bar.showMessage('Path not found')

    def __unpack(self, path, tier):
        for f in os.scandir(path):
            if f.is_dir() and tier != 1:
                self.__unpack(f.path, tier - 1)
            else:
                self.__move_up(f.path)
        # EAFP (Easier to Ask Forgiveness than Permission)
        try:
            os.rmdir(path)
        except OSError:
            print('Delete Failed: {} not empty'.format(path))

    def __move_up(self, file):
        file_name = os.path.basename(file)
        current = self.progress_bar.value() + 1
        self.progress_bar.setValue(current)
        self.status_bar.showMessage('Unpacking {}/{}'.format(current, self.count))
        try:
            os.rename(file, os.path.join(self.root_dir, file_name))
        except OSError:
            print('Move Failed: {} already exists'.format(file_name))
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
