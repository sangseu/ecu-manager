import numpy
from scipy import ndimage
from scipy.interpolate import interp1d, interp2d

from PyQt4 import QtCore, QtGui
from PyQt4 import uic

class TableViewWidget(QtGui.QWidget):
    """
    Table view widget
    """

    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.initUi()
        self.init_data()
        self.update()

    def initUi(self):
        self.ui = uic.loadUi('ui/resources/table_view_widget.ui', self)

        self.ui.tableWidget.setRowCount(16)
        self.ui.tableWidget.setColumnCount(16)
        self.ui.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.ui.tableWidget.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)

        for i in range(self.ui.tableWidget.columnCount()):
            for j in range(self.ui.tableWidget.rowCount()):
                self.ui.tableWidget.setItem(i, j, QtGui.QTableWidgetItem())

        self.ui.tableWidget.cellChanged.connect(self.cell_changed)
        self.ui.tableWidget.customContextMenuRequested.connect(self.cell_context_menu)
        self.ui.tableWidget.keyPressed.connect(self.key_pressed)
        self.ui.interpButton.clicked.connect(self.interp_data)
        self.ui.filterButton.clicked.connect(self.filter_data)
        self.ui.clearButton.clicked.connect(self.clear_data)

    def init_data(self):
        """Initialize data array"""

        self.data = [[0 for i in range(16)] for j in range(16)]

    def update(self):
        """Update table values"""

        QtGui.QWidget.update(self)

        for i in range(self.ui.tableWidget.rowCount()):
            for j in range(self.ui.tableWidget.columnCount()):
                self.ui.tableWidget.item(i, j).setText('%.2f' % self.data[i][j])
                # colorize cell
                g = int(255 - self.data[i][j] / 1 * 96)

                if g < 0:
                    g = 0
                elif g > 255:
                    g = 255

                color = QtGui.QColor(255, g, 128)
                self.ui.tableWidget.item(i, j).setBackground(color)

    def interp_data(self):
        """Interpolate selected data"""

        if len(self.ui.tableWidget.selectedRanges()) > 0:
            sel = self.ui.tableWidget.selectedRanges()[0]

            row_count = sel.rowCount()
            column_count = sel.columnCount()

            if row_count == 1 and column_count == 1:
                return

            x = sel.leftColumn();
            _x = sel.rightColumn()
            y = sel.topRow()
            _y = sel.bottomRow()
            z = [[self.data[y][x], self.data[y][_x]], [self.data[_y][x], self.data[_y][_x]]]

            if row_count == 1 and column_count > 1:
                z = interp1d([x, _x], z[0])(range(x, _x + 1))
                z = [z.tolist()]

            elif column_count == 1 and row_count > 1:
                z = interp1d([y, _y], [z[0][0], z[1][0]])(range(y, _y + 1))
                z = numpy.array([z]).T.tolist()

            else:
                z = interp2d([x, _x], [y, _y], z)(range(x, _x + 1), range(y, _y + 1))
                z = z.tolist()

            self.modify_selected(sel, z)

    def filter_data(self):
        """Filter selected data"""

        self.data = ndimage.gaussian_filter(self.data, 0.5)
        self.update()

    def clear_data(self):
        """Clear all data"""

        if len(self.ui.tableWidget.selectedRanges()) > 0:
            sel = self.ui.tableWidget.selectedRanges()[0]
            self.modify_selected(sel, 0)

    def modify_selected(self, selection, value, method='set'):
        """Modify selected cells"""

        x = selection.leftColumn();
        _x = selection.rightColumn()
        y = selection.topRow()
        _y = selection.bottomRow()

        if isinstance(value, (list, tuple)):
            for i in range(y, _y + 1):
                for j in range(x, _x + 1):
                    self.data[i][j] = value[i - y][j - x]

        else:
            for i in range(y, _y + 1):
                for j in range(x, _x + 1):
                    if method == 'set':
                        self.data[i][j] = value
                    elif method == 'inc':
                        self.data[i][j] += value
                    elif method == 'dec':
                        self.data[i][j] -= value
            
        self.update()        

    def cell_edit_dialog(self):
        """Cell edit dialog"""

        value, ok = QtGui.QInputDialog.getDouble(self, 'Enter Value', '', 0, -65535, 65535, 2)

        if not ok:
            return 

        if len(self.ui.tableWidget.selectedRanges()) > 0:
            sel = self.ui.tableWidget.selectedRanges()[0]
            self.modify_selected(sel, value)

    def cell_changed(self, row, column):
        """Cell changed slot"""

        cell = self.ui.tableWidget.item(row, column)

        try:
            value = float(cell.text())
        except ValueError:
            value = 0

        self.data[row][column] = value
        cell.setText('%.2f' % value)

    def cell_context_menu(self, pos):
        """Cell context menu"""

        menu = QtGui.QMenu('Actions', self.ui.tableWidget)
        menu.addAction('Edit').triggered.connect(self.cell_edit_dialog)
        menu.addAction('Clear').triggered.connect(self.clear_data)
        menu.addAction('Interpolate').triggered.connect(self.interp_data)
        menu.addAction('Filter').triggered.connect(self.filter_data)
        menu.exec_(self.ui.tableWidget.mapToGlobal(pos))

    def key_pressed(self, event):
        if len(self.ui.tableWidget.selectedRanges()) > 0:
            sel = self.ui.tableWidget.selectedRanges()[0]
            key = event.key()

            if key == QtCore.Qt.Key_Plus:
                self.modify_selected(sel, 0.01, method='inc')

            elif key == QtCore.Qt.Key_Minus:
                self.modify_selected(sel, 0.01, method='dec')
