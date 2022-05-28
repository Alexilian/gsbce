import csv
import random
import draw
from draw import *
from tab import *
import mysql.connector

mydb = mysql.connector.connect(host="localhost", user="root", password="", database="gsb_carte_electronique")

mycursor = mydb.cursor()


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.widthWin = 1024
        self.heightWin = 900

        self.InitWindow()

    # fonction d'initiation de la fenêtre
    def InitWindow(self):
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle("Gerber Viewer")
        self.setGeometry(0, 0, self.widthWin, self.heightWin)

    def get_list_chip(self, idCarte):
        # return sous la forme d'une liste de liste
        # [nomcomposant:DX; forme; largeur; hauteur; UNKNOWN; UNKNOWN; rotation; *UNKNOWN; *UNKNOWN; *UNKNOWN;]
        # UNKNOWN --> ne sais pas a quoi cela correspond
        # * --> n'est pas présent pour toutes les pièces
        req = """SELECT id, forme, largeur, hauteur, inconnu1, inconnu2, rotation, relief1, relief2, relief3 FROM apr WHERE id_CarteElectronique = %s"""
        mycursor.execute(req, tuple(idCarte))
        apr_list = []
        for the_row in mycursor:
            apr_temp_list = []
            for the_column in list(the_row):
                if type(the_column) == str:
                    if len(the_column) != 0:
                        apr_temp_list.append(the_column)
                else:
                    apr_temp_list.append(the_column)
            apr_list.append(apr_temp_list)
        return apr_list

    # return une liste du contenu des fichiers gerber
    def get_gerber_list(self, idCarte, gerber):

        req = """SELECT """+ gerber +""" FROM carteelectronique WHERE id = %s"""
        mycursor.execute(req, tuple(idCarte))
        strDelete = r"\r\n"
        gBefore = str(list(list(mycursor)[0])[0])[2:-1].split(strDelete)
        gList = []
        for element in gBefore:
            if element != "" and element is not None and element.find("%") == -1 and element.find(
                    "G04") == -1 and element.find("M00") == -1 and element.find("M02") == -1 and element.find(
                    "G01") == -1 and element.find("G75") == -1 and element.find("G71") == -1:
                gList.append(element[:-1].strip())
        return gList

    def get_list_per_chip(self, idCarte, gerber):
        # return une liste de liste où chaques sous liste est une instruction pour placer toutes les formes
        x = 1  # variable pour qu'un certain bloc de code ne s'execute qu'une seule fois
        index1 = None  # variable pour definir l'index du debut du code gerber a traduire
        ancient_list = self.get_gerber_list(idCarte, gerber)
        list_chip = self.get_list_chip(idCarte)
        list_component = []
        sub_list = []
        for count, element in enumerate(ancient_list):
            for name_component in list_chip:
                if element == name_component[0] and x == 1:  # verification si la ligne correspond au nom du composant
                    index1 = count
                    x = 0
                elif element == name_component[0]:
                    index2 = count  # variable pour definir l'index de fin du code gerber a traduire
                    for i in range(index1, index2):
                        sub_list.append(ancient_list[i])
                    list_component.append(sub_list[:])  # ne pas oublier les ":" sinon le clear() casse tout
                    sub_list.clear()
                    index1 = index2
            if element == 'G36':  # G36 est le debut du dessin libre (sans forme fixe)
                index1 = count
            elif element == 'G37':  # G37 est la fin du dessin libre
                index2 = count
                for i in range(index1, index2):
                    sub_list.append(ancient_list[i])
                list_component.append(sub_list[:])
                sub_list.clear()
                index1 = index2
        for i in range(index1, len(ancient_list)):
            sub_list.append(ancient_list[i])
        list_component.append(sub_list)
        return list_component

    def transform_coo(self, idCarte, gerber):
        # return la meme liste qu'avant mais avec les coordonnés rangees
        many_lists = self.get_list_per_chip(idCarte, gerber)
        new_list = many_lists
        for a_list in many_lists:
            index = many_lists.index(a_list)
            for the_command in a_list:
                sub_index = a_list.index(the_command)
                coo_list = []
                if the_command.find("J0") == -1:
                    if the_command[0] == "X":  # regarde si le premier terme est X
                        pos_y = the_command.find("Y")
                        if pos_y == -1:  # donc si on ne trouve pas de Y dans la ligne
                            coo_list.append(int(the_command[1:-3])/10000)  #10000 parceque on a un rapport de 10000
                            coo_list.append("Null")  # le null indique que c'est la meme coo que le point d'avant
                        else:
                            coo_list.append(int(the_command[1:pos_y])/10000)  # prend tout ce qu'il y a entre X et Y
                            coo_list.append(int(the_command[pos_y+1:-3])/10000)  # prend tout ce qu'il y a entre Y et D0
                        coo_list.append(the_command[-3:])  # rajout des D01/D02 etc pour savoir si l'on "leve le stylo"
                        many_lists[index][sub_index] = coo_list
                    elif the_command[0] == "Y":
                        pos_x = the_command.find("X")
                        if pos_x == -1:
                            coo_list.append("Null")
                            coo_list.append(int(the_command[1:-3])/10000)
                        else:
                            coo_list.append(int(the_command[1:pos_x])/10000)
                            coo_list.append(int(the_command[pos_x+1:-3])/10000)
                        coo_list.append(the_command[-3:])
                        many_lists[index][sub_index] = coo_list
                    else:
                        new_list[index][sub_index] = many_lists[index][sub_index]
        return new_list

    def all_info_form(self, idCarte, gerber):
        # complete les infos des formes a dessiner (la largeur et la hauteur)
        bigger_list = self.transform_coo(idCarte, gerber)
        list_component = self.get_list_chip(idCarte)
        width = 0
        height = 0
        for big_list in bigger_list:
            the_piece = big_list[0]
            for component in list_component:
                if component[0] == the_piece:
                    width = round(float(component[2]) /39.3701, 5)  # 3.9701 pour traduire de inch a mm
                    height = round(float(component[3]) / 39.3701, 5)  # et vu qu'il y a un rapport de 10 alors 39.3701
            if the_piece == "G36":  # n'est pas une piece, donc met 0 en largeur et 0 en hauteur
                width = 0
                height = 0
            big_list.insert(1, width)
            big_list.insert(2, height)
        return bigger_list

    ######################################################################################################

    def get_coo_component(self, idCarte):
        # return la liste avec le nom du composant avec ses coordonnées

        req = """SELECT Designator, MidX, MidY FROM placement WHERE id_CarteElectronique = %s"""

        mycursor.execute(req, tuple(idCarte))

        big_list = []

        for the_row in mycursor:
            the_row = list(the_row)
            the_row[1] = the_row[1][:-2]
            the_row[2] = the_row[2][:-2]
            the_row[1] = [the_row[1], the_row[2]]
            the_row.pop(2)
            big_list.append(the_row)

        return big_list

    def get_tab_component(self, idCarte):
        # return la liste avec le "Designator", "Manufacturer Part Number", et la "Quantity" du composant

        req = """SELECT composant.Designator, composant.Manufacturer_Part_Number, composant.Quantity FROM composant INNER JOIN placement ON placement.id_Composant = composant.id WHERE id_CarteElectronique = %s"""

        mycursor.execute(req, tuple(idCarte))

        big_list = [['Designator', 'Manufacturer_Part_Number', 'Quantity']]

        for the_row in mycursor:
            the_row = list(the_row)
            big_list.append(the_row)

        self.window2 = WindowTableau(big_list, self)  # appel de la fenetre Tab qui prend la liste en param
        return big_list

    ####################################################################################################################

    def get_rap_value(self, the_list, path_component):
        # return le rapport pour pouvoir changer l'echelle du PCB dans le draw_form() via les coo_max/min
        upper_x = None
        upper_y = None
        lower_x = None
        lower_y = None
        rap = []
        biggest_list = self.adapt_coo(the_list, path_component)
        for bigger_list in biggest_list:
            for big_list in bigger_list:
                for element in big_list:
                    if type(element) is list:
                        if type(element[0]) is int or type(element[0]) is float:  # recup les plus petites/grandes coo
                            if upper_x is None or element[0] > upper_x:
                                upper_x = element[0]
                            if lower_x is None or element[0] < lower_x:
                                lower_x = element[0]
                        if type(element[1]) is int or type(element[1]) is float:
                            if upper_y is None or element[1] > upper_y:
                                upper_y = element[1]
                            if lower_y is None or element[1] < lower_y:
                                lower_y = element[1]
        if upper_x > self.widthWin or upper_y > self.heightWin:  # verifie si la plus grande coo sort de l'ecran
            if upper_x/self.widthWin > upper_y/self.heightWin:
                rap.append(upper_x/self.widthWin)  # calcul le rapport qu'il faut utiliser pour que rien ne sorte
            else:
                rap.append(upper_y/self.heightWin)
        else:
            if self.widthWin/upper_x > self.heightWin/upper_y:
                rap.append(self.widthWin/upper_x)
            else:
                rap.append(self.heightWin/upper_y)
        rap.append(lower_x)
        rap.append(lower_y)
        return rap  # sous la forme [rapport, min_x, min_y]

    def adapt_coo(self, biggest_list, path_component):
        # return la meme liste qu'avant mais cette fois en ayant adapté les coordonnées pour etre en 0,0 en origine
        lower_x = None  # plus petite valeur X de la liste
        lower_y = None  # plus petite valeur y de la liste
        for bigger_list in biggest_list:
            for big_list in bigger_list:
                for element in big_list:
                    if type(element) is list:  # check si c'est une liste, donc la liste des coordonnées
                        if type(element[0]) is int:  # check si c'est bien le X ou le Y et non le D01 par exemple
                            if lower_x is None or element[0] < lower_x:
                                lower_x = element[0]
                        if type(element[1]) is int:
                            if lower_y is None or element[1] < lower_y:
                                lower_y = element[1]
        for bigger_list in biggest_list:
            for big_list in bigger_list:
                for element in big_list:
                    if type(element) is list:
                        if type(element[0]) is int:
                            element[0] -= lower_x  # soustrait lower_x a toutes les coo X pour que l'origine soit a 0
                        if type(element[1]) is int:
                            element[1] -= lower_y  # soustrait lower_y a toutes les coo Y pour que l'origine soit a 0
        return biggest_list

    ####################################################################################################################

    def draw_function(self, biggest_list, path_chip, path_component, idCarte, face):
        # dessine finalement les formes et les traits a visualiser
        big_list_coo = []

        self.window = draw.Window(big_list_coo, self)  # appel la fenetre Draw qui prend une liste en param
        self.window.widthWin = self.widthWin
        self.window.heightWin = self.heightWin
        self.window.setGeometry(339, 32, self.widthWin, self.heightWin*2)

        list_chip = self.get_list_chip(idCarte)
        rap = self.get_rap_value(biggest_list, path_chip)
        list_component = self.get_coo_component(idCarte)
        previous_coo_x = None
        previous_coo_y = None

        for bigger_list in biggest_list:
            for big_list in bigger_list:
                coo_x = 0
                coo_y = 0
                if big_list[1] == 0 and big_list[2] == 0:
                    width = 1
                    height = 1
                else:
                    width = big_list[1]*rap[0]
                    height = big_list[2]*rap[0]
                for element in big_list:
                    if type(element) is list:
                        if element[2] == 'D02':  # D02 siginifier qu'on leve le stylo apres avoir dessiné la forme
                            if element[0] != 'Null':
                                if face == 'f':  # regarde si c'est la face de devant
                                    coo_x = (element[0] - rap[1]/2) * rap[0] - width/2
                                else:  # donc c'est la face de derriere, il faut donc inverser l'axe des abcisses
                                    coo_x = self.widthWin - ((element[0] - rap[1] / 2) * rap[0]) - width / 2
                                previous_coo_x = coo_x
                            if element[1] != 'Null':
                                coo_y = self.heightWin - ((element[1] - rap[2]) * rap[0] + height/2)
                                previous_coo_y = coo_y
                            for the_chip in list_chip:
                                if big_list[0] == the_chip[0]:
                                    if the_chip[1] == "RECTANGULAR":  # check si la forme a dessiner est un rectangle
                                        big_list_coo.append([coo_x + width / 2, coo_y + height/2, width, height, the_chip[1], float(the_chip[6])])
                                    elif the_chip[1] == "ROUNDED":
                                        big_list_coo.append([coo_x, coo_y, width, height, the_chip[1], the_chip[6]])
                                    elif the_chip[1] == "RELIEF":
                                        print("Je ne sais toujours pas ce que c'est que RELIEF, c'est dans le .apr")
                        elif element[2] == 'D01':  # D01 signifie qu'on laisse le stylo baissé pour dessiner le prochain
                            if element[0] != 'Null':
                                if face == 'f':
                                    coo_x = (element[0] - rap[1]/2) * rap[0] - width/2
                                else:
                                    coo_x = self.widthWin - ((element[0] - rap[1] / 2) * rap[0] + width / 2)
                            if element[1] != 'Null':
                                coo_y = self.heightWin - ((element[1] - rap[2]) * rap[0] + height/2)
                            if 0 < previous_coo_x <= self.widthWin and 0 < previous_coo_y <= self.heightWin and 0 < coo_x <= self.widthWin and 0 < coo_y <= self.heightWin:
                                if big_list[0] == "G36":  # G36 veut dire que l'on commence le tracé "libre"
                                    big_list_coo.append([previous_coo_x, previous_coo_y, coo_x, coo_y, 1])
                                    previous_coo_x = coo_x
                                    previous_coo_y = coo_y
                                else:
                                    for the_chip in list_chip:
                                        if big_list[0] == the_chip[0]:
                                            big_list_coo.append([previous_coo_x, previous_coo_y, coo_x, coo_y, 2])
                                            previous_coo_x = coo_x
                                            previous_coo_y = coo_y

        for the_component in list_component:
            for the_component_spec in the_component:
                if type(the_component_spec) == list:
                    if face == "f":
                        x_component = (float(the_component_spec[0]) - rap[1] / 2) * rap[0] - 10
                    else:
                        x_component = self.widthWin - ((float(the_component_spec[0]) - rap[1] / 2) * rap[0] + 10)
                    y_component = self.heightWin - ((float(the_component_spec[1]) - rap[2]) * rap[0] + 10)

                    self.window.draw_target(x_component, y_component, the_component[0])  # dessine le composant (noir)

        self.window.update()  # actulise la fenetre puisque la liste a changé

    ####################################################################################################################

    def onClickTab(self, clicked_line):  # fonction de jonction de Tab a Draw
        self.window.circle_label_via_tab(clicked_line)

    def onClickDraw(self, clicked_label):  # fonction de jonction de Draw a Tab
        self.window2.highlight_via_draw(clicked_label)
