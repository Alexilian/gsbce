import sys
import csv
import mysql.connector
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from functions import *


class UserWindow(QWidget):

    def __init__(self, parent=None):
        super(UserWindow, self).__init__(parent)

        self.title = 'Gerber Viewer'
        self.left = 500
        self.top = 200
        self.width = 512
        self.height = 512

        self.button1 = QPushButton('Créer', self)
        self.button2 = QPushButton('Visualiser', self)
        self.button3 = QPushButton('Réinserer', self)
        self.button4 = QPushButton('Retour au menu', self)
        self.button5 = QPushButton('Valider', self)

        self.label = QLabel(self)

        layout = QHBoxLayout()
        self.dropDown = QComboBox()
        self.dropDownFace = QComboBox()

        layout.addWidget(self.dropDown)
        layout.addWidget(self.dropDownFace)
        self.setLayout(layout)
        self.setWindowTitle("combo box demo")

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.label.setGeometry(0, 64, 512, 48)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setText("Choisissez une option")

        self.button1.setGeometry(64, 384, 128, 64)
        self.button1.clicked.connect(self.createCarte)
        self.button2.setGeometry(320, 384, 128, 64)
        self.button2.clicked.connect(self.selectCarte)
        self.button3.setGeometry(64, 384, 128, 64)
        self.button3.clicked.connect(self.createCarte)
        self.button4.setGeometry(320, 384, 128, 64)
        self.button4.clicked.connect(self.backMenu)
        self.button5.setGeometry(64, 384, 128, 64)
        self.button5.clicked.connect(self.onClickDropBox)

        self.button3.hide()
        self.button4.hide()
        self.button5.hide()

        self.dropDownFace.addItems(['f - Front', 'b - Bottom'])

        self.dropDown.hide()
        self.dropDownFace.hide()

    # selectionne les fichiers pour pouvoir les inserer dans la base de données
    def createCarte(self):

        name, done1 = QInputDialog.getText(self, 'Saisie de texte', 'Entrez votre nom de projet:')
        gbo, done2 = QFileDialog.getOpenFileName(self, 'Sélection de fichier', 'Insertion GBO:')
        gto, done3 = QFileDialog.getOpenFileName(self, 'Sélection de fichier', 'Insertion GTO:')
        gbs, done4 = QFileDialog.getOpenFileName(self, 'Sélection de fichier', 'Insertion GBS:')
        gts, done5 = QFileDialog.getOpenFileName(self, 'Sélection de fichier', 'Insertion GTS:')
        csvApr, done6 = QFileDialog.getOpenFileName(self, 'Sélection de fichier', 'Insertion csvApr:')
        csvComposant, done7 = QFileDialog.getOpenFileName(self, 'Sélection de fichier', 'Insertion csvComposant:')
        csvPlacement, done8 = QFileDialog.getOpenFileName(self, 'Sélection de fichier', 'Insertion csvPlacement:')

        if done1 and done2 and done3 and done4 and done5 and done6 and done7 and done8:
            self.insertBLOBCSV(csvApr, csvComposant, csvPlacement, name, gbo, gto, gbs, gts)
        else:
            self.label.setText("Vous avez oublié un fichier !")

        # Hide the pushbutton after inputs provided by the use.
        self.button1.hide()
        self.button2.hide()
        self.button3.show()
        self.button4.show()

    # insert les fichiers selectionnés dans la base de données
    def insertBLOBCSV(self, apr, composant, placement, nom, GBO, GTO, GBS, GTS):
        try:

            sql_insert_blob_query = """INSERT INTO carteelectronique (nom, GBO, GTO, GBS, GTS) VALUES (%s,%s,%s,%s,%s)"""
            GBO = self.convertToBinaryData(GBO)
            GTO = self.convertToBinaryData(GTO)
            GBS = self.convertToBinaryData(GBS)
            GTS = self.convertToBinaryData(GTS)

            # Convert data into tuple format
            insert_blob_tuple = (nom, GBO, GTO, GBS, GTS)
            myCursor.execute(sql_insert_blob_query, insert_blob_tuple)

            apr = csv.reader(open(apr))
            composant = csv.reader(open(composant))
            placement = csv.reader(open(placement))

            for rowApr in apr:
                theList = rowApr[0].split(";")
                req = "INSERT INTO apr (id_CarteElectronique, id, forme, largeur, hauteur, inconnu1, inconnu2, rotation"
                if(11 == len(theList)):
                    req += ", relief1, relief2, relief3"
                req += ") VALUES ("
                for i in theList:
                    req += "%s, "
                req = req[:-2]
                req += ")"
                theList = tuple(theList)

                myCursor.execute(req, theList)

            for rowComp in composant:

                theList = rowComp[0].split(";")
                req = "INSERT INTO composant (id, comment, "
                if(theList[2] is not None and theList[2] != ""):
                    req += "Description, "
                req += "Designator, Footprint, LibRef, Manufacturer_Name, Manufacturer_Part_Number, Quantity"
                if(theList[-1] is not None and theList[-1] != ""):
                    req += ", value"
                req += ") VALUES ("
                theList = list(filter(None, theList))
                for i in theList:
                    req += "%s, "
                req = req[:-2]
                req += ")"
                theList = tuple(theList)

                myCursor.execute(req, theList)

            for rowPlace in placement:
                print("RowPlace Commencé")
                theList = rowPlace[0].split(";")
                req = "INSERT INTO placement (id_CarteElectronique, id, Designator, Footprint, MidX, MidY, RefX, RefY, PadX, PadY, Layer, Rotation, id_Composant) VALUES ("
                for i in theList:
                    req += "%s, "
                req = req[:-2]
                req += ")"
                print(theList)
                print(req)
                theList = tuple(theList)

                myCursor.execute(req, theList)

            connection.commit()
            self.label.setText("Tout les fichiers ont bien été sélectionnés et inséré")

        except mysql.connector.Error as error:
            self.label.setText("Failed inserting CSV data into MySQL table {}".format(error))
            print("Failed inserting CSV data into MySQL table {}".format(error))

    # convertie les fichiers en binary
    def convertToBinaryData(self, filename):
        # Convert digital data to binary format
        with open(filename, 'rb') as file:
            binaryData = file.read()
        return binaryData

    # retourne au menu principal
    def backMenu(self):
        self.button1.show()
        self.button2.show()
        self.button3.hide()
        self.button4.hide()
        self.button5.hide()
        self.dropDown.hide()
        self.dropDownFace.hide()
        self.dropDown.clear()
        self.label.setText("Veuillez choisir une option")

    # selectionne une carte a visualiser
    def selectCarte(self):

        self.dropDown.show()
        self.dropDownFace.show()
        self.label.setText("Choisissez une carte à visualiser")
        self.button1.hide()

        self.button5.show()
        self.button4.show()

        try:
            sql_select_card_query = "SELECT id, nom FROM carteelectronique"

            myCursor.execute(sql_select_card_query)

            for theRow in myCursor:
                self.dropDown.addItem(str(theRow[0]) + " - " + theRow[1])

        except mysql.connector.Error as error:
            print("Failed to load data from MySQL table {}".format(error))

    # lance l'application de visualisation sur la pression du bouton valider
    def onClickDropBox(self):
        self.launcher(self.dropDown.currentText()[0], self.dropDownFace.currentText()[0])

    # definition des parametres de l'application de visualisation
    def launcher(self, idCarte, faceLetter):
        biggest_list = []
        face = faceLetter
        if face == "f":
            strGS = "GTS"
            strGO = "GTO"
        else:
            strGS = "GBS"
            strGO = "GBO"
        biggest_list.append(window_pcb.all_info_form(idCarte, strGS))
        biggest_list.append(window_pcb.all_info_form(idCarte, strGO))
        path_chip = window_pcb.get_list_chip(idCarte)
        path_component = window_pcb.get_coo_component(idCarte)
        window_pcb.get_tab_component(idCarte)
        window_pcb.draw_function(biggest_list, path_chip, path_component, idCarte, face)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window_pcb = MainWindow()

    screen = app.primaryScreen()
    size = screen.size()
    window_pcb.widthWin = size.width()-339
    window_pcb.heightWin = size.height()-300

    ex = UserWindow()
    connection = mysql.connector.connect(host="localhost", user="root", password="", database="gsb_carte_electronique")
    myCursor = connection.cursor()
    ex.show()
    sys.exit(app.exec_())