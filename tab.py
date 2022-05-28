import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore, QtGui

class WindowTableau(QWidget):

    def __init__(self, list_component, functions):
        super().__init__()
        self.title = 'Tableau'
        self.list_component = list_component
        self.functions = functions
        self.initUI()

    def create_table(self):
        # Create table
        row = len(self.list_component)
        column = len(self.list_component[0])
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(row)
        self.tableWidget.setColumnCount(column)
        for i in range(0, row):
            for j in range(0, column):
                if type(self.list_component[i][j]) != list:
                    self.tableWidget.setItem(i, j, QTableWidgetItem(self.list_component[i][j]))
                    self.tableWidget.item(i, j).setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                else:
                    self.tableWidget.setItem(i, j, QTableWidgetItem(", ".join(self.list_component[i][j])))
                    self.tableWidget.item(i, j).setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)


        # table selection change
        self.tableWidget.clicked.connect(self.on_click)

    def initUI(self):
        self.setWindowIcon(QtGui.QIcon("logoFablab.png"))
        self.setWindowTitle(self.title)
        self.setGeometry(0, 32, 339, 267)

        self.create_table()

        # Add box layout, add table to box layout and add box layout to widget
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

        # Show widget
        self.show()

    def highlight_via_draw(self, clicked_label):

        for index, element in enumerate(self.list_component[1:]):
            if type(element[0]) != list:
                if element[0] == clicked_label:
                    for i in range(self.tableWidget.columnCount()):
                        for j in range(1, self.tableWidget.rowCount()):
                            self.tableWidget.item(j, i).setSelected(False)
                        self.tableWidget.item(index+1, i).setSelected(True)
            else:
                for sub_element in element[0]:
                    if sub_element == clicked_label:
                        for i in range(self.tableWidget.columnCount()):
                            for j in range(1, self.tableWidget.rowCount()):
                                self.tableWidget.item(j, i).setSelected(False)
                            self.tableWidget.item(index+1, i).setSelected(True)

    @pyqtSlot()
    def on_click(self):
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            for i in range(self.tableWidget.columnCount()):
                self.tableWidget.item(currentQTableWidgetItem.row(), i).setSelected(True)
                clicked_line = self.list_component[currentQTableWidgetItem.row()][0]
        self.functions.onClickTab(clicked_line)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window2 = WindowTableau()
    sys.exit(app.exec())
