from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
from functools import partial
import math

from tab import *
from functions import *

# fonction qui verifie si mon label est cliqué, que l'on appelle dans draw_target()
def clickable(widget):

    class Filter(QObject):
        clicked = pyqtSignal()

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked


class Window(QWidget):

    def __init__(self, big_list_coo, functions):
        super().__init__()

        self.list_component_with_id = []

        self.big_list_coo = big_list_coo

        self.title = "PCB"

        self.functions = functions

        self.widthWin = 1024
        self.heightWin = 500

        self.label_list = [[], [], []]

        self.current_label = []

        self.multiple_label = 0

        self.InitWindow()

    # creation des parametres de la fenetre
    def InitWindow(self):
        self.setWindowIcon(QtGui.QIcon("logoFablab.png"))
        self.setWindowTitle(self.title)
        self.setGeometry(340, 30, self.widthWin, self.heightWin)
        self.show()

    # fonction integré permettant de dessiner des formes, ne peut pas etre appelée. Appelée auto par rafraichissement
    def paintEvent(self, e):
        if self.isActiveWindow():  # verifie si on ets sur cette fenetre (PCB)
            self.clear_current_label()  # Clear tout les label entouré via le Tab
        painter = QPainter(self)
        for list_coo in self.big_list_coo:
            if type(list_coo[4]) == int:
                painter.setPen(QPen(Qt.gray, list_coo[4]))
                painter.drawLine(list_coo[0], list_coo[1], list_coo[2], list_coo[3])
            elif list_coo[4] == "RECTANGULAR":  # bloc pour dessiner un rectangle ABCD
                painter.setPen(QPen(Qt.gray, 2))
                # attribution des coordonnées respectives des points ABCD
                Ax = list_coo[0]
                Ay = list_coo[1]
                Bx = Ax + list_coo[2]
                By = Ay
                Cx = Bx
                Cy = By + list_coo[3]
                Dx = Ax
                Dy = Cy
                if list_coo[5] != 0:  # verification de la rotation de la piece (donc si differente de 0)
                    # calculs pour connaitre les nouvelles coo des points apres la rotation par rapport au point A
                    Bxp = (Bx-Ax) * math.cos(math.radians(list_coo[5])) + (By-Ay) * -math.sin(math.radians(list_coo[5])) + Ax
                    Byp = (Bx-Ax) * math.sin(math.radians(list_coo[5])) + (By-Ay) * math.cos(math.radians(list_coo[5])) + Ay
                    Cxp = (Cx-Ax) * math.cos(math.radians(list_coo[5])) + (Cy-Ay) * -math.sin(math.radians(list_coo[5])) + Ax
                    Cyp = (Cx-Ax) * math.sin(math.radians(list_coo[5])) + (Cy-Ay) * math.cos(math.radians(list_coo[5])) + Ay
                    Dxp = (Dx-Ax) * math.cos(math.radians(list_coo[5])) + (Dy-Ay) * -math.sin(math.radians(list_coo[5])) + Ax
                    Dyp = (Dx-Ax) * math.sin(math.radians(list_coo[5])) + (Dy-Ay) * math.cos(math.radians(list_coo[5])) + Ay
                    list_points = [[Ax, Bxp, Cxp, Dxp], [Ay, Byp, Cyp, Dyp]]
                    # regarde quel point est le plus en haut, en bas, a droite, et a gauche
                    # pour pouvoir centrer correctement le rectangle
                    max_x = max(list_points[0])
                    min_x = min(list_points[0])
                    max_y = max(list_points[1])
                    min_y = min(list_points[1])
                    w_to_sub = (max_x - min_x)/2 - (Ax - min_x)
                    h_to_sub = (max_y - min_y)/2 - (Ay - min_y)
                    if list_coo[5] >= 180:  # si la rotation est superieur a 180 alors on inverse le sens du deplacement
                        w_to_sub *= -1
                        h_to_sub *= -1
                    Ax += w_to_sub
                    Bxp += w_to_sub
                    Cxp += w_to_sub
                    Dxp += w_to_sub
                    Ay += h_to_sub
                    Byp += h_to_sub
                    Cyp += h_to_sub
                    Dyp += h_to_sub
                    painter.drawLine(Ax, Ay, Bxp, Byp)
                    painter.drawLine(Bxp, Byp, Cxp, Cyp)
                    painter.drawLine(Cxp, Cyp, Dxp, Dyp)
                    painter.drawLine(Dxp, Dyp, Ax, Ay)
                else:  # donc si il n'y a pas de rotation
                    Ax -= list_coo[2]/2
                    Bx -= list_coo[2]/2
                    Cx -= list_coo[2]/2
                    Dx -= list_coo[2]/2
                    Ay -= list_coo[3]/2
                    By -= list_coo[3]/2
                    Cy -= list_coo[3]/2
                    Dy -= list_coo[3]/2
                    painter.drawLine(Ax, Ay, Bx, By)
                    painter.drawLine(Bx, By, Cx, Cy)
                    painter.drawLine(Cx, Cy, Dx, Dy)
                    painter.drawLine(Dx, Dy, Ax, Ay)

            elif list_coo[4] == "ROUNDED":
                painter.setPen(QPen(Qt.gray, 2))
                # painter.setBrush(QBrush(QtGui.QColor(list_coo[5], list_coo[6], list_coo[7]), Qt.SolidPattern))
                painter.drawEllipse(list_coo[0], list_coo[1], list_coo[2], list_coo[3])

    def draw_label(self, x, y, w, h):
        # creating label
        label = QLabel(self)

        # setting geometry of the label
        label.setGeometry(x, y, w, h)
        # setting background color to label when mouse hover over it
        sty = "QLabel{background-color : gray}QLabel:hover{background-color: blue}"
        label.setStyleSheet(sty)
        label.show()

    def draw_circle_label(self, x, y, w, h):
        # creating label
        label = QLabel(self)

        # setting geometry of the label
        label.setGeometry(x, y, w, h)
        # setting background color to label when mouse hover over it

        demiW = int(w/2)
        sty = "QLabel{background-color : gray; border-radius :"
        sty += "{}".format(demiW)
        sty += "px}"
        label.setStyleSheet(sty)

        label.show()

    def draw_target(self, x, y, nom):
        # creating label
        label1 = QLabel(self)

        # setting geometry of the label
        label1.setGeometry(x+7, y+7, 6, 6)
        # setting background color to label when mouse hover over it

        sty = "QLabel{background-color : rgba(0,0,0,1);border-radius : 3px}"
        label1.setStyleSheet(sty)

        label2 = QLabel(self)
        label2.setAlignment(QtCore.Qt.AlignCenter)
        label2.setGeometry(x-20, y-20, 60, 60)
        sty2 = "QLabel{background-color : rgba(255, 255, 255, 0) ;border-radius : 30px; color: rgba(0, 0, 0, 0);" \
               "font-size: 20px;}QLabel:hover{border: 2px solid red; color: red}"
        label2.setStyleSheet(sty2)

        str_id_lab = "{}".format(label2)

        self.label_list[0].append(label2)
        self.label_list[1].append(str_id_lab)
        self.label_list[2].append([x, y])

        str_id_lab = str_id_lab[-19:-1]

        self.list_component_with_id.append([str_id_lab, nom])

        clickable(label2).connect(partial(self.highlight_tab_line, str_id_lab, self.list_component_with_id))

        label1.show()
        label2.show()

    def draw_target_via_tab(self, x, y):

        if self.current_label is not None:
            if type(self.current_label) != list:
                self.current_label.hide()
            else:
                for the_current_label in self.current_label:
                    the_current_label.hide()

        label = QLabel(self)

        self.current_label = label

        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setGeometry(x - 20, y - 20, 60, 60)
        sty = "QLabel{background-color : rgba(255, 255, 255, 0) ;border-radius : 30px;" \
              "font-size: 20px; border: 2px solid red; color: red}"
        label.setStyleSheet(sty)

        label.show()

    def draw_multiple_target_via_tab(self, x, y):

        if self.current_label is not None and self.multiple_label == 0:
            if type(self.current_label) != list:
                self.current_label.hide()
            else:
                for the_current_label in self.current_label:
                    the_current_label.hide()

        label = QLabel(self)

        if type(self.current_label) == list:
            self.current_label.append(label)
        else:
            self.current_label = [self.current_label]
            self.current_label.append(label)

        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setGeometry(x - 20, y - 20, 60, 60)
        sty = "QLabel{background-color : rgba(255, 255, 255, 0) ;border-radius : 30px;" \
              "font-size: 20px; border: 2px solid red; color: red}"
        label.setStyleSheet(sty)

        label.show()

    def highlight_tab_line(self, str_id_lab, list_key_name_component):
        for element in list_key_name_component:
            if element[0] == str_id_lab:
                clicked_label = element[1]
        self.functions.onClickDraw(clicked_label)

    def circle_label_via_tab(self, clicked_line):
        list_str_footprint = []
        if type(clicked_line) != list:
            for label in self.list_component_with_id:
                if clicked_line == label[1]:
                    list_str_footprint = label[0]
        else:
            for label in self.list_component_with_id:
                for one_component in clicked_line:
                    if one_component == label[1]:
                        list_str_footprint.append(label[0])
        for index, element in enumerate(self.label_list[1]):
            if type(list_str_footprint) != list:
                if element.find(list_str_footprint) != -1:
                    coo_x = self.label_list[2][index][0]
                    coo_y = self.label_list[2][index][1]
                    self.draw_target_via_tab(coo_x, coo_y)
            else:
                for str_footprint in list_str_footprint:
                    if element.find(str_footprint) != -1:
                        coo_x = self.label_list[2][index][0]
                        coo_y = self.label_list[2][index][1]
                        self.draw_multiple_target_via_tab(coo_x, coo_y)
                        self.multiple_label = 1
        self.multiple_label = 0

    def clear_current_label(self):
        if type(self.current_label) == list:
            for the_current_label in self.current_label:
                the_current_label.hide()
        else:
            self.current_label.hide()


if __name__ == '__main__':
    App = QApplication(sys.argv)
    window = Window()
    sys.exit(App.exec())