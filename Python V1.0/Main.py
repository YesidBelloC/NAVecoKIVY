# https://urlz.fr/
# https://materialdesignicons.com/
# https://kivymd.readthedocs.io/en/latest/index.html
# https://www.color-hex.com/color/7a51d0
# https://imagecolorpicker.com/

# https://towardsdatascience.com/3-ways-to-convert-python-app-into-apk-77f4c9cd55af

import kivy
from kivy.core.window import Window
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics.context_instructions import Color
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics.vertex_instructions import Line
from kivy.properties import ObjectProperty
from kivy.properties import DictProperty
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.garden.mapview import MapView, MapMarker, MapMarkerPopup
from kivy.metrics import dp
from kivy.uix.dropdown  import DropDown
from kivy.clock import Clock
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.clock import mainthread
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.pickers import MDTimePicker
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import (
    MDFlatButton,
    MDRectangleFlatButton,
    MDRaisedButton,
    MDFillRoundFlatButton,
    MDRectangleFlatIconButton,
    MDFillRoundFlatIconButton,
    MDIconButton,
    MDFloatingActionButton
)
from kivymd.app import MDApp
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import Snackbar

# External Libraries
import googlemaps
import openrouteservice as ors
import statistics
import polyline
import numpy as np
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['text.color'] = 'w'
matplotlib.rcParams['axes.edgecolor'] = 'w'

# Internal Libraries
import time
import sqlite3
import random as rdm
from math import *
from pprint import pprint
import threading

# kivy.require('1.9.0')

Window.size = (400,700)

#3ca62b green
#c23328 red
#121212 background
#4d367e selection
#673bb7 EXPLEO

# TODO:
# Correct MaxSpeed ORS ya, GM falta
# Add paramaeter to parameter page: Order Filter Elev, Coef Selection, Coeff Mutation, Citaire d'arret
# Auto zoom calculado
# Resfresh energy estimation
# Add code control MPC
# Show more than one route

# Add GPS Data (position actuelle)
# Send mail
# Synchronize param and debug with NAVeco Code

# Cierre automatico de floataction button

############################################################ GEOimport
#API key for Gooogle Maps
GM_key = 'AIzaSyDrB16uv9NYnnT4WH4V0zcJmqvHGkxL9mE'
clientGM = googlemaps.Client(key=GM_key)
MapClientGM = clientGM
# dir(MapClient)
DevelopperMode = True

clientORS = ors.Client(key='5b3ce3597851110001cf62487778ecd1fca04f93a0099fa0b1a13240')

def getDistance(lat1,lon1,lat2,lon2):
    R = 6371000
    phi1 = lat1*pi/180
    phi2 = lat2*pi/180
    dlat = (lat2-lat1)*pi/180
    dlon = (lon2-lon1)*pi/180

    a = sin(dlat/2)*sin(dlat/2)+cos(phi1)*cos(phi2)*sin(dlon/2)*sin(dlon/2)
    c = 2*atan2(sqrt(a), sqrt(1-a))

    return R * c

############################################################ HEX-RGB

def hex_to_rgb(hex):
  rgb = []
  for i in (0, 2, 4):
    decimal = int(hex[i:i+2], 16)
    rgb.append(decimal)

  return tuple(rgb)

############################################################ AG Fonctions

"""  Entrée : Tableau 2 dimensions : [ Distance (m), Vmax (m/s) ] ( Sortie de la segmentation.csv)
     Sortie : retourne 3 vecteurs:
        * un pour les points où on coupe, ie: où la vitesse change
        * un 2eme vecteur de toutes les vitesses sur notre trajet
        * un 3eme pour les distances des differents segments où V est constant ==> il aura donc la meme
            taille que le vecteur précédent
"""

def speed_and_dist_cut(_dist_and_speed):

    _speeds = []
    dist_segment_speed = []
    cut_points = []

    # premiere vitesse max
    V = _dist_and_speed[0][1]
    _speeds.append(V)

    for i in range(1, len(_dist_and_speed)):
            if(_dist_and_speed[i][1] != V):
                cut_points.append(i)
                V = _dist_and_speed[i][1]
                _speeds.append(V)
                # ajouter la distance du segment (la où v = cst)
                if(len(dist_segment_speed) > 0):
                    dist_segment_speed.append(_dist_and_speed[i-1][0] - _dist_and_speed[cut_points[-2]-1][0] )
                else:
                    dist_segment_speed.append(_dist_and_speed[i-1][0])

    #ajouter la distance du dernier segment s'il y'a plus de 2 limitations de vitesse
    if len(_speeds) > 1:
        dist_segment_speed.append(_dist_and_speed[len(_dist_and_speed)-1][0] - _dist_and_speed[cut_points[-1]-1][0] )

    # s'il y aune seule vitesse limite la distance du segment == la distance totale
    else: # cad : len(dist_segment_speed) == 0 :
        dist_segment_speed.append(_dist_and_speed[-1][0])


    return cut_points, _speeds, dist_segment_speed


#---------------------------------------------------------------------------------------------------

"""
    Entrée :  [Amin (m), Amax (m/s), [Vmax]]
    Sortie :  2 tableaux:
    *un vecteur pour les accelerations possibles, avec le 'pas' qu'on a choisi et les
        limites 'a_min' et 'a_max
    * une matrice qui contient la vitesse min et vitesse max pour tout le trajet [ [Vmin_1, Vmax_1],
                                                                                   [Vmin_2, Vmax_2],
                                                                                   ...] en (m/s)
"""
def split_speed_and_acceleration(_Acceleration_min, _Acceleration_max, _speeds):

    vectors_speeds = []

    subdivision_acceleration = 50
    step_acceleration = (_Acceleration_max - _Acceleration_min)/subdivision_acceleration

    vector_acceleration = [ i*step_acceleration for i in range(-round(subdivision_acceleration/2) , round(subdivision_acceleration/2) +1 ) ]

    for i in range(0, len(_speeds)):
        #===============================================================================
        # initialisation des vitesses min a avoir en fonction des limitations de vitesse
        if _speeds[i] <= 8.33 and _speeds[i] >= 7: # >= 5.55: # 30 kmh --> Vmin = 20 kmh
            tmp = [5.55]
        elif _speeds[i] <= 13.88 and _speeds[i] >= 10: # >= 8.33 # 50 kmh --> Vmin = 30 kmh
            tmp = [8.33]
        elif _speeds[i] <= 25 and _speeds[i] >= 15: # >= 13.88  # 90 kmh --> Vmin = 50 kmh
            tmp = [13.88]
        elif _speeds[i] > 25 :   # 110 ou 130 kmh --> Vmin = 80 kmh
            tmp = [22.22]
        else:
            tmp = [ _speeds[i]/4 ] # si une limitation de vitesse est "trop petite" (on met Vmin = Vmax/4 kmh)
        if( _speeds[i] not in tmp ):
            tmp.append( _speeds[i] )
        #i += 1
        vectors_speeds.append( tmp )



    return vector_acceleration, vectors_speeds

#=======================================================================================

"""
    Entrée :  [[Amin (m), Amax (m/s)], [Vmin, Vmax]]
    Sortie :  [chromosome]
* Cette méthode de génération, génére des valeurs de gauche à droite du chromosome, en commancant par a_1 ensuite V_1, a_2, V_2, ...
* C'est la méthode utilisée'
"""
def generate_chromosome(vector_acceleration, vectors_speeds):

    acceptable = True
    chromosome_table = []

    vector_acceleration_positive = [i for i in vector_acceleration if i > 0] # pour a_0
    vector_acceleration_negative = [j for j in vector_acceleration if j < 0] # pour a_final

    # ajouter la premiere acceleration (positive) et non NULLE
    acceleration_random = round(rdm.random()*max(vector_acceleration_positive)  ,2)
    while acceleration_random == 0:
        acceleration_random = round(rdm.random()*max(vector_acceleration_positive)  ,2)

    chromosome_table.append( acceleration_random ) # acceleration de depart
    i = 0
    while( i < len(vectors_speeds)-1  ):
        if(i == 0):
              speed_random = rdm.random()*(vectors_speeds[i][-1] - vectors_speeds[i][0]) + vectors_speeds[i][0]
              chromosome_table.append( speed_random )

              acceleration_random = rdm.random()*vector_acceleration[-1]*rdm.choice([-1,1])
              chromosome_table.append( acceleration_random )
              i = i + 1
        else:

            if(acceleration_random < 0):

                # si on deccelere alors il faudra que la prochaine vitesse minimale 'vectors_speeds[i][0]'
                # soit strictement inferieure a la vitesse actuelle, cad 'speed_random'
                if speed_random <= vectors_speeds[i][0]:
                    acceptable = False
                    break

                spd_random = rdm.random()*( min( vectors_speeds[i][-1], speed_random) - vectors_speeds[i][0] ) + vectors_speeds[i][0]
                # il faut qu'elle soit STRICTEMENT inferieure a la vitesse precedente car a < 0
                while spd_random == speed_random:
                    spd_random = rdm.random()*( min( vectors_speeds[i][-1], speed_random) - vectors_speeds[i][0] ) + vectors_speeds[i][0]
                    # print(str(spd_random) + " =======  "+str(speed_random) )
                speed_random = spd_random
                chromosome_table.append( speed_random )

            elif(acceleration_random > 0):
                if vectors_speeds[i][-1] <= speed_random :
                    acceptable = False
                    break;

                spd_random = rdm.random()*(vectors_speeds[i][-1] - vectors_speeds[i][0]) + vectors_speeds[i][0]
                # il faut qu'elle soit STRICTEMENT superieure a la vitesse precedente car a < 0
                while spd_random == speed_random:
                    spd_random = rdm.random()*(vectors_speeds[i][-1] - vectors_speeds[i][0]) + vectors_speeds[i][0]
                speed_random = spd_random
                chromosome_table.append( speed_random )

            else :
                # si a == 0 alors on garde la meme vitesse. deja stockée dans la derniere valeur 'speed_random'
                # et verifier que si on garde la meme vts qu'avant, qu'elle soit
                # tjrs inferieure a la limitte max de la vts d'apres et superieure a
                # la vitesse min d'apres
                if( (speed_random <= vectors_speeds[i][-1]) and (speed_random >= vectors_speeds[i][0]) ):
                    chromosome_table.append( speed_random )
                else:#
                    acceptable = False #
                    break #


            acceleration_random = round(rdm.random()*vector_acceleration[-1],2)*rdm.choice([-1,1])
            #acceleration_random = rdm.choice( vector_acceleration )
            chromosome_table.append( acceleration_random )
            i = i + 1

#=======================================================================================

    # car s'il y a une seule limitation de vitesse alors ca rentre meme pas dans la boucle d'au dessus,
    # donc aacelerarion_random et ... ne sont pas définies
    if len(vectors_speeds) > 1 :

        # ajoutée pour le soucis de a == 0 en dernier
        if(acceleration_random < 0):

            # verifier que la vitesse min d'apres soit inferieure strictement, sinon ce n'est pas possible de
            # deccelerer vers une vitesse plus grande que soi, ou égale
            if speed_random <= vectors_speeds[i][0]:
                acceptable = False

            else:
                spd_random = rdm.random()*( min( vectors_speeds[i][-1], speed_random) - vectors_speeds[i][0] ) + vectors_speeds[i][0]
                # il faut qu'elle soit STRICTEMENT inferieure a la vitesse precedente car a < 0
                while spd_random == speed_random:
                    spd_random = rdm.random()*( min( vectors_speeds[i][-1], speed_random) - vectors_speeds[i][0] ) + vectors_speeds[i][0]

                speed_random = spd_random
                chromosome_table.append( speed_random )

        elif(acceleration_random > 0):

            if vectors_speeds[i][-1] <= speed_random :
                acceptable = False

            else:
                spd_random = rdm.random()*(vectors_speeds[i][-1] - vectors_speeds[i][0]) + vectors_speeds[i][0]
                # il faut qu'elle soit STRICTEMENT superieure a la vitesse precedente car a < 0
                while spd_random == speed_random:
                    spd_random = rdm.random()*(vectors_speeds[i][-1] - vectors_speeds[i][0]) + vectors_speeds[i][0]

                speed_random = spd_random
                chromosome_table.append( speed_random )
           #=======================================================================================
        else: # a == 0    #
            # on verifie qu'on depasse pas la limite en gardant la mm vts
            if( (speed_random <= vectors_speeds[i][-1]) and (speed_random >= vectors_speeds[i][0]) ):
                # ajouter l'avant derniere vitesse
                chromosome_table.append( speed_random )
            else:#
                acceptable = False #

    # sinon, il a une seule limitation de vitesse ==> on ajoute juste le random vitesse, car la premiere
    # acceleration y est deja (au debut)
    else:

        speed_random = rdm.random()*(vectors_speeds[i][-1] - vectors_speeds[i][0]) + vectors_speeds[i][0]
        chromosome_table.append( speed_random )

    acceleration_random = rdm.random()*min(vector_acceleration_negative)
    while acceleration_random == 0:
        acceleration_random = rdm.random()*min(vector_acceleration_negative)

    #ajouter la derniere decceleration et la derniere vitesse v=0
    chromosome_table.append( acceleration_random ) # decceleration finale (vers V=0)
    chromosome_table.append( 0 ) # vitesse finale = 0
    i = i + 1
    # print("je suis laaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"+str(acceptable))
    return acceptable, chromosome_table


#---------------------------------------------------------------------------------------------------

"""
    Entrée :  [[Chromosome], [Dist de seg], [point], [Vmax]]
    Sortie :  [Durée (s)]
Comme son nom l'indique, cette fonction calcule les différentes durrées en [s] pour
les différentes phases du chromosome donné en entrée'
"""
def calculate_durations( chromosome, dist_segment_speed , cut_points, speeds):

    # Pour avoir les données pour chaque phases, independemment des depassements
    duration_brute_per_phase = []
    distance_raw_per_phase = []

    # Les distances et les durées des phases en detail (en separant les depassements )
    distance_per_phase = []
    duration_per_phase = []

    dur_seg_tmp = []

    # Calculer les differentes durées brutes des diff phases (en cumulant des les durées mm s'il y a depassement)
    duration_raw_per_phase = []

    duration_segment = []
    i = 0
    j = 0  # and j<len(dist_segment_speed) dans le while ne sert a rien si tt va bien
    while(i < len(chromosome) ):

        if(i == 0):
            duration_1 = chromosome[i+1]/chromosome[i]
            distance_1 = duration_1*chromosome[i+1]/2

            if(chromosome[i+2] == 0):

                duration_2 = 0
                distance_2 = duration_2*chromosome[i+1] + duration_2*(chromosome[i+3] - chromosome[i+1])/2

                #sign_acceleration = abs(chromosome[i+2]) / chromosome[i+2]
                dist_tmp = distance_1 + distance_2
                distance_3 = dist_segment_speed[j] - dist_tmp

                duration_3 = distance_3/chromosome[i+1]

            elif(chromosome[i+2] > 0 and chromosome[i+3] > speeds[j] ):

                 duration_2 = (speeds[j] - chromosome[i+1] )/chromosome[i+2]
                 distance_2 = duration_2*chromosome[i+1] + duration_2*(speeds[j] - chromosome[i+1])/2

                 dist_tmp =  distance_1 + distance_2
                 distance_3 = dist_segment_speed[j] - dist_tmp

                 duration_3 = distance_3/chromosome[i+1]

            else:
                duration_2 = ( chromosome[i+3] - chromosome[i+1] )/chromosome[i+2]
                distance_2 = duration_2*chromosome[i+1] + duration_2*(chromosome[i+3] - chromosome[i+1])/2

                #sign_acceleration = abs(chromosome[i+2]) / chromosome[i+2]
                dist_tmp = distance_1 + distance_2
                distance_3 = dist_segment_speed[j] - dist_tmp

                duration_3 = ( dist_segment_speed[j] - dist_tmp )/chromosome[i+1]

            duration_raw_per_phase.append( duration_1 )
            duration_raw_per_phase.append( duration_3 )
            duration_raw_per_phase.append( duration_2 )

            # mettre a jour la duree de tout le segement
            duration_segment.append(duration_1 + duration_2 + duration_3)
            duration_per_phase.append([duration_1 , duration_3 , duration_2])
            distance_per_phase.append([distance_1 , distance_3 , distance_2])


            # pour avoir les distances 'brutes' par phases
            distance_raw_per_phase.append(distance_1)
            distance_raw_per_phase.append(distance_3)
            distance_raw_per_phase.append(distance_2)

            i = i + 3
            j = j + 1

        else: # i >= 1
            if(chromosome[i] == 0 ):
                # print(str(i) + " Fin")
                break

            if( chromosome[i] > speeds[j-1] ):
                 duration_1 = ( chromosome[i] - speeds[j-1] )/chromosome[i-1]
                 distance_1 = duration_1*speeds[j-1]  +  duration_1*(chromosome[i]-speeds[j-1] )/2

                 if(chromosome[i+1] == 0):
                     duration_2 = 0

                     dist_tmp =  distance_1
                     #dist_tmp = duration_2*chromosome[i] + duration_2*(chromosome[i+2] - chromosome[i])/2
                     distance_3 = dist_segment_speed[j] - dist_tmp

                     duration_3 = distance_3/chromosome[i]

                 elif(chromosome[i+1] > 0 and chromosome[i+2] > speeds[j] ):
                     duration_2 = ( speeds[j] - chromosome[i] ) / chromosome[i+1]
                     distance_2 = duration_2*chromosome[i] + duration_2*(speeds[j] - chromosome[i])/2

                     dist_tmp = distance_1 + distance_2
                     distance_3 = dist_segment_speed[j] - dist_tmp

                     duration_3 = distance_3/ chromosome[i]

                 else:
                     duration_2 = ( chromosome[i+2] - chromosome[i] )/chromosome[i+1]
                     distance_2 = duration_2*chromosome[i] + duration_2*(chromosome[i+2] - chromosome[i])/2

                     dist_tmp = distance_1  + distance_2
                     distance_3 = dist_segment_speed[j] - dist_tmp

                     duration_3 = distance_3/chromosome[i]

                 duration_per_phase.append([duration_1 , duration_3,  duration_2])
                 # si on a une acceleration au debut du segment a prendre en
                 # compte ==> on rajoute sa duree a la duree de derniere acceleration du segment precedent
                 duration_raw_per_phase[-1] = duration_raw_per_phase[-1] + duration_1

                 duration_raw_per_phase.append( duration_3 )
                 duration_raw_per_phase.append( duration_2 )

                 # mettre a jour la duree de tout le segement
                 duration_segment.append(duration_1 + duration_2 + duration_3)
                 distance_per_phase.append([distance_1 , distance_3 , distance_2])

                 #=======================================================================================
                 # pour avoir les distances 'brutes' par phases
                 distance_raw_per_phase[-1] = distance_raw_per_phase[-1] + distance_1
                 distance_raw_per_phase.append(distance_3)
                 distance_raw_per_phase.append(distance_2)
                 #=======================================================================================

                 j = j + 1
                 i = i + 2

             #=======================================================================================
            else:
                duration_1 = 0  # y'avait pas de depassement avant
                distance_1 = 0
                if(chromosome[i+1] == 0):
                    duration_2 = 0
                    distance_2 = 0

                    dist_tmp = distance_2
                    distance_3 = dist_segment_speed[j] - dist_tmp

                    duration_3 = distance_3/chromosome[i]

                elif(chromosome[i+1] > 0 and chromosome[i+2] > speeds[j] ):
                    duration_2 = ( speeds[j] - chromosome[i] ) / chromosome[i+1]
                    distance_2 = duration_2*chromosome[i] + duration_2*(speeds[j] - chromosome[i])/2

                    dist_tmp = distance_2
                    distance_3 = dist_segment_speed[j] - dist_tmp

                    duration_3 = distance_3/ chromosome[i]

                else:
                    duration_2 = ( chromosome[i+2] - chromosome[i] )/chromosome[i+1]
                    distance_2 = duration_2*chromosome[i] + duration_2*(chromosome[i+2] - chromosome[i])/2

                    dist_tmp = distance_2
                    distance_3 = dist_segment_speed[j] - dist_tmp

                    duration_3 = distance_3/ chromosome[i]

                duration_raw_per_phase.append( duration_3 )
                duration_raw_per_phase.append( duration_2 )

                duration_per_phase.append([duration_1 , duration_3,  duration_2])

                # mettre a jour la duree de tout le segement
                duration_segment.append(duration_2 + duration_3)
                distance_per_phase.append([distance_1 , distance_3 , distance_2])

                #########################################################
                # pour avoir les distances 'brutes' par phases
                # distance_1 == 0
                distance_raw_per_phase.append(distance_3)
                distance_raw_per_phase.append(distance_2)
                #########################################################

                j = j + 1
                i = i + 2
             ####################################################

    return duration_raw_per_phase, duration_per_phase, distance_per_phase, distance_raw_per_phase


#-----------------------------------------------------------------------------------------------------


"""
    Entrée :  [[Chromosome], [Durée (s)], [Dist de seg], [point], [Vmax]]
    Sortie :  [Distance par m], [Durée par m], [Energie par m], [Vitt par m]
    Cette fonction calcule l'énergie consommée pour le chromosome donné en entrée,
    ainsi que le temps de trajet du même chromosome,  et les vitesses chaque 1 mètre
"""

def evaluate(chromosome ,duration_raw_per_phase, distance_raw_per_phase , _dist_and_slope):

    """ 0) les données du véhicule """
    m = 1100 # masse du véhicule
    C_r = 0.01 # Coeff
    g = 9.81 # gravitée
    Rw = 1.25 #
    SC_x =0.609 # surface

    Motorization = 'Elect'
    #Motorization = 'Therm'

    if Motorization == 'Therm':
        Rdm_positive = 1/0.5
        Rdm_negative = 0
    else :
        Rdm_positive = 1/0.8
        Rdm_negative = 0.2

    #---------------------------------------------------------------------------------

    """ 2) transformer la matrice des distances de chaque phase de chaque segement (en brute) en une liste
        de distances cumulées (a la fin on aura la distance totale)
        par exp: [1,3,2] ==> [1,4,6]  ( '1' la durée qu'on met pour la premiere phase, ...)"""


    cumulative_raw_distance = []
    distance_init = 0

    for i in range( 0, len(distance_raw_per_phase) ) :

            cumulative_raw_distance.append(distance_raw_per_phase[i] + distance_init)
            distance_init = distance_init + distance_raw_per_phase[i]

    #---------------------------------------------------------------------------------
#---------------------------------------------------------------------------------

    """ 3) parcourir la matrice de ditance_pente pour calculer la puissance """

    #Energie_consommée = 0
    #Ec_list = []

    i = 0 # pour parcourir le chromosome (les différentes phases)
    j = 1 # pour parcourir la liste dist_slope (pour récuperer les pentes chaque 1 m )
    k = 0 # pour les itérations des temps

    times_metre = [0]
    vts_metre = [0]
    energy_consumed_metre = [0]
    tps = []
    F_trac = 0

    while(i < len(chromosome) - 1  ): # -1 car on prend pas en compte le dernier V = 0 (ca ne consomme pas en +)

        if(i == 0): # car V_0 = 0

            while( j < len(_dist_and_slope)   and j  <= round(cumulative_raw_distance[i])   ):
                # temps pour chaque metre (au point j)
                times_metre.append( sqrt( j*2/chromosome[i] ) )
                #vts_metre.append( chromosome[i]*( times_metre[-1]-times_metre[-2] ) )
                vts_metre.append( chromosome[i]*( times_metre[-1] ) )

                #=====================================================================================================
                # calcul de F_trac = ma - Fa - Fr - Fw
                F_trac =   (m*chromosome[i]
                            + m*g*cos( _dist_and_slope[j][1] )*C_r
                            + m*g*sin( _dist_and_slope[j][1] )
                            + 0.5*Rw*SC_x
                            *( 0 + chromosome[i]*times_metre[-1])**2  )
                #=====================================================================================================

                # Calucul de puissance en ce point j ( En = dt*V(t)*F*Randement )
                # quand i == 0 accel > 0 et donc ya un randement positif
                if F_trac >= 0 :
                    energy_consumed_metre.append(  ( times_metre[-1]-times_metre[-2] )*( 0 + chromosome[i]*times_metre[-1] )*( m*chromosome[i] + m*g*cos( _dist_and_slope[j][1] )*C_r + m*g*sin( _dist_and_slope[j][1] ) + 0.5*Rw*SC_x *( 0 + chromosome[i]*times_metre[-1])**2 )*Rdm_positive)

                    if energy_consumed_metre[-1] < 0 :
                        print(" Error !")

                else:
                    #energy_consumed_metre.append(0)
                    energy_consumed_metre.append(  ( times_metre[-1]-times_metre[-2] )*( 0 + chromosome[i]*times_metre[-1] )*( m*chromosome[i] + m*g*cos( _dist_and_slope[j][1] )*C_r + m*g*sin( _dist_and_slope[j][1] ) + 0.5*Rw*SC_x *( 0 + chromosome[i]*times_metre[-1])**2 )*Rdm_negative)

                j += 1

            i += 1
            tps.append(times_metre[-1])

        else:

            if(i%2 == 1): # a == 0 (Vitesse constante) et V_0 = chromosome[i] "c'est lui mm"

                while( j < len(_dist_and_slope) and j <= round(cumulative_raw_distance[i])   ):

                    # temps pour chaque metre (au point j)
                    times_metre.append( (1/chromosome[i]) + times_metre[-1]  )
                    vts_metre.append( chromosome[i]  )

                    #=====================================================================================================
                    # calcul de F_trac = ma - Fa - Fr - Fw
                    F_trac = (  m*g*cos( _dist_and_slope[j][1] )*C_r
                    + m*g*sin( _dist_and_slope[j][1] )
                    + 0.5*Rw*SC_x * (chromosome[i]**2) )
                    #=====================================================================================================

                    # Calucul de puissance en ce point j ( En = dt*V(t)*F*Randement )
                    # quand  pente > 0 ==> ya un randement positif
                    # quand  pente <= 0 ==> ya pas de rendement ( dans le cas thermique )
                    # Energie = V_0*(ma-mgcos(alpha)*Cr - mgsin(alpha) - 0.5*ro*SCx * V_0**2)*Randement
                    if F_trac >= 0 :
                        energy_consumed_metre.append(  ( times_metre[-1]-times_metre[-2] )
                                                        *( chromosome[i] )
                                                        *(  m*g*cos( _dist_and_slope[j][1] )*C_r
                                                        + m*g*sin( _dist_and_slope[j][1] )
                                                        + 0.5*Rw*SC_x
                                                        * chromosome[i]**2  )
                                                        * Rdm_positive
                                                        #*(1 + ( abs(_dist_and_slope[j][1])/_dist_and_slope[j][1] ) )
                                                        )

                        if energy_consumed_metre[-1] < 0 :
                            print(" Error !")

                    else:
                        #energy_consumed_metre.append(0)
                        energy_consumed_metre.append(  ( times_metre[-1]-times_metre[-2] )
                                                        *( chromosome[i] )
                                                        *(  m*g*cos( _dist_and_slope[j][1] )*C_r
                                                        + m*g*sin( _dist_and_slope[j][1] )
                                                        + 0.5*Rw*SC_x
                                                        * chromosome[i]**2  )
                                                        * Rdm_negative
                                                        #*(1 + ( abs(_dist_and_slope[j][1])/_dist_and_slope[j][1] ) )
                                                        )

                    j += 1

                tps.append(times_metre[-1])
                #k = j-1

            else: #  V_0 = chromosome[i-1] "c'est la vitesse constante d'avant"

                last_time = times_metre[-1] # la derniere durée, à laquelle on va additionner les autres durées

                while( j < len(_dist_and_slope) and j < round(cumulative_raw_distance[i])  ):

                    coeff = [0.5*chromosome[i] , chromosome[i-1] , -(j-k) ]
                    possibles_solutions = [s for s in np.roots(coeff) if s > 0  ]
                    tps_for_metre =  min(possibles_solutions)


                    times_metre.append( last_time + tps_for_metre )
                    vts_metre.append(  chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-last_time )  )  )

                    #=====================================================================================================
                    # calcul de F_trac = ma - Fa - Fr - Fw
                    F_trac =   (m*chromosome[i]
                    + m*g*cos( _dist_and_slope[j][1] )*C_r
                    + m*g*sin( _dist_and_slope[j][1] )
                    + 0.5*Rw*SC_x * ( chromosome[i-1] +  chromosome[i]*( times_metre[-1]-last_time )  )**2)
                    #=====================================================================================================

                    # vts_metre.append(  chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-times_metre[-2] )  )  )

                    # Calucul de puissance en ce point j ( En = dt*V(t)*F*Randement )
                    # quand  pente > 0 ==> ya un randement positif
                    # quand  pente <= 0 ==> ya pas de rendement ( dans le cas thermique )
                    # Energie = V_0*(ma-mgcos(alpha)*Cr - mgsin(alpha) - 0.5*ro*SCx * V_0**2)*Randement
                    if F_trac >= 0 :
                        energy_consumed_metre.append(  ( times_metre[-1]-times_metre[-2] )
                                                        *( chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-last_time ) ) )
                                                        # *( chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-times_metre[-2] ) ) )
                                                        *( m*chromosome[i]
                                                        + m*g*cos( _dist_and_slope[j][1] )*C_r
                                                        + m*g*sin( _dist_and_slope[j][1] )
                                                        + 0.5*Rw*SC_x
                                                        *( chromosome[i-1] +  chromosome[i]*( times_metre[-1]-last_time )  )**2  )
                                                        # ( chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-times_metre[-2] ) ) ) **2  )
                                                        *Rdm_positive
                                                        #*(1 + ( abs(_dist_and_slope[j][1])/_dist_and_slope[j][1] ) )
                                                        )

                        if energy_consumed_metre[-1] < 0 :
                            print(" Error !!!!")

                    else:
                        #energy_consumed_metre.append(0)
                        energy_consumed_metre.append(  ( times_metre[-1]-times_metre[-2] )
                                                        *( chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-last_time ) ) )
                                                        # *( chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-times_metre[-2] ) ) )
                                                        *( m*chromosome[i]
                                                        + m*g*cos( _dist_and_slope[j][1] )*C_r
                                                        + m*g*sin( _dist_and_slope[j][1] )
                                                        + 0.5*Rw*SC_x
                                                        *( chromosome[i-1] +  chromosome[i]*( times_metre[-1]-last_time )  )**2  )
                                                        # ( chromosome[i-1] + ( chromosome[i]*( times_metre[-1]-times_metre[-2] ) ) ) **2  )
                                                        *Rdm_negative
                                                        #*(1 + ( abs(_dist_and_slope[j][1])/_dist_and_slope[j][1] ) )
                                                        )

                    j += 1

                tps.append(times_metre[-1])
                #k = j-1

            k = j-1
            i += 1

    return  cumulative_raw_distance, energy_consumed_metre, times_metre, vts_metre,tps


#------------------------------------------------------------------------------------------------
#---------------------------------  PLOT CHROMOSOMES -------------------------------------------------------
#------------------------------------------------------------------------------------------------
"""
    Entrée :  [[[Chromosome]], [Vmax], [Durée (s) jusq'u moitié de la phase d'accel], [Durée (s)], Title, ]
    Sortie :  [Distance par m], [Durée par m], [Energie par m], [Vitt par m]
"""
def plot_chromosome(chromosome_table, spd, duration_per_phase, duration_raw_per_phase, title):

    #======================== pour le plot du Vmax   ====================================
    duration_Vmax_plot = [0]
    i=0
    while(i < len(duration_per_phase) ):
        if(i==0):
            duree = duration_per_phase[i][0]+ duration_per_phase[i][1] + duration_per_phase[i][2]
            i = i + 1
        else:
            duree = duration_Vmax_plot[-1] + sum( duration_per_phase[i] )
            i = i + 1

        duration_Vmax_plot.append(duree)
        duration_Vmax_plot.append(duree)

    # print("duration_Vmax_plot " +str(duration_Vmax_plot) )

    #=======================================================================================
    speed_Vmax_plot = []
    for v in spd:
        speed_Vmax_plot.append(v)
        speed_Vmax_plot.append(v)
    speed_Vmax_plot.append(spd[-1])
    # print(speed_Vmax_plot)

    #====================================== plot pour le Vmin  =================================
    # on utilise le meme tableau de duree que pour le Vmax (au dessus)

    #calcul des vitesses Min
    speed_Vmin_plot = []
    for v in spd:

        if v <= 13.88: # 50 kmh
            speed_Vmin_plot.append(8.33)
            speed_Vmin_plot.append(8.33)
        elif v <= 25:  # 90 kmh
            speed_Vmin_plot.append(13.88)
            speed_Vmin_plot.append(13.88)
        else:                   # 110 ou 130 kmh
            speed_Vmin_plot.append(22.22)
            speed_Vmin_plot.append(22.22)

    speed_Vmin_plot.append(speed_Vmin_plot[-1])

    #=======================================================================================
    duration_plot = [0]
    for duree in duration_raw_per_phase:
        duration_plot.append(duree+ duration_plot[-1])
    #print(duration_plot)

    vitesses = [0]
    for i in range(0, len(chromosome_table)-1):
        if(i%2 == 1):
            vitesses.append(chromosome_table[i])
            vitesses.append(chromosome_table[i])
    vitesses.append(0)
    #print(vitesses)

    #-------------------- Plot -------------------------------------------------
    plt.figure(figsize=(10,5))
    plt.plot(duration_plot,vitesses)

    plt.plot(duration_Vmax_plot,speed_Vmax_plot)
    #plt.plot(duration_Vmax_plot,speed_Vmin_plot)
    #plt.fill_between(duration_Vmax_plot,speed_Vmax_plot,alpha=0.1)

    plt.plot(duration_plot, vitesses, 'o')
    plt.xlabel("Time(s)")
    plt.ylabel("Speed (m/s)")
    plt.legend(['Speed','Speed Max'])
    plt.title(str(title))
    #plt.legend(['Speed','Speed Max', 'Speed min'])
    plt.fill_between(duration_plot,vitesses,alpha=0.1)
    plt.grid()
    plt.show()
#=======================================================================================
################################################################## Crossovers + Mutations


""" croisement 1: la moyenne des vitesses en gardant les accelerations du parent 1 (meilleur parent)
    ainsi que les vitesses si la moyenne n'est pas possible """

def crossover_speed_mean(chromosome_1 , chromosome_2):
    chromosome_result = []

    for i in range(len(chromosome_1)):

        if(i%2 == 0):
            chromosome_result.append(chromosome_1[i])

        else:
            if( i > 1 and ( chromosome_1[i-1] > 0 and chromosome_2[i-1] >= 0 ) and chromosome_result[i-2] < (chromosome_1[i] + chromosome_2[i])/2 ):
                if round((chromosome_1[i] + chromosome_2[i])/2  ,2 ) != 0 :
                    chromosome_result.append( round((chromosome_1[i] + chromosome_2[i])/2  ,2 ) )
                else:
                    chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2  )

            elif( i > 1 and ( chromosome_1[i-1] < 0 and chromosome_2[i-1] <= 0 ) and chromosome_result[i-2] > (chromosome_1[i] + chromosome_2[i])/2 ):
                if round((chromosome_1[i] + chromosome_2[i])/2  ,2 ) != 0 :
                    chromosome_result.append( round((chromosome_1[i] + chromosome_2[i])/2  ,2 ) )
                else :
                    chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2   )


            else:
                chromosome_result.append( chromosome_1[i] )


    return chromosome_result



""" croisement 2: la moyenne des vitesses et des accelerations en gardant les accelerations et les vitesses
    du parent 1 si la moyenne n'est pas possible """
    # en gardant ceux du "MEILLEUR" parent

def crossover_speed_and_acceleration_mean(chromosome_1 , chromosome_2):
    chromosome_result = []

    for i in range(len(chromosome_1)):
        if (i == 0): # accel et vitesse de la premiere phase (tjrs les memes qlq le chrom)
            chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2  )
            chromosome_result.append( (chromosome_1[i+1] + chromosome_2[i+1])/2  )

        elif(i%2 == 0):

            if( ( chromosome_1[i] > 0 and chromosome_2[i] >= 0 ) and chromosome_result[i-1] < (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                chromosome_result.append( (chromosome_1[i+1] + chromosome_2[i+1])/2 )

            elif( ( chromosome_1[i] < 0 and chromosome_2[i] <= 0 ) and chromosome_result[i-1] > (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                chromosome_result.append( (chromosome_1[i+1] + chromosome_2[i+1])/2 )

            elif( ( chromosome_1[i] < 0 and chromosome_2[i] <= 0 ) and chromosome_result[i-1] <= (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                chromosome_result.append( chromosome_1[i+1] )

            elif( ( chromosome_1[i] > 0 and chromosome_2[i] >= 0 ) and chromosome_result[i-1] >= (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                chromosome_result.append( chromosome_1[i+1]  )

            # on garde ceux du parent 1 (le meilleur)
            elif( chromosome_1[i] == 0) :
                chromosome_result.append( chromosome_1[i] )
                chromosome_result.append( chromosome_result[i-1] )
            else:
                chromosome_result.append( chromosome_1[i] )
                chromosome_result.append( chromosome_1[i+1] )

    return chromosome_result


"""
    Entrée :  [Chromosome], [Chromosome]
    Sortie :  [Chromosome], bool use_this_one_point_crossover (Operation used?)
"""
""" croisement 3: echange en un point random, cad qu'avant ce point random on garde la prtie du parent 1
    et apres, la partie du parent 2. Si ce n'est pas possible on applique le croisement 2 (juste au dessus) """


def crossover_exchange_one_point(chromosome_1 , chromosome_2):
    chromosome_result = []
    rand_cut_point = rdm.randint(2, len(chromosome_1)-2 )
    use_this_one_point_crossover = True

    # On tombe sur une acceleration
    if(
        ( rand_cut_point%2 == 0 and chromosome_1[rand_cut_point] > 0 and chromosome_2[rand_cut_point] > 0
        and chromosome_2[rand_cut_point+1] > chromosome_1[rand_cut_point-1])
        or
        (rand_cut_point%2 == 0 and chromosome_1[rand_cut_point] < 0 and chromosome_2[rand_cut_point] < 0
        and chromosome_2[rand_cut_point+1] < chromosome_1[rand_cut_point-1])
      )  :

        for i in range(len(chromosome_1)):

            if i < rand_cut_point :
                chromosome_result.append( chromosome_1[i] )
            else:
                chromosome_result.append( chromosome_2[i] )

    # On tombe sur une vitesse
    elif(
        (rand_cut_point%2 == 1 and chromosome_1[rand_cut_point-1] > 0
        and chromosome_2[rand_cut_point] > chromosome_1[rand_cut_point-2])
        or
        (rand_cut_point%2 == 1 and chromosome_1[rand_cut_point-1] < 0
        and chromosome_2[rand_cut_point] < chromosome_1[rand_cut_point-2])
       ) : # vitesse

        for i in range(len(chromosome_1)):

            if i < rand_cut_point :
                chromosome_result.append( chromosome_1[i] )
            else:
                chromosome_result.append( chromosome_2[i] )

    else :
        use_this_one_point_crossover = False
        for i in range(len(chromosome_1)):

            if (i == 0): # accel et vitesse de la premiere phase (tjrs les memes qlq le chrom)
                chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                chromosome_result.append(  (chromosome_1[i+1] + chromosome_2[i+1])/2 )

            elif(i%2 == 0):

                if( ( chromosome_1[i] > 0 and chromosome_2[i] >= 0 ) and chromosome_result[i-1] < (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                    chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                    chromosome_result.append( (chromosome_1[i+1] + chromosome_2[i+1])/2 )

                elif( ( chromosome_1[i] < 0 and chromosome_2[i] <= 0 ) and chromosome_result[i-1] > (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                    chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                    chromosome_result.append( (chromosome_1[i+1] + chromosome_2[i+1])/2 )

                elif( ( chromosome_1[i] < 0 and chromosome_2[i] <= 0 ) and chromosome_result[i-1] <= (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                    chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                    chromosome_result.append( chromosome_1[i+1]  )

                elif( ( chromosome_1[i] > 0 and chromosome_2[i] >= 0 ) and chromosome_result[i-1] >= (chromosome_1[i+1] + chromosome_2[i+1])/2 ):
                    chromosome_result.append( (chromosome_1[i] + chromosome_2[i])/2 )
                    chromosome_result.append( chromosome_1[i+1]  )

                # on garde ceux du parent 1 (le meilleur)
                else:
                    if chromosome_1[i] == 0 :
                        chromosome_result.append( chromosome_1[i] )
                        chromosome_result.append( chromosome_result[i-1] )
                    else:
                        chromosome_result.append( chromosome_1[i] )
                        chromosome_result.append( chromosome_1[i+1] )

    return chromosome_result, use_this_one_point_crossover

""" Mutation : on prend une des accelerations du chromosome et on lui donne la plus grande valeur de toutes
    les accelations possibles (cad: si c une accel negative on lui donne la plus petite et si c une
                               accel positive on lui donne la plus grande accel PARMIS LES ACCEL DU CHROM)"""

def mutation_chromosome(chromosome_1):

    chromosome_result = chromosome_1.copy()

    # prendre une acceleration aléatoirement
    gene = rdm.randrange(0, len(chromosome_1)-1,2)

    # si l'acceleration prise est negative ==> on la remplace avec la plus petite accel du chrom
    if chromosome_result[gene] < 0 :
        # parmis toutes les accel negatives de ce chromosome
        chromosome_result[gene]  = min([i for i in chromosome_result[0:len(chromosome_result):2]])

    # si l'acceleration prise est positive ==> on la remplace avec la plus grosse accel du chrom
    elif chromosome_result[gene] > 0 :
        # parmis toutes les accel positives de ce chromosome
        chromosome_result[gene]  = max([i for i in chromosome_result[0:len(chromosome_result):2]])

    return chromosome_result

############################################################ KV File

KV = '''
#:import MapView kivy.garden.mapview.MapView


<WatingSpinner@MDSpinner>:
    size_hint: None, None
    size: dp(48), dp(48)
    pos_hint: {'center_x': .5, 'center_y': .5}
    determinate: False

<CheckVehiculeType@MDCheckbox>:
    group: 'VehiculeTypeGroup'
    size_hint: None, None
    size: dp(48), dp(48)

<CheckVehiculeTech@MDCheckbox>:
    group: 'VehiculeTechGroup'
    size_hint: None, None
    size: dp(48), dp(48)

<CheckEnvironnementDirVentNS@MDCheckbox>:
    group: 'EnvironnementDirVentNS'
    size_hint: None, None
    size: dp(48), dp(48)

<CheckEnvironnementDirVentWE@MDCheckbox>:
    group: 'EnvironnementDirVentWE'
    size_hint: None, None
    size: dp(48), dp(48)

<CheckSegmentationOptions@MDCheckbox>:
    group: 'SegmentationOptions'
    size_hint: None, None
    size: dp(48), dp(48)

<CheckOptimisationObjectivesn@MDCheckbox>:
    group: 'OptimisationObjectives'
    size_hint: None, None
    size: dp(48), dp(48)

<ContentNavigationDrawer>

    MDNavigationDrawerMenu:

        MDNavigationDrawerHeader:
            title: "NAVeco"
            title_color: "#ffffff"
            text: "V 1.0"
            spacing: "4dp"
            padding: "12dp", 0, 0, "56dp"

        MDNavigationDrawerLabel:
            text: "Param:"

        MDNavigationDrawerDivider

        OneLineAvatarIconListItem:
            text: "Carte"
            on_press:
                root.nav_drawer.set_state("close")
                root.screen_manager.current = "Main"
            IconLeftWidgetWithoutTouch:
                icon: "home"

        OneLineAvatarIconListItem:
            text: "Vehicule"
            on_press:
                root.nav_drawer.set_state("close")
                root.screen_manager.current = "Vehicule"
            IconLeftWidgetWithoutTouch:
                icon: "car-info"

        OneLineAvatarIconListItem:
            text: "Environnement"
            on_press:
                root.nav_drawer.set_state("close")
                root.screen_manager.current = "Environnement"
            IconLeftWidgetWithoutTouch:
                icon: "pine-tree"

        OneLineAvatarIconListItem:
            text: "Paramètres"
            on_press:
                root.nav_drawer.set_state("close")
                root.screen_manager.current = "Parametres"
            IconLeftWidgetWithoutTouch:
                icon: "application-cog"

        MDNavigationDrawerDivider

        OneLineAvatarIconListItem:
            text: "Nous contacter"
            on_press:
                root.nav_drawer.set_state("close")
                root.screen_manager.current = "Contacter"
            IconLeftWidgetWithoutTouch:
                icon: "email"


MDScreen:
    name: "Principal"

    MDNavigationLayout:

        MDScreenManager:
            id: screen_manager

            MDScreen:
                id:MainScreen
                name: "Main"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        id: AppBarmap
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "NAVeco project"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MyMapView:
                        size_hint: 1, 0.9
                        id: map
                        on_map_relocated: app.DrawItinerary()

                MDFloatingActionButtonSpeedDial:
                    id: speed_dial
                    data: app.data
                    root_button_anim: True
                    hint_animation: True
                    icon: "arrow-right"



            MDScreen:
                name: "Vehicule"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Vehicule"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 20
                        padding : 20
                        size_hint: 1, 1
                        ScrollView:
                            bar_width:10
                            size_hint: 1, 3
                            MDList:
                                id: VehiculesContainer
                        MDBoxLayout:
                            orientation :'horizontal'
                            spacing : 20
                            padding : 20
                            MDFillRoundFlatIconButton:
                                icon:'pen-plus'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Nouvelle"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "VehiculeNew"
                            Widget:
                            MDFillRoundFlatIconButton:
                                icon:'content-save'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Effacer"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    app.SQL_Vehicule_delete()


            MDScreen:
                name: "Environnement"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Environnement"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 20
                        padding : 20
                        size_hint: 1, 1
                        ScrollView:
                            bar_width:10
                            size_hint: 1, 3
                            MDList:
                                id: EnvironnementContainer
                        MDBoxLayout:
                            orientation :'horizontal'
                            spacing : 20
                            padding : 20
                            MDFillRoundFlatIconButton:
                                icon:'pen-plus'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Nouvelle"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "EnvironementNew"
                            Widget:
                            MDFillRoundFlatIconButton:
                                icon:'content-save'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Effacer"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    app.SQL_Environnement_delete()


            MDScreen:
                name: "Parametres"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Parametres"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 20
                        padding : 20
                        size_hint: 1, 1
                        ScrollView:
                            bar_width:10
                            size_hint: 1, 3
                            MDList:
                                MDTextField:
                                    id: ParamEchDist
                                    text:"1"
                                    helper_text:"Echantillonnage de distance [m]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: ParamFactDist
                                    text:"0.5"
                                    helper_text:"Facteur distance [%1]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: ParamFactVites
                                    text:"0.0"
                                    helper_text:"Facteur vitesse [%1]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: ParamFactEnerg
                                    text:"0.4"
                                    helper_text:"Facteur energie [%1]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: ParamFactConf
                                    text:"0.1"
                                    helper_text:"Facteur confort [%1]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDNavigationDrawerDivider
                                    padding: [0, 10, 0, 110]
                                MDBoxLayout:
                                    orientation:"horizontal"
                                    padding : 10
                                    MDBoxLayout:
                                        orientation:"vertical"
                                        spacing : 0
                                        MDIcon:
                                            icon:'transit-detour'
                                        MDSwitch:
                                            id: ParamInterpolationPente
                                    Widget:
                                    MDBoxLayout:
                                        orientation:"vertical"
                                        spacing : 0
                                        MDIcon:
                                            icon:'weather-pouring'
                                        MDSwitch:
                                            id: ParamOptionPluie

                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            MDFillRoundFlatIconButton:
                                icon:'arrow-left'
                                text: "Arrière"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Main"
                            Widget:
                            MDFillRoundFlatIconButton:
                                icon:'content-save'
                                text: "Enregistrer"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Main"

            MDScreen:
                name: "Contacter"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Nous contacter"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 0
                        padding : 20
                        Widget:
                        MDBoxLayout:
                            orientation :'horizontal'
                            spacing : 0
                            padding : 10
                            Widget:
                                size_hint: 0.1, 1
                            MDTextFieldRect:
                                text:"Write your message here."
                                size_hint: 0.8, 2
                                # height: "30dp"
                                background_color: '#ffffff'
                            Widget:
                                size_hint: 0.1, 1
                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            padding : 20
                            MDFillRoundFlatIconButton:
                                icon:'arrow-left'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Arrière"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Main"
                            Widget:
                            MDFillRoundFlatIconButton:
                                icon:'send-outline'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Send"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Main"

            MDScreen:
                name: "DataTrip"
                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Trip"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 20
                        padding : 20
                        size_hint: 1, 1
                        ScrollView:
                            bar_width:10
                            size_hint: 1, 3
                            MDList:
                                MDBoxLayout:
                                    orientation:"horizontal"
                                    spacing:"10dp"
                                    adaptive_height: True
                                    MDRaisedButton:
                                        id: VehiculeSelected
                                        text: "     Vehicule      "
                                        on_press:
                                            app.Trip_Data_refresh()
                                    Widget:
                                    MDRaisedButton:
                                        id: EnvironnementSelected
                                        text: "Environnement"
                                        on_press:
                                            app.Trip_Data_refresh()
                                MDBoxLayout:
                                    orientation:"horizontal"
                                    spacing:"10dp"
                                    adaptive_height: True
                                    MDBoxLayout:
                                        orientation :'horizontal'
                                        size_hint: 1, 1
                                        MDTextField:
                                            id: FromTextInput
                                            hint_text:"From"
                                    MDTextField:
                                        id: ToTextInput
                                        hint_text:"To"
                                MDRaisedButton:
                                    id: PlaceSelection
                                    bg_color:"#c23328"
                                    text: "Écrivez-vous un endroit, svp"
                                    size_hint: 1, 1
                                    on_press:
                                        app.PlaceSelectinoFunct()
                                MDNavigationDrawerDivider
                                MDBoxLayout:
                                    orientation:"horizontal"
                                    spacing:"1dp"
                                    adaptive_height: True
                                    padding : [0,10]
                                    MDLabel:
                                        text: "Psgr: "
                                        halign: "left"
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'account'
                                        MDCheckbox:
                                            id: Passenger1
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'account'
                                        MDCheckbox:
                                            id: Passenger2
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'account'
                                        MDCheckbox:
                                            id: Passenger3
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'account'
                                        MDCheckbox:
                                            id: Passenger4
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                MDNavigationDrawerDivider
                                MDTextField:
                                    id: ChargeSuppl
                                    hint_text:"Charge supplementaire [Kg]"
                                MDBoxLayout:
                                    orientation:"horizontal"
                                    spacing:"10dp"
                                    adaptive_height: True
                                    padding :0
                                    MDRaisedButton:
                                        id: TimeDeparture
                                        bg_color:"#c23328"
                                        text: "Temps de depart"
                                        size_hint: 1, 1
                                        on_press:
                                            app.show_time_picker_dep()
                                    MDRaisedButton:
                                        id: TimeArrive
                                        bg_color:"#c23328"
                                        text: "Temps d'arrivée"
                                        size_hint: 1, 1
                                        on_press:
                                            app.show_time_picker_arr()
                                MDTextField:
                                    id: TimeTolerance
                                    hint_text:"Tolerance du temps [min]"
                                MDLabel:
                                    text: "  "
                                    halign: "center"
                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            MDFillRoundFlatIconButton:
                                icon:'arrow-left'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                size_hint: 1, 1
                                text: "Arrière"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Main"
                            Widget:
                            MDFillRoundFlatIconButton:
                                icon:'car-arrow-right'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                size_hint: 1, 1
                                text: '  GO  '
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    app.GetItinerary()

            MDScreen:
                name: "EnvironementNew"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Nouvelle Environement"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 0
                        padding : [30,30]
                        MDTextField:
                            id: EnvironnementNom
                            text:"Environnement_1"
                            helper_text:"Nom"
                            #text_color_focus: '#ff0000'
                            text_color_normal: '#ffffff'
                            helper_text_mode: "persistent"
                        MDTextField:
                            id: EnvironnementGrav
                            text:"9.81"
                            helper_text:"Gravité [m/s3]"
                            #text_color_focus: '#ff0000'
                            text_color_normal: '#ffffff'
                            helper_text_mode: "persistent"
                        MDTextField:
                            id: EnvironnementMassVolAir
                            text:"1.25"
                            helper_text:"Masse volum. de l'air [Kg/m3]"
                            #text_color_focus: '#ff0000'
                            text_color_normal: '#ffffff'
                            helper_text_mode: "persistent"
                        MDTextField:
                            id: EnvironnementCoefRoul
                            text:"0.01"
                            helper_text:"Coef. roulement [N/rad]"
                            #text_color_focus: '#ff0000'
                            text_color_normal: '#ffffff'
                            helper_text_mode: "persistent"
                        MDTextField:
                            id: EnvironnementVittVent
                            text:"0.00"
                            helper_text:"Vitesse du vent [m/s3]"
                            #text_color_focus: '#ff0000'
                            text_color_normal: '#ffffff'
                            helper_text_mode: "persistent"
                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            padding : [0,10]
                            MDLabel:
                                text: "Direction du vent:"
                                halign: "left"
                            Widget:
                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            Widget:
                            MDBoxLayout:
                                orientation:"horizontal"
                                spacing:"1dp"
                                MDIcon:
                                    icon:'arrow-left-bold-box'
                                CheckEnvironnementDirVentWE:
                                    id: EnvironnementDirectVentWest
                                    size_hint: None, None
                                    size: "48dp", "48dp"
                                    pos_hint: {'center_x': .5, 'center_y': .5}
                            MDBoxLayout:
                                orientation:"horizontal"
                                spacing:"1dp"
                                MDIcon:
                                    icon:'arrow-up-bold-box'
                                CheckEnvironnementDirVentNS:
                                    id: EnvironnementDirectVentNorth
                                    size_hint: None, None
                                    size: "48dp", "48dp"
                                    pos_hint: {'center_x': .5, 'center_y': .5}
                            MDBoxLayout:
                                orientation:"horizontal"
                                spacing:"1dp"
                                MDIcon:
                                    icon:'arrow-down-bold-box'
                                CheckEnvironnementDirVentNS:
                                    id: EnvironnementDirectVentSouth
                                    size_hint: None, None
                                    size: "48dp", "48dp"
                                    pos_hint: {'center_x': .5, 'center_y': .5}
                            MDBoxLayout:
                                orientation:"horizontal"
                                spacing:"1dp"
                                MDIcon:
                                    icon:'arrow-right-bold-box'
                                CheckEnvironnementDirVentWE:
                                    id: EnvironnementDirectVentEast
                                    size_hint: None, None
                                    size: "48dp", "48dp"
                                    pos_hint: {'center_x': .5, 'center_y': .5}

                            Widget:
                        MDLabel:
                            text: "  "
                            halign: "center"
                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            MDFillRoundFlatIconButton:
                                icon:'arrow-left'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Arrière"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Environnement"
                            Widget:
                            MDFillRoundFlatIconButton:
                                icon:'content-save'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Enregistrer"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    app.SQL_Environnement_add()

            MDScreen:
                name: "VehiculeNew"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "VehiculeNew"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 20
                        padding : 20
                        size_hint: 1, 1
                        ScrollView:
                            bar_width:10
                            size_hint: 1, 3
                            MDList:
                                MDTextField:
                                    id: VehiculeNom
                                    text:"Vehicule_1"
                                    helper_text:"Nom"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    theme_text_color: "white"
                                    helper_text_mode: "persistent"
                                MDBoxLayout:
                                    orientation:"horizontal"
                                    spacing:"1dp"
                                    adaptive_height: True
                                    padding : [0,20]
                                    MDLabel:
                                        text: "Type:"
                                        halign: "left"
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'motorbike'
                                        CheckVehiculeType:
                                            id: VehiculeTypeMoto
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'car-hatchback'
                                        CheckVehiculeType:
                                            id: VehiculeTypeSmallCar
                                            active: True
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'car-estate'
                                        CheckVehiculeType:
                                            id: VehiculeTypeBigCar
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                MDTextField:
                                    id: VehiculeMasse
                                    text:"1500"
                                    helper_text:"Masse [m]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeRayon
                                    text:"0.3099"
                                    helper_text:"Rayon de la roue [m]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeMaxFrein
                                    text:"2000"
                                    helper_text:"Max. frenaige [Nm]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeRapRed
                                    text:"14.577"
                                    helper_text:"Rapport de réduction  boite vitesse[-]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeMaxPot
                                    text:"10000"
                                    helper_text:"Puissance Max. [W]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeCoefCoup
                                    text:"1e-07"
                                    helper_text:"Coeff de rend Couple [-]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeCoefVites
                                    text:"5e-09"
                                    helper_text:"Coeff de rend Vitesse [-]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeMaxTracc
                                    text:"260"
                                    helper_text:"Couple max [Nm]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDTextField:
                                    id: VehiculeMaxRPM
                                    text:"10000"
                                    helper_text:"Vitesse max [RPM]"
                                    #text_color_focus: '#ff0000'
                                    text_color_normal: '#ffffff'
                                    helper_text_mode: "persistent"
                                MDBoxLayout:
                                    orientation:"horizontal"
                                    spacing:"1dp"
                                    adaptive_height: True
                                    padding : [0,20]
                                    MDLabel:
                                        text: "Tech:"
                                        halign: "left"
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'battery-charging-high'
                                        CheckVehiculeTech:
                                            id: VehiculeTechElectr
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'gas-station'
                                        CheckVehiculeTech:
                                            id: VehiculeTechTherm
                                            active: True
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                                    MDBoxLayout:
                                        orientation:"horizontal"
                                        spacing:"1dp"
                                        MDIcon:
                                            icon:'ev-station'
                                        CheckVehiculeTech:
                                            id: VehiculeTechHybr
                                            size_hint: None, None
                                            size: "48dp", "48dp"
                                            pos_hint: {'center_x': .5, 'center_y': .5}
                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            MDFillRoundFlatIconButton:
                                icon:'arrow-left'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Arrière"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Vehicule"
                            Widget:
                            MDFillRoundFlatIconButton:
                                icon:'content-save'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                text: "Enregistrer"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    app.SQL_Vehicule_add()


            MDScreen:
                id: DataLoggerScreen
                name: "DataLoggerPage"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Data Logger"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDBoxLayout:
                        orientation :'vertical'
                        spacing : 20
                        padding : 20
                        size_hint: 1, 1
                        MDBoxLayout:
                            id:GraphPieChartID
                            orientation:"vertical"
                            adaptive_height: True
                        MDBoxLayout:
                            id:GraphElevID
                            orientation:"vertical"
                            adaptive_height: True
                        MDBoxLayout:
                            id:GraphPenteID
                            orientation:"vertical"
                            adaptive_height: True
                        MDBoxLayout:
                            id:GraphSpeedID
                            orientation:"vertical"
                            adaptive_height: True
                        Widget:
                        MDBoxLayout:
                            orientation:"horizontal"
                            spacing:"1dp"
                            adaptive_height: True
                            MDFillRoundFlatIconButton:
                                icon:'arrow-left'
                                pos_hint : {'center_x':0.5,'center_y':0.5}
                                size_hint : {1,0.5}
                                text: "Arrière"
                                theme_text_color: "Custom"
                                text_color: "white"
                                theme_icon_color: "Custom"
                                icon_color: "white"
                                on_press:
                                    root.ids.screen_manager.current = "Main"


            MDScreen:
                name: "Template"

                MDBoxLayout:
                    orientation :'vertical'
                    spacing : 0
                    padding : 0
                    MDTopAppBar:
                        pos_hint: {"top": 1}
                        elevation: 4
                        title: "Template"
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                    MDLabel:
                        text: "Template"
                        halign: "center"

        MDNavigationDrawer:
            id: nav_drawer
            radius: (0, 16, 16, 0)

            ContentNavigationDrawer:
                screen_manager: screen_manager
                nav_drawer: nav_drawer
'''

# class VehiculeDataBaseControls(MDBoxLayout):
#     pass

class WatingSpinner(MDSpinner):
    pass

class MyMapView(MapView):
    grp = ObjectProperty(None)
    grp1 = ObjectProperty(None)

class ContentNavigationDrawer(MDScrollView):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

class NAVecoApp(MDApp):
    data = DictProperty()

    def build(self):

        self.theme_cls.primary_hue = "500"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"#Light

        self.root = Builder.load_string(KV)

        self.root.ids.ToTextInput.bind(text = self.SearchTo)
        self.root.ids.FromTextInput.bind(text = self.SearchFrom)

        ##################################################### DialogBlocks

        self.dialog_Waitting = MDDialog(
                title=" ",
                type="custom",
                radius=[20, 7, 20, 7],
                content_cls=MDBoxLayout(
                    MDLabel(
                        id="WaitingTextID",
                        text=" ",
                    ),
                    WatingSpinner(),
                    MDLabel(
                        text=" ",
                    ),
                    orientation="vertical",
                    spacing="30dp",
                    adaptive_height= True
                )
            )
        # Avoid to get out if click outside of Dialog
        self.dialog_Waitting.auto_dismiss = False

        self.dialog_SureData = MDDialog(
                title="Data confirmation",
                type="custom",
                content_cls=MDBoxLayout(
                    MDLabel(
                        text="The passengers numbers has been selected?",
                    )
                ),
                buttons=[
                    MDFlatButton(
                        text="Yes",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release= lambda x: self.dialog_SureData.dismiss()
                    ),
                    MDFlatButton(
                        text="No",
                        theme_text_color="Custom",
                        on_release= lambda x: self.dialog_SureData.dismiss()
                    ),
                ],
                # on_open = lambda x: self.WaittingRouteFunct(),
            )

        ##################################################### Initial GPS SEARCH

        self.MapZoom = 15

        Place='18 Avenue Jacques Jezequel, Vanves'
        response = clientGM.geocode(Place)
        self.LatUsr = response[0]['geometry']['location']['lat'] #48.8187902
        self.LngUsr = response[0]['geometry']['location']['lng'] # 2.2911665

        self.root.ids.map.lat = self.LatUsr
        self.root.ids.map.lon = self.LngUsr
        self.root.ids.map.zoom = self.MapZoom # 10 Ville, 15 Rue, 19/20 Batiment, 1 Monde

        ##################################################### Define Relative Layout


        self.CardsLayout = MDRelativeLayout(
                MDRaisedButton(
                                id = "EcoRouteInfo",
                                pos_hint={"center_x": 0.2, "center_y": 0.83},
                                text="[b]Fast[/b]",
                                font_size=14,
                                md_bg_color="#673bb7",
                                padding=5,
                                halign = 'left',
                                on_release= lambda x: self.SelectedRoutInfo(),
                                ),
                MDRaisedButton(
                                id = "NormalRouteInfo",
                                pos_hint={"center_x": 0.5, "center_y": 0.83},
                                text="[b]Fast[/b]",
                                font_size=14,
                                md_bg_color="#673bb7",
                                padding=5,
                                halign = 'left',
                                on_release= lambda x: self.SelectedRoutInfo(),
                                ),
                MDRaisedButton(
                                id = "FastRouteInfo",
                                pos_hint={"center_x": 0.8, "center_y": 0.83},
                                text="[b]Fast[/b]",
                                font_size=14,
                                md_bg_color="#673bb7",
                                padding=5,
                                halign = 'left',
                                on_release= lambda x: self.SelectedRoutInfo(),
                                ),
                MDRaisedButton(
                                id = "CancelRoute",
                                size_hint=(0.9, 0.05),
                                pos_hint={"center_x": 0.5, "center_y": 0.74},
                                text="[b]Cancel[/b]",
                                font_size=14,
                                md_bg_color="#a23931",
                                on_release= lambda x: self.ResetRoutInfo(),
                                ),

            )

        self.ButtonNavigationLayout = MDRelativeLayout(
                MDFillRoundFlatButton(
                                id = "RefSpeedNavigation",
                                size_hint=(0.6, 0.3),
                                pos_hint={"center_x": 0.4, "center_y": 0.2},
                                text="[b]100[size=40]\nkm/h[/size][/b]",
                                font_size=110,
                                md_bg_color="#673bb7",
                                # on_release= lambda x: self.ResetRoutInfo(),
                                ),
                MDRaisedButton(
                                id = "InfoNavigation",
                                size_hint=(0.4, 0.05),
                                pos_hint={"center_x": 0.275, "center_y": 0.85},
                                text="[b]Data Logger[/b]",
                                font_size=14,
                                md_bg_color="#673bb7",
                                on_release= lambda x: self.DataloggerPageGo(),
                                ),
                MDRaisedButton(
                                id = "CancelNavigation",
                                size_hint=(0.4, 0.05),
                                pos_hint={"center_x": 0.725, "center_y": 0.85},
                                text="[b]Cancel[/b]",
                                font_size=14,
                                md_bg_color="#a23931",
                                on_release= lambda x: self.ResetRoutInfo(),
                                ),

            )

        ##################################################### Define data

        self.data = {
                'Center': [
                'crosshairs-gps',
                "on_press", lambda x: print("pressed Center"),
                "on_release", lambda x: self.Center_Data()
            ],
                'Trip': [
                'arrow-decision-auto',
                "on_press", lambda x: print("pressed Trip"),
                "on_release", lambda x: self.switch_to_Trip_Data(),
            ],
            }

        self.items = ["Electrique", "Thermique", "Hybride"]

        ##################################################### Define variables

        self.FromPlaceSelected = False
        self.ToPlaceSelected = False
        self.LastPlaceSelected = ''

        return self.root

    def Center_Data(self):

        print("pressed Center Inside")
        print(self.LatUsr)
        print(self.LngUsr)
        print(self.root.ids.map.lat)
        print(self.root.ids.map.lon)
        # self.root.ids.map.lat = self.LatUsr
        # self.root.ids.map.lon = self.LngUsr
        # print(self.root.ids.map.center)
        # self.root.ids.map.center_on(self.LatUsr, self.LngUsr)
        # print(self.root.ids.map.center_x)
        # print(self.root.ids.map.center_y)
        # self.root.ids.map.set_center_x
        # self.root.ids.map.set_center_y
        self.root.ids.map.walk(self.LatUsr, self.LngUsr)

    def switch_to_Trip_Data(self, *args, **kwargs):
        self.Trip_Data_refresh()
        self.root.ids.screen_manager.current = 'DataTrip'

    def on_start(self):

        self.SQL_Vehicule_creation()
        self.SQL_Vehicule_refresh()

        self.SQL_Environnement_creation()
        self.SQL_Environnement_refresh()

    def Trip_Data_refresh(self):
        # EnvironnementSelected VehiculeSelected

        con = sqlite3.connect("NAVecoAPP.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM EnvironnementNAVeco WHERE Choisi=:c",{"c":1})
        data = cur.fetchall()
        if (len(data)==0):
            self.root.ids.EnvironnementSelected.text = 'Environnement'
            self.root.ids.screen_manager.current = 'Environnement'
        elif (len(data)==1):
            self.root.ids.EnvironnementSelected.text = data[0][0]
        else:
            self.root.ids.EnvironnementSelected.text = '    Multi    '
        # self.root.ids.inputID.text
        con.commit()
        con.close()

        con = sqlite3.connect("NAVecoAPP.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM VehiculeNAVeco WHERE Choisi=:c",{"c":1})
        data = cur.fetchall()
        if (len(data)==0):
            self.root.ids.VehiculeSelected.text = 'Vehicule'
            self.root.ids.screen_manager.current = 'Vehicule'
        elif (len(data)==1):
            self.root.ids.VehiculeSelected.text = data[0][0]
        else:
            self.root.ids.VehiculeSelected.text = '  Multi '
        con.commit()
        con.close()

    def SQL_Vehicule_creation(self):
        connectionSQL = sqlite3.connect("NAVecoAPP.db")
        cursorSQL = connectionSQL.cursor()
        cursorSQL.execute("CREATE TABLE if not exists VehiculeNAVeco(Nom, Type, Masse, Rayon, MaxFrein, RapRed, MaxPot, CoeffCoup, CoefVites, MaxTracc, MaxRPM, Tech, Choisi)")
        connectionSQL.commit()
        connectionSQL.close()

    def SQL_Environnement_creation(self):
        connectionSQL = sqlite3.connect("NAVecoAPP.db")
        cursorSQL = connectionSQL.cursor()
        cursorSQL.execute("CREATE TABLE if not exists EnvironnementNAVeco(Nom, Grav, MassVolAir, CoefRoul, VittVent, DirVent, Choisi)")
        connectionSQL.commit()
        connectionSQL.close()

    def SQL_Environnement_add(self):
        try:
            con = sqlite3.connect("NAVecoAPP.db")
            cur = con.cursor()
            EnvironnementNom = self.root.ids.EnvironnementNom.text
            EnvironnementGrav = float(self.root.ids.EnvironnementGrav.text)
            EnvironnementMassVolAir = float(self.root.ids.EnvironnementMassVolAir.text)
            EnvironnementCoefRoul = float(self.root.ids.EnvironnementCoefRoul.text)
            EnvironnementVittVent = float(self.root.ids.EnvironnementVittVent.text)
            if (self.root.ids.EnvironnementDirectVentNorth.active):
                if (self.root.ids.EnvironnementDirectVentNorth.active and self.root.ids.EnvironnementDirectVentWest.active):
                    EnvironnementDirectVent = 'North-West'
                elif (self.root.ids.EnvironnementDirectVentNorth.active and self.root.ids.EnvironnementDirectVentEast.active):
                    EnvironnementDirectVent = 'North-East'
                else:
                    EnvironnementDirectVent = 'North'
            else:
                if (self.root.ids.EnvironnementDirectVentSouth.active and self.root.ids.EnvironnementDirectVentWest.active):
                    EnvironnementDirectVent = 'South-West'
                elif (self.root.ids.EnvironnementDirectVentSouth.active and self.root.ids.EnvironnementDirectVentEast.active):
                    EnvironnementDirectVent = 'South-East'
                else:
                    EnvironnementDirectVent = 'South'
            cur.execute("SELECT * FROM EnvironnementNAVeco WHERE Nom=:c",{"c":EnvironnementNom})
            data = cur.fetchall()
            print(data)
            if (len(data)==0):
                cur.execute("INSERT INTO EnvironnementNAVeco VALUES (?,?,?,?,?,?,?)",(EnvironnementNom, EnvironnementGrav, EnvironnementMassVolAir, EnvironnementCoefRoul, EnvironnementVittVent, EnvironnementDirectVent,False))
                cur.execute("SELECT * FROM EnvironnementNAVeco WHERE Nom=:c",{"c":EnvironnementNom})
                data = cur.fetchall()
                print(data)
                con.commit()
                con.close()
                self.SQL_Environnement_refresh()
                Snackbar(
                    text="Environnement added!",
                    snackbar_x="10dp",
                    snackbar_y="10dp",
                    size_hint_x=(
                        Window.width - (dp(10) * 2)
                    ) / Window.width
                ).open()
                self.root.ids.screen_manager.current = "Environnement"
            else:
                print("Environnement Name already used")
                Snackbar(
                    text="Environnement name already used",
                    snackbar_x="10dp",
                    snackbar_y="10dp",
                    size_hint_x=(
                        Window.width - (dp(10) * 2)
                    ) / Window.width
                ).open()
                con.commit()
                con.close()
        except:
            Snackbar(
                text="Data not allowed!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()


    def SQL_Vehicule_add(self):
        try:
            con = sqlite3.connect("NAVecoAPP.db")
            cur = con.cursor()
            VehiculeName = self.root.ids.VehiculeNom.text
            if (self.root.ids.VehiculeTypeMoto.active):
                VehiculeType = 'Moto'
            elif (self.root.ids.VehiculeTypeSmallCar.active):
                VehiculeType = 'Car'
            elif (self.root.ids.VehiculeTypeBigCar.active):
                VehiculeType = 'BigCar'
            else:
                VehiculeType = 'NaN'
            VehiculeMasse = float(self.root.ids.VehiculeMasse.text)
            VehiculeRayon = float(self.root.ids.VehiculeRayon.text)
            VehiculeMaxFrein = float(self.root.ids.VehiculeMaxFrein.text)
            VehiculeRapRed = float(self.root.ids.VehiculeRapRed.text)
            VehiculeMaxPot = float(self.root.ids.VehiculeMaxPot.text)
            VehiculeCoefCoup = float(self.root.ids.VehiculeCoefCoup.text)
            VehiculeCoefVites = float(self.root.ids.VehiculeCoefVites.text)
            VehiculeMaxTracc = float(self.root.ids.VehiculeMaxTracc.text)
            VehiculeMaxRPM = float(self.root.ids.VehiculeMaxRPM.text)
            if (self.root.ids.VehiculeTechElectr.active):
                VehiculeTech = 'Electrique'
            elif (self.root.ids.VehiculeTechTherm.active):
                VehiculeTech = 'Thermique'
            elif (self.root.ids.VehiculeTechHybr.active):
                VehiculeTech = 'Hybride'
            else:
                VehiculeTech = 'NaN'
            cur.execute("SELECT * FROM VehiculeNAVeco WHERE Nom=:c",{"c":VehiculeName})
            data = cur.fetchall()
            print(data)
            if (len(data)==0):
                cur.execute("INSERT INTO VehiculeNAVeco VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(VehiculeName, VehiculeType, VehiculeMasse, VehiculeRayon, VehiculeMaxFrein, VehiculeRapRed, VehiculeMaxPot, VehiculeCoefCoup, VehiculeCoefVites, VehiculeMaxTracc, VehiculeMaxRPM, VehiculeTech,False))
                cur.execute("SELECT * FROM VehiculeNAVeco WHERE Nom=:c",{"c":VehiculeName})
                data = cur.fetchall()
                print(data)
                con.commit()
                con.close()
                self.SQL_Vehicule_refresh()
                Snackbar(
                    text="Vehicule added!",
                    snackbar_x="10dp",
                    snackbar_y="10dp",
                    size_hint_x=(
                        Window.width - (dp(10) * 2)
                    ) / Window.width
                ).open()
                self.root.ids.screen_manager.current = "Vehicule"
            else:
                print("VehiculeName already used")
                Snackbar(
                    text="Vehicule name already used",
                    snackbar_x="10dp",
                    snackbar_y="10dp",
                    size_hint_x=(
                        Window.width - (dp(10) * 2)
                    ) / Window.width
                ).open()
                con.commit()
                con.close()
        except:
            Snackbar(
                text="Data not allowed!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()


    def SQL_Vehicule_refresh(self):
        con = sqlite3.connect("NAVecoAPP.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM VehiculeNAVeco")
        data = cur.fetchall()
        # print(data)
        print('Data inside vehicule DataBase:')
        self.root.ids.VehiculesContainer.clear_widgets()
        for elem in data:
            print(str(elem[0])+" "+str(elem[1])+" "+str(elem[2]))
            if (str(elem[1])=='Moto'):
                if (str(elem[-1])=='0'):
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="motorbike"
                            ),
                            bg_color="#121212",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
                else:
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="motorbike"
                            ),
                            bg_color="#4d367e",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
            elif (str(elem[1])=='Car'):
                if (str(elem[-1])=='0'):
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="car"
                            ),
                            bg_color="#121212",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
                else:
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="car"
                            ),
                            bg_color="#4d367e",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
            elif (str(elem[1])=='BigCar'):
                if (str(elem[-1])=='0'):
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="car-estate"
                            ),
                            bg_color="#121212",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
                else:
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="car-estate"
                            ),
                            bg_color="#4d367e",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
            else:
                if (str(elem[-1])=='0'):
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="car"
                            ),
                            bg_color="#121212",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
                else:
                    self.root.ids.VehiculesContainer.add_widget(
                        TwoLineIconListItem(
                            IconLeftWidget(
                                icon="car"
                            ),
                            bg_color="#4d367e",
                            text=str(elem[0]),
                            secondary_text= str(elem[11]),
                            on_release= lambda x=str(elem[0]): self.select_item_Vehicule(x),
                        )

                    )
        print('################################')
        con.commit()
        con.close()

    def select_item_Vehicule(self, text_item):
        con = sqlite3.connect("NAVecoAPP.db")
        cur = con.cursor()
        VehiculeNom = text_item.text
        cur.execute("SELECT * FROM VehiculeNAVeco WHERE Nom=:c",{"c":VehiculeNom})
        data = cur.fetchall()

        print(data)
        Current_color = hex_to_rgb('4d367e')

        if (text_item.bg_color[0]==Current_color[0]/255):
            text_item.bg_color="#121212"
            cur.execute("UPDATE VehiculeNAVeco SET Choisi = 0 WHERE Nom=:c",{"c":VehiculeNom})
            con.commit()
            con.close()
        else:
            text_item.bg_color="#4d367e"
            cur.execute("UPDATE VehiculeNAVeco SET Choisi = 1 WHERE Nom=:c",{"c":VehiculeNom})
            con.commit()
            con.close()

    def SQL_Environnement_refresh(self):
        con = sqlite3.connect("NAVecoAPP.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM EnvironnementNAVeco")
        data = cur.fetchall()
        # print(data)
        print('Data inside environnement DataBase:')
        self.root.ids.EnvironnementContainer.clear_widgets()
        for elem in data:
            print(str(elem[0])+" "+str(elem[1])+" "+str(elem[2]))
            if (str(elem[-1])=='0'):
                self.root.ids.EnvironnementContainer.add_widget(
                    TwoLineIconListItem(
                        IconLeftWidget(
                            icon="pine-tree-box"
                        ),
                        bg_color="#121212",
                        text=str(elem[0]),
                        secondary_text= "Direction du vent: "+str(elem[5]),
                        on_release= lambda x=str(elem[0]): self.select_item_Environ(x),
                    )

                )
            else:
                self.root.ids.EnvironnementContainer.add_widget(
                    TwoLineIconListItem(
                        IconLeftWidget(
                            icon="pine-tree-box"
                        ),
                        bg_color="#4d367e",
                        text=str(elem[0]),
                        secondary_text= "Direction du vent: "+str(elem[5]),
                        on_release= lambda x=str(elem[0]): self.select_item_Environ(x),
                    )

                )

        print('################################')
        con.commit()
        con.close()

    def select_item_Environ(self, text_item):
        # self.screen.ids.drop_item.set_item(text_item)
        # self.menu.dismiss()

        con = sqlite3.connect("NAVecoAPP.db")
        cur = con.cursor()
        EnvironnementNom = text_item.text
        cur.execute("SELECT * FROM EnvironnementNAVeco WHERE Nom=:c",{"c":EnvironnementNom})
        data = cur.fetchall()
        # if (len(data)==0):
        #
        # else:
        #     print("Name already used")
        Current_color = hex_to_rgb('4d367e')

        if (text_item.bg_color[0]==Current_color[0]/255):
            text_item.bg_color="#121212"
            cur.execute("UPDATE EnvironnementNAVeco SET Choisi = 0 WHERE Nom=:c",{"c":EnvironnementNom})
            con.commit()
            con.close()
        else:
            text_item.bg_color="#4d367e"
            cur.execute("UPDATE EnvironnementNAVeco SET Choisi = 1 WHERE Nom=:c",{"c":EnvironnementNom})
            con.commit()
            con.close()



    def SQL_Vehicule_delete(self):
        try:
            con = sqlite3.connect("NAVecoAPP.db")
            cur = con.cursor()
            cur.execute("SELECT * FROM VehiculeNAVeco")
            data = cur.fetchall()
            cur.execute("DELETE FROM VehiculeNAVeco WHERE Nom=:c",{"c":data[-1][0]})
            con.commit()
            con.close()
            Snackbar(
                text="Vehicule deleted!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
            self.SQL_Vehicule_refresh()
        except:
            print('Database not loaded')

    def SQL_Environnement_delete(self):
        try:
            con = sqlite3.connect("NAVecoAPP.db")
            cur = con.cursor()
            cur.execute("SELECT * FROM EnvironnementNAVeco")
            data = cur.fetchall()
            cur.execute("DELETE FROM EnvironnementNAVeco WHERE Nom=:c",{"c":data[-1][0]})
            con.commit()
            con.close()
            Snackbar(
                text="Environnement deleted!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
            self.SQL_Environnement_refresh()
        except:
            print('Database not loaded')

    def SearchFrom(self, instance, text):
        self.FromPlaceSelected = False
        self.LastPlaceSelected = 'From'
        print(text)
        Place=text
        if (text==''):
            self.root.ids.PlaceSelection.text = "Écrivez-vous un endroit, svp"
        else:
            response = clientGM.places_autocomplete(Place)
            try:
                pprint(response[0]['description'])
                len(response[0]['description'])
                if (len(response[0]['description'])>39):
                    self.root.ids.PlaceSelection.text = response[0]['description'][0:40]
                else:
                    self.root.ids.PlaceSelection.text = response[0]['description']
            except:
                self.root.ids.PlaceSelection.text = "Not found"
        print(self.FromPlaceSelected)


    def SearchTo(self, instance, text):
        self.ToPlaceSelected = False
        self.LastPlaceSelected = 'To'
        print(text)
        Place=text
        if (text==''):
            self.root.ids.PlaceSelection.text = "Écrivez-vous un endroit, svp"
        else:
            response = clientGM.places_autocomplete(Place)
            try:
                pprint(response[0]['description'])
                len(response[0]['description'])
                if (len(response[0]['description'])>39):
                    self.root.ids.PlaceSelection.text = response[0]['description'][0:40]
                else:
                    self.root.ids.PlaceSelection.text = response[0]['description']
            except:
                self.root.ids.PlaceSelection.text = "Not found"

    def PlaceSelectinoFunct(self):
        if (self.ToPlaceSelected==False and self.LastPlaceSelected == 'To'):
            self.root.ids.ToTextInput.text = self.root.ids.PlaceSelection.text
            self.root.ids.PlaceSelection.text = "Not found"
            self.ToPlaceSelected=True
        elif (self.FromPlaceSelected==False and self.LastPlaceSelected == 'From'):
            self.root.ids.FromTextInput.text = self.root.ids.PlaceSelection.text
            self.root.ids.PlaceSelection.text = "Not found"
            self.FromPlaceSelected=True
            print(self.FromPlaceSelected)
        elif (self.LastPlaceSelected == ''):
            print("Data not written")
            Snackbar(
                text="Data not written!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
        else:
            Snackbar(
                text="Places selected!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
            print("Data already complete")

    def show_time_picker_dep(self, *args):
        ClockTime_dep = MDTimePicker()
        ClockTime_dep.bind(on_cancel=self.on_cancel_dep, time=self.get_time_dep)
        ClockTime_dep.open()

    def get_time_dep(self, instance, time):
        # TimeArrive TimeDeparture
        self.root.ids.TimeDeparture.text = "Dep: "+str(time)
        print(time)
        return time

    def on_cancel_dep(self, instance, time):
        self.root.ids.TimeDeparture.text = "Temps de depart"
        print(time)
        print('Calcel')

    def show_time_picker_arr(self, *args):
        ClockTime_arr = MDTimePicker()
        ClockTime_arr.bind(on_cancel=self.on_cancel_arr, time=self.get_time_arr)
        ClockTime_arr.open()

    def get_time_arr(self, instance, time):
        # TimeArrive TimeDeparture
        self.root.ids.TimeArrive.text = "Arr: "+str(time)
        print(time)
        return time

    def on_cancel_arr(self, instance, time):
        self.root.ids.TimeArrive.text = "Temps d'arrivée"
        print(time)
        print('Calcel')

    def GetItinerary(self, *args):
        if (self.root.ids.VehiculeSelected.text=="Vehicule"):
            print("Vehicle not selected")
            Snackbar(
                text="Select at least one vehicle!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
        elif (self.root.ids.EnvironnementSelected.text=="Environnement"):
            print("Environement not selected")
            Snackbar(
                text="Select at least one environment!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
        elif (self.FromPlaceSelected==False):

            print("Place not selected")
            Snackbar(
                text="Select an initial place!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
        elif (self.ToPlaceSelected==False):
            print("Place not selected")
            Snackbar(
                text="Select a destination!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()
        # elif (self.root.ids.ChargeSuppl.text==""):
        #     print("Charge not selected")
        #     Snackbar(
        #         text="Select your load!",
        #         snackbar_x="10dp",
        #         snackbar_y="10dp",
        #         size_hint_x=(
        #             Window.width - (dp(10) * 2)
        #         ) / Window.width
        #     ).open()
        # elif (self.root.ids.TimeDeparture.text == "Temps de depart"):
        #     print("Departure time not selected")
        #     Snackbar(
        #         text="Select an initial time!",
        #         snackbar_x="10dp",
        #         snackbar_y="10dp",
        #         size_hint_x=(
        #             Window.width - (dp(10) * 2)
        #         ) / Window.width
        #     ).open()
        # elif (self.root.ids.TimeArrive.text == "Temps d'arrivée"):
        #     print("Arrival time not selected")
        #     Snackbar(
        #         text="Select a limit time!",
        #         snackbar_x="10dp",
        #         snackbar_y="10dp",
        #         size_hint_x=(
        #             Window.width - (dp(10) * 2)
        #         ) / Window.width
        #     ).open()
        # elif (self.root.ids.TimeTolerance.text == ""):
        #     print("Tolerance time not selected")
        #     Snackbar(
        #         text="Select your time tolerance!",
        #         snackbar_x="10dp",
        #         snackbar_y="10dp",
        #         size_hint_x=(
        #             Window.width - (dp(10) * 2)
        #         ) / Window.width
        #     ).open()
        else:

            print("READY")
            Snackbar(
                text="Let's go!",
                snackbar_x="10dp",
                snackbar_y="10dp",
                size_hint_x=(
                    Window.width - (dp(10) * 2)
                ) / Window.width
            ).open()


            ##-Récupération du point d'arrive et depart

            Place=self.root.ids.FromTextInput.text
            departure_adress = clientGM.places_autocomplete(Place)
            departure = clientGM.geocode(departure_adress[0]['description'])[0]
            self.departure_name = departure['formatted_address']
            self.departure_long = departure['geometry']['location']['lng']
            self.departure_lat = departure['geometry']['location']['lat']

            Place=self.root.ids.ToTextInput.text
            arrival_adress = clientGM.places_autocomplete(Place)
            arrival = clientGM.geocode(arrival_adress[0]['description'])[0]
            self.arrival_name = arrival['formatted_address']
            self.arrival_long = arrival['geometry']['location']['lng']
            self.arrival_lat = arrival['geometry']['location']['lat']


            if DevelopperMode:
                print("Departure:")
                print(self.departure_name)
                print("lat: "+str(self.departure_lat)+" | lng: "+str(self.departure_long)+"\n")

                print("Arrival:")
                print(self.arrival_name)
                print("lat: "+str(self.arrival_lat)+" | lng: "+str(self.arrival_long)+"\n")



            t1 = threading.Thread(target=self.ObtainDataORS)
            t1.start()
            self.dialog_Waitting.title = "Getting itinerary"
            self.dialog_Waitting.content_cls.ids.WaitingTextID.text= "Connecting to ORS server..."
            # self.dialog_Waitting.content_cls.ids.WaitingTextID.text= "Connecting to GoogleMap server..."
            self.dialog_Waitting.open()
            print("Starting Data recovering...")
            # self.ObtainDataGM()
            # self.ObtainDataORS()

            # wait until thread 1 is completely executed
            # t1.join()

    @mainthread
    def EndingDataReceptionFunct(self):

        self.dialog_Waitting.dismiss()

        self.NormalRouteInfo = [self.distance, self.duration]


        ## Test Folium

        # import folium
        # import statistics
        # import webbrowser
        #
        # points = []
        # LatList = []
        # LonList = []
        # for i in range(len(geometry)):
        #     LatList.append(geometry[i][1])
        #     LonList.append(geometry[i][0])
        #     points.append(tuple([geometry[i][1], geometry[i][0]]))
        # map = folium.Map(location=[statistics.mean(LatList), statistics.mean(LonList)], default_zoom_start=15)
        # folium.PolyLine(
        #     points, color="red",
        #     weight=2.5,
        #     opacity=1
        #     ).add_to(map)
        # map.save('mymap.html')
        # output_file = "mymap.html"
        # webbrowser.open(output_file, new=2)  # open in new tab

        ## Clock Function

        #Clock.schedule_interval(self.DrawItinerary,1/10)

        ## Adapt/Add widgets

        self.MapZoom = 13 # 10 Ville, 15 Rue, 19/20 Batiment, 1 Monde

        self.root.ids.map.lat = statistics.mean(self.LatList)
        self.root.ids.map.lon = statistics.mean(self.LonList)

        self.root.ids.MainScreen.add_widget(self.CardsLayout)

        self.CardsLayout.ids.NormalRouteInfo.text = "[b]Normal[/b]\n"+"[size=12]Time: "+str(int(self.NormalRouteInfo[1]/3600))+"h "+str(int(self.NormalRouteInfo[1]/60))+"m\n"+"Dist: "+str(int(self.NormalRouteInfo[0]/1000))+"."+str(int(self.NormalRouteInfo[0]/1000%1*10))+"km\n"+"Ener: 112.5Kwh[/size]"
        self.CardsLayout.ids.EcoRouteInfo.text = "[b]ECO[/b]\n"+"[size=12]Time: "+str(int(self.NormalRouteInfo[1]/3600))+"h "+str(int(self.NormalRouteInfo[1]/60))+"m\n"+"Dist: "+str(int(self.NormalRouteInfo[0]/1000))+"."+str(int(self.NormalRouteInfo[0]/1000%1*10))+"km\n"+"Ener: 112.5Kwh[/size]"
        self.CardsLayout.ids.FastRouteInfo.text = "[b]Fast[/b]\n"+"[size=12]Time: "+str(int(self.NormalRouteInfo[1]/3600))+"h "+str(int(self.NormalRouteInfo[1]/60))+"m\n"+"Dist: "+str(int(self.NormalRouteInfo[0]/1000))+"."+str(int(self.NormalRouteInfo[0]/1000%1*10))+"km\n"+"Ener: 112.5Kwh[/size]"

        self.PinStart = MapMarkerPopup(lat=self.Coordenates[0][0],lon= self.Coordenates[0][1], source='./img/PinStart.png')
        self.PinEnd = MapMarkerPopup(lat=self.Coordenates[-1][0],lon= self.Coordenates[-1][1], source='./img/PinEnd.png')
        self.root.ids.map.add_widget(self.PinStart)
        self.root.ids.map.add_widget(self.PinEnd)

        print("Data recovery compiled!")

        self.DrawItinerary()
        self.root.ids.screen_manager.current = "Main"



    def WaittingRouteFunct(self):
        for i in range(5):
            # time.sleep(1)
            print(i)
        print('Bye Bye')
        # self.dialog_Waitting.dismiss()


    def DrawItinerary(self, *args):
        try:

            # self.root.ids.MainScreen.remove_widget(self.root.ids.AppBarmap)
            # self.root.ids.map.get_latlon_at(0,600)
            # self.CoordenatesDownSample = [[48.81200799070672, 2.2843000449218778], #0 0
            #             [48.825571491753166, 2.2843000449218778], # 0 600
            #             [48.81652956551922, 2.2945997275390653]] # 200 300

            points = []

            self.root.ids.map.zoom = self.MapZoom # 10 Ville, 15 Rue, 19/20 Batiment, 1 Monde

            MarketItitPopup = MapMarkerPopup(lat=float(self.CoordenatesDownSample[0][0]),lon= float(self.CoordenatesDownSample[0][1]), )
            self.root.ids.map.add_widget(MarketItitPopup)
            MarketEndPopup = MapMarkerPopup(lat=float(self.CoordenatesDownSample[-1][0]),lon= float(self.CoordenatesDownSample[-1][1]))
            self.root.ids.map.add_widget(MarketEndPopup)

            for i in range(len(self.CoordenatesDownSample)):
                Marketn = MapMarker(lat=float(self.CoordenatesDownSample[i][0]),lon= float(self.CoordenatesDownSample[i][1]))
                self.root.ids.map.add_marker(Marketn)
                if((Marketn.x<self.root.ids.MainScreen.size[0] and Marketn.x>0) and (Marketn.y<self.root.ids.MainScreen.size[1]*0.85  and Marketn.y>0)):
                    points.append([Marketn.center_x, Marketn.y])

            lines = Line()
            lines.points = points
            lines.width = 2
            if self.root.ids.map.grp is not None:
                # just update the group with updated lines lines
                self.root.ids.map.grp.clear()
                self.root.ids.map.grp.add(lines)
            else:
                with self.root.ids.map.canvas.after:
                    #  create the group and add the lines
                    # Color(1,0,0,1)  # line color red
                    Color(0,0,1,1)  # line color blue
                    # Color(0,1,0,1)  # line color green
                    self.root.ids.map.grp = InstructionGroup()
                    self.root.ids.map.grp.add(lines)
            # self.root.ids.speed_dial.close_stack # NO FUNCION EL CIERRE AUTOMATICO


        except:
            print('Cordenates not included')

    def ResetRoutInfo(self, *args):
        print('cancel evert')

        self.CoordenatesDownSample = []

        try:
            self.root.ids.map.remove_widget(self.PinStart)
            self.root.ids.map.remove_widget(self.PinEnd)
        except:
            print('Pins not in')

        try:
            self.root.ids.MainScreen.remove_widget(self.CardsLayout)
        except:
            print('CardsLayout not in')

        try:
            self.root.ids.MainScreen.remove_widget(self.ButtonNavigationLayout)
        except:
            print('ButtonNavigationLayout not in')

        try:
            self.root.ids.map.grp.clear()
        except:
            print('Not itinerary designed')

        try:
            self.root.ids.map.grp1.clear()
        except:
            print('Not Navigation rectangle designed')

        self.MapZoom = 15

        Place='18 Avenue Jacques Jezequel, Vanves'
        response = clientGM.geocode(Place)
        self.LatUsr = response[0]['geometry']['location']['lat'] #48.8187902
        self.LngUsr = response[0]['geometry']['location']['lng'] # 2.2911665

        self.root.ids.map.lat = self.LatUsr
        self.root.ids.map.lon = self.LngUsr

        Snackbar(
            text="Trip canceled!",
            snackbar_x="10dp",
            snackbar_y="10dp",
            size_hint_x=(
                Window.width - (dp(10) * 2)
            ) / Window.width
        ).open()

        self.DrawItinerary()
        self.root.ids.speed_dial.close_stack

    def SelectedRoutInfo(self, *args):

        print('Trip Selected!')

        self.dialog_Waitting.title = "Optimizing speed reference"
        self.dialog_Waitting.content_cls.ids.WaitingTextID.text= "Running genetic algorithm..."
        self.dialog_Waitting.open()

        t1 = threading.Thread(target=self.AlgorithGenetiqueNAVeco)
        t1.start()

    def DataloggerPageGo(self):

        self.root.ids.screen_manager.current = "DataLoggerPage"

    def AlgorithGenetiqueNAVeco(self):

        print("Starting Algorithm Genetique...")
        comienzo = time.time()

        ###############################################

        # Données :
        Population_size = 150
        limit_generation  = 150
        Selection_probability = 0.5
        Mutation_probability = 0.2

        acceleration_max = 2.5 # en m/s²

        # Criteres d'arret
        gain = 0.01 # en kWh
        limit_identical_best = 10

        # pour les resultats finaux. Pour chaque trajet (Vmax, Pente)
        DataRoute = []
        DataFinal = [] # pour ecrire les resultats dans un fichier csv

        plot_best_solution = True

        #==============================================================================

        ##Données :

        self.DataFinal = []

        for i in range(len(self.LatList)-1):
            self.DataFinal.append([i,self.LatList[i],self.LonList[i],self.DistCum[i],self.MaxSpeed[i],self.Pente[i],self.elev_list[i],self.duration])

        self.DataFinal.insert(0,['Num','Lat','Lng','Dist (m)','MaxSpeed (m/s)','Slope (rad)','Altitude (m)','Duree (s)'])

        data = self.DataFinal

        comienzo = time.time()
        #Trajet réel
        data = data[1:]
        #[['Num', 'Lat', 'Lng', 'Dist (m)', 'MaxSpeed (m/s)', 'Slope (rad)', 'Altitude (m)', 'Duree (s)']]
        DistSpeed = []
        DistSlope = []
        for point in data:
            DistSpeed.append( [ float(point[3]) , float(point[4]) ] )
            DistSlope.append( [ float(point[3]) , float(point[5]) ] )


        #==============================================================================

        cut , spd , dist_segment_speed = speed_and_dist_cut(DistSpeed)
        print("-----------------------------------------------------------")

        vect_accel, vect_speed = split_speed_and_acceleration(-acceleration_max , acceleration_max , spd)

        print("-----------------------------------------------------------")

        #====================== 1) Chromosome a duree min ===============================================

        self.UpGradeWattingTextFunct("Creating chrommosome min")
        print("Chromosome a duree min...")

        # pour avoir la durée min possible
        chromosome_duraion_min = []

        chromosome_duraion_min.append( acceleration_max )
        chromosome_duraion_min.append( spd[0] )

        for i in range( 1, len(spd) ):

            if(spd[i] > spd[i-1]):
                chromosome_duraion_min.append(acceleration_max)
            elif( spd[i] < spd[i-1] ):
                chromosome_duraion_min.append(-acceleration_max)
            else:
                chromosome_duraion_min.append( 0 )

            chromosome_duraion_min.append( spd[i] )


        chromosome_duraion_min.append(-acceleration_max)
        chromosome_duraion_min.append( 0 )
        #------------------------------------------------------------------------------------------
        duration_raw_per_phase, duration_per_phase, distance_per_phase, distance_raw_per_phase = calculate_durations(chromosome_duraion_min, dist_segment_speed, cut, spd)

        cumulative_raw_distance, energy_consumed_metre, times_metre, vts_metre,tps   = evaluate(chromosome_duraion_min ,duration_raw_per_phase, distance_raw_per_phase, DistSlope )
        duration_min = times_metre[-1]

        vts_metre_max   = vts_metre
        times_metre_max = times_metre
        energy_consumed_metre_max = energy_consumed_metre

        crom_min_lst = [ chromosome_duraion_min,  sum(energy_consumed_metre), times_metre[-1]]


        #====================== 2) Chromosome a duree max ===============================================
        self.UpGradeWattingTextFunct("Creating chrommosome max")
        print("Chromosome a duree max...")

        # pour avoir la durée max

        chromosome_duraion_max = []

        min_spd = []
        for s in spd :

            # si au dessous de 30 kmh ==> vts min = 20
            if s <= 8.33 and s >= 7: # >= 5.55
                min_spd.append(5.55)
            # si au dessous de 50 kmh ==> vts min = 30
            elif s <= 13.88 and s >= 10: # >= 8.33
                min_spd.append(8.33)
            # si au dessous de 90 kmh ==> vts min = 50
            elif  s <= 25 and s >= 15: # >= 13.88
                min_spd.append(13.88)
            # si > 90 kmh ==> vts min = 80
            elif s >= 25:
                min_spd.append(22.22)
            # si les limitations de vitesse sont "trop petite"
            else:
                min_spd.append( s*0.75 )
                #min_spd.append( min(spd) )



        chromosome_duraion_max.append( (acceleration_max + 0)/2  )
        chromosome_duraion_max.append( min_spd[0] )

        for i in range(0, len(min_spd)-1):

            if min_spd[i] < min_spd[i+1] :
                chromosome_duraion_max.append( (acceleration_max + 0)/2  )
                chromosome_duraion_max.append( min_spd[i+1] )

            elif min_spd[i] > min_spd[i+1] :
                chromosome_duraion_max.append( -(acceleration_max + 0)/2  )
                chromosome_duraion_max.append( min_spd[i+1] )

            else :
                chromosome_duraion_max.append( 0  )
                chromosome_duraion_max.append( min_spd[i+1] )

        chromosome_duraion_max.append( -(acceleration_max + 0)/2  )
        chromosome_duraion_max.append( 0 )

        duration_raw_per_phase, duration_per_phase, distance_per_phase, distance_raw_per_phase = calculate_durations(chromosome_duraion_max, dist_segment_speed, cut, spd)

        cumulative_raw_distance, energy_consumed_metre, times_metre, vts_metre,tps   = evaluate(chromosome_duraion_max ,duration_raw_per_phase, distance_raw_per_phase, DistSlope )

        vts_metre_min   = vts_metre
        times_metre_min = times_metre
        energy_consumed_metre_min = energy_consumed_metre

        duration_max = times_metre[-1]
        crom_max_lst = [ chromosome_duraion_max,  sum(energy_consumed_metre), times_metre[-1]]

        #=================================== Launch Algo


        #start = time.time()

        a = b = c = []

        #================== Titre pour les plots des best solution ============================

        plot_title = "meilleure solution trouvée"

        #======================================


        start_final = time.time()
        stabilisation_time = 0

        #============================= 3) Generer une population initiale ========================
        self.UpGradeWattingTextFunct("Creating initial population")
        start = time.time()
        print("Generer une population initiale...")

        execution_time = [0]

        Population = []
        Nbre_iteration = 2

        Population.append( crom_max_lst )
        Population.append( crom_min_lst )

        # pour les exporter toutes les populations et voir leur evolution
        data_by_population = []
        data_by_generation = []

        counter_Kivy = 0

        while ( Nbre_iteration < Population_size ):

            # print(counter_Kivy)
            counter_Kivy = counter_Kivy+1

            acceptable_chromosome = False
            acceptable_duration = False
            #acceptable_energie = False
            # or acceptable_energie != True (dans le while juste au dessous)
            while(acceptable_chromosome != True or acceptable_duration != True ):
                start_final = time.time()
                # generer un chromosome et verifier s'il est acceptable
                acceptable_chromosome, chromosome_1 = generate_chromosome(vect_accel, vect_speed)
                a.append(time.time() - start_final)
                if acceptable_chromosome == False :
                    break

                # calculer les differentes durees allouees
                duration_raw_per_phase, duration_per_phase, distance_per_phase, distance_raw_per_phase = calculate_durations(chromosome_1, dist_segment_speed, cut, spd)
                b.append(time.time() - start_final - a[-1])
                # verifier qu'il n y a pas de duree negative (ca peut etre le cas juste qd la dist est trop petite)
                acceptable_duration = True
                s = 0
                for i in range(0, len(duration_raw_per_phase)):
                    if duration_raw_per_phase[i] < 0 :
                        acceptable_duration = False
                        break
                    else:
                        s += duration_raw_per_phase[i]
                if acceptable_duration == False:
                    break

                # verifier si la duree totale du chromosome (duree du trajet) est entre duree_min et duree_max
                if(s < duration_min or s > duration_max):
                    acceptable_duration = False
                    break
                cumulative_raw_distance, energy_consumed_metre, times_metre, vts_metre, tps   = evaluate(chromosome_1 ,duration_raw_per_phase, distance_raw_per_phase, DistSlope )
                Population.append( [chromosome_1 , sum(energy_consumed_metre), times_metre[-1] ] )
                Nbre_iteration += 1
                c.append(time.time() - start_final - a[-1] - b[-1])
        # afficher les temps de parcours et les energies consommees des chromosomes generees
        # for crm in Population:
            #print(f'Ec = {crm.Fitness} ---- Tps = {crm.times_metre[-1]}')
            # print(f'Ec = {crm[1]} ---- Tps = {crm[2]}')

        time_to_generate_population = time.time() - start
        # print(f'creating population in {time_to_generate_population } (s)')
        # print("")
        # print(f'str(a) =  {sum(a)} (s)')
        # print(f'str(b) =  {sum(b)} (s)')
        # print(f'str(c) =  {sum(c)} (s)')

        # pour avoir le meilleur de la population de depart et de le mttre dans le csv (en bas)
        Population.sort( key=lambda x: x[1] , reverse = False )

        #============================= 4)Tri et  Selection =============================

        population_selected_Wheel = []
        population_selected_Wheel = Population.copy()

        #=========================================================================


        start1 = time.time()
        execution_time = []
        #============================= 4) L'algorithme ===============================================

        increment_identical_best = 0
        increment_generation = 0
        # Trier les chromosomes dans le sens croissant de l'energie consommee (ie: le premier est le 'best')
        #population_selected_Wheel.sort( key=attrgetter('Fitness') , reverse = False )
        population_selected_Wheel.sort( key=lambda x: x[1] , reverse = False )
        # initialiser les meilleurs solutions connues et de generation
        best_known_chromosome = population_selected_Wheel[0]
        best_chromosome_of_generation = population_selected_Wheel[0]

        new_generation = []

        execution_crossover = []
        execution_creation_chrom = []
        execution_sort = []
        execution_boucle_for_class = []
        execution_generation = []
        execution_creation_chrom1 = []
        execution_fonctions = []
        data_by_step = []
        data_by_generation = []
        indices_cross_list = []
        len_indices = []
        Crossover_ameliorate = [0,0,0] # un tableau pour competer le nbre de fois que chaque croisment 1,2 ou 3 a AMLIORE la solution


        #=======================================================================================================
                                            # DEBUT #
        #=======================================================================================================

        print("DEBOUT Algorithme Genetique...")

        self.UpGradeWattingTextFunct("Generation: 0/"+str(limit_generation))

        counter_Kivy = 0

        while(increment_identical_best < limit_identical_best and increment_generation < limit_generation):

            # print(counter_Kivy)
            counter_Kivy = counter_Kivy+1

            #le debut de time pour la construction d'une generation
            start_time_generation = time.time()
            Crossover_used_nbre = [0,0,0]

            # On crée une nouvelle génération
            # for i in range(0, len(population_selected_Wheel)-1 ) :
            #     for j in range(i+1 , len(population_selected_Wheel) ):

            while len(new_generation) != len(Population):

                # print(counter_Kivy)

                # On prend 2 crom aleatoirement (differents) pour les croiser, et verifier
                # qu'ils n'ont pas été deja croisés
                rand_crom_1 = rdm.randint(0, len(Population)-1)
                rand_crom_2 = rdm.randint(0, len(Population)-1)
                while rand_crom_2 == rand_crom_1 or [rand_crom_1, rand_crom_2] in indices_cross_list or [rand_crom_2, rand_crom_1] in indices_cross_list:
                    rand_crom_1 = rdm.randint(0, len(Population)-1)
                    rand_crom_2 = rdm.randint(0, len(Population)-1)


                # on garde les indices des cromosomes croisés pour ne pas les re-croiser
                indices_cross_list.append( [rand_crom_1, rand_crom_2] )


                #rien.append([len(population_selected_Wheel),i,j])
                #==============================================================
                start = time.time()
                #==============================================================

                # générer un nouveau chromosome en croisant 2 parents selectionnes
                rand_crois = rdm.randint(1, 3)
                #rand_crois = 3
                start_cross = time.time()
                if( rand_crois == 1 ):
                    chromosome_child = crossover_speed_mean(population_selected_Wheel[rand_crom_1][0],
                                                                population_selected_Wheel[rand_crom_2][0])
                elif(rand_crois == 2 ) :
                    chromosome_child = crossover_speed_and_acceleration_mean(population_selected_Wheel[rand_crom_1][0],
                                                            population_selected_Wheel[rand_crom_2][0])
                else:
                    chromosome_child, use_cross_3 = crossover_exchange_one_point(population_selected_Wheel[rand_crom_1][0],
                                                            population_selected_Wheel[rand_crom_2][0])

                #==============================================================
                end_cross  = time.time()
                execution_crossover.append(end_cross - start_cross)
                #==============================================================

                mutation_bool = False
                # Mutation probable du fil
                if rdm.random() <= Mutation_probability:
                    chromosome_child = mutation_chromosome(chromosome_child)
                    mutation_bool = True

                start_fonctions  = time.time()
                # calcul des caractéristiques du fils (et notamment l'Energie)
                duration_raw_per_phase, duration_per_phase, distance_per_phase, distance_raw_per_phase = calculate_durations(chromosome_child, dist_segment_speed, cut, spd)

                # verifier s'il n ya pas de durée négative
                acceptable_duration  = True
                for k in range(0, len(duration_raw_per_phase)):
                    if duration_raw_per_phase[k] < 0 :
                        acceptable_duration = False
                        break
                # if acceptable_duration == False :
                #     break

                cumulative_raw_distance, energy_consumed_metre, times_metre, vts_metre,tps = evaluate(chromosome_child ,duration_raw_per_phase, distance_raw_per_phase, DistSlope )

                #==============================================================
                end_fonctions  = time.time()
                execution_fonctions.append(end_fonctions - start_fonctions)
                #==============================================================

                acceptable_time = True
                if times_metre[-1] > duration_max or times_metre[-1]  < duration_min :
                    acceptable_time = False
                    #break

                start_creation = time.time()
                # On crée le nouveau chromosome
                end_creation  = time.time()
                execution_creation_chrom.append(end_creation - start_creation)

                # # verifier si l'energie n'est pas negative
                # if( crm_child.Fitness > 0 ):

                acceptable_child = True
                if( sum(energy_consumed_metre) == best_chromosome_of_generation[1] and times_metre[-1] == best_chromosome_of_generation[2]):
                    acceptable_child = False
                    #break
                # verifier s'il est le meilleur de sa generation
                elif( sum(energy_consumed_metre) < best_chromosome_of_generation[1] and acceptable_child == True and acceptable_duration == True and acceptable_time == True):
                    start_creation1 = time.time()

                    best_chromosome_of_generation = [chromosome_child, sum(energy_consumed_metre), times_metre[-1]]
                    end_creation1  = time.time()
                    execution_creation_chrom1.append(end_creation1 - start_creation1)

                    # ajouter le crossover utilisé pour trouver ce chromosome et s'il a été muté
                    # ce 'if' cest pour garder le meilleur de la generation
                    if len(data_by_step) > 0:
                        data_by_step.clear()

                    #data_by_step.append(sum(energy_consumed_metre))
                    # Verifier que si c'est vraiment l'opérateur 3 qui ete utilise ou c'etait le 2
                    if rand_crois == 3:
                        if use_cross_3 == False:
                            rand_crois = 2

                    data_by_step.append(rand_crois)

                    data_by_step.append(mutation_bool)
                    data_by_step.append(rand_crom_1)
                    data_by_step.append(rand_crom_2)

                # l'injecter dans la nouvelle generation, s'il n'y est pas
                if( ([chromosome_child, sum(energy_consumed_metre), times_metre[-1]] not in new_generation) and acceptable_child == True and acceptable_duration == True and acceptable_time == True):

                    new_generation.append( [chromosome_child, sum(energy_consumed_metre), times_metre[-1]] )

                    # Enregistrer les opérateurs de croisement utilisés pour ajouter ce 'child' à la nouvelle génération
                    # Verifier que si c'est vraiment l'opérateur 3 qui ete utilise ou c'etait le 2
                    if rand_crois == 3:
                        if use_cross_3 == False:
                            rand_crois = 2

                    Crossover_used_nbre[rand_crois -1] += 1

                # print("  ")
                # print(f'acccccepte ON EST A --- {increment_generation} -- {len(new_generation)}')
                # print("  ")

                execution_time.append(time.time() -  start )

            len_indices.append(len(indices_cross_list))
            #vider la liste des indices croisés
            indices_cross_list.clear()

            start_boucle_for_class = time.time()
            # for a in new_generation:
                # print(a[0])
            end_boucle_for_class = time.time()
            execution_boucle_for_class.append(end_boucle_for_class - start_boucle_for_class)


            start_generation = time.time()
            # on met a jour la meilleur solution de connue

            #if( best_known_chromosome[1]/3600000  > best_chromosome_of_generation[1]/3600000  ):
            if( (best_known_chromosome[1]/3600000 - best_chromosome_of_generation[1]/3600000  >= gain) or
                (best_known_chromosome[1] == best_chromosome_of_generation[1] and best_known_chromosome[2] > best_chromosome_of_generation[2]) ):

                best_known_chromosome = best_chromosome_of_generation
                increment_identical_best = 0

                # on incremente la case du croisement utilisé pour avoir ce 'best_know'
                Crossover_ameliorate[ data_by_step[0]-1 ] += 1 # le rand_crois utilisé pour avoir ce best know

                # sauvegarder comment a t on obtenu ce best_know
                data_by_step.insert(0, best_chromosome_of_generation[1]/3600000) # energie du best generation
                data_by_step.insert(0, best_known_chromosome[1]/3600000) # energie consommee du best know
                data_by_step.insert(0, best_known_chromosome[2]) # tps de trajet
                data_by_step.insert(0, increment_generation+1) # num de generation
                data_by_step.append('Ameliorée') # Il ya amélioration de la solution globale (best know)
                stabilisation_time = time.time() - start_final
            else:
                increment_identical_best += 1

                # sauvegarder comment a t on obtenu ce best_know
                # verifier si cest le premier best_know, cad qu il na pas ete obtenu avec cross ou mut (best de depart)
                if len(data_by_step) == 0:
                    data_by_step.append(best_chromosome_of_generation[1]/3600000)
                    data_by_step.append('')
                    data_by_step.append('')
                    data_by_step.append('')
                    data_by_step.append('')

                    data_by_step.insert(0, best_known_chromosome[1]/3600000) # energie consommee
                    data_by_step.insert(0, best_known_chromosome[2]) # tps de trajet
                    data_by_step.insert(0, increment_generation+1) # num de generation
                    data_by_step.append('') # pas d'amélioration de la solution globale
                # best generation n'est meilleure que best know, mais il existe une best generation
                else :
                    # # on supprime ce qu'il ya car ce n'est pas meuilleure que best know, et donc ca ne sert
                    # # a rien de garder les informations concernant best generation
                    # data_by_step.clear()

                    data_by_step.insert(0, best_chromosome_of_generation[1]/3600000)

                    data_by_step.insert(0, best_known_chromosome[1]/3600000) # energie consommee
                    data_by_step.insert(0, best_known_chromosome[2]) # tps de trajet
                    data_by_step.insert(0, increment_generation+1) # num de generation
                    data_by_step.append('') # pas d'amélioration de la solution globale

            # limite de generation
            increment_generation += 1
            self.UpGradeWattingTextFunct("Generation: "+str(increment_generation)+"/"+str(limit_generation))


            # print(f'---------- increment_generation = {increment_generation} and increment_identical_best = {increment_identical_best} ----------------------------------------------------------------------------------------')

            # Trier notre generation dans l'odre decroissant de l'energie consommee
            #new_generation_tmp = new_generation.copy()
            new_generation.sort( key=lambda x: x[1] , reverse = True )

            # calculer la somme de toutes les energies consommees, pour former le determinateur
            sum_fitness = 0
            for crm in new_generation:
                sum_fitness += crm[1]

            # faire une copie de l'anciene generation pour completer la nouvelle selectionnee avec les meilleurs
            previous_generation = population_selected_Wheel.copy()
            population_selected_Wheel.clear()

            # Affecter une probabilite a chacun des chromosomes, en fct de leurs energies et les selectionner
            # selon la proba de selection donnée en entrée

            sum_iterate = 0
            for crm in new_generation:
                sum_iterate += crm[1]
                if sum_fitness == 0 :
                    population_selected_Wheel = new_generation.copy()
                    break
                elif( (sum_iterate/sum_fitness) >= Selection_probability ):
                    population_selected_Wheel.append(crm)

            # La taille de la population selectionnée (l'ajouter aux data finaux)
            if increment_generation-1 > 0 :
                data_by_step.append( round(100*len(population_selected_Wheel)/float(Population_size),2) )
            else:
                data_by_step.append(100)  # a la premiere itération toute la population est selectionee


            start_sort = time.time()
            # completer la nouvelle selectionnee avec des chromosomes de l'ancienne generation (choisis aleatoirement)
            # jusuqu'a atteindre la taille de la population initiale
            previous_generation.sort( key=lambda x: x[1] , reverse = False)

            #==============================================================
            end_sort  = time.time()
            execution_crossover.append(end_sort - start_sort)
            #==============================================================

            k = 0
            while len(population_selected_Wheel) < len(Population) and k < len(previous_generation):
                #population_selected_Wheel.append(previous_generation.pop( random.randint( 0, len(previous_generation)-1 ) ) )
                if previous_generation[k] not in population_selected_Wheel :
                    population_selected_Wheel.append(previous_generation[k])
                k += 1

            # si on trouve plus de chromosome de la generation precedente a rajouter, on en rajoute des random
            # while k == len(previous_generation) and len(population_selected_Wheel) < len(Population) :

            population_selected_Wheel.sort( key=lambda x: x[1] , reverse = False )

            # print(f'-------------------- taille de pop_wheel {len(population_selected_Wheel)} ---------')
            # on verifie que la nouvelle population selectionnee n'est pas reduite a 1 chrom ou rien
            # if( len(population_selected_Wheel) <= 1 ):
            #     break
            #==========================================================================================================

            # Ajouter le temps de consructtion d'une generation aux 'datas' de la generation
            end_time_generation = time.time()
            data_by_step.insert(2, end_time_generation - start_time_generation)

            # calcul de l'ecart-type de la generation et sa moyenne (en energie), et les ajouter aux donnees du csv
            standard_deviation_generation = statistics.pstdev([chld[1] for chld in new_generation ])
            mean_generation = statistics.mean([chld[1] for chld in new_generation ])
            data_by_step.append(standard_deviation_generation/3600000)
            data_by_step.append(mean_generation/3600000)

            # injecter ds les datas de chaque génération, le nbre de fois ou chaque croisment a creer un child 'realisable' pour la nvlle generation
            data_by_step.append(Crossover_used_nbre[0]) #
            data_by_step.append(Crossover_used_nbre[1])
            data_by_step.append(Crossover_used_nbre[2])


            # copier toutes les informations obtenues de cette génération, et l'injecter dans les datas finaux
            data_by_generation.append(data_by_step.copy())
            data_by_step.clear()


            #vider la liste new_generation et celle qui contient le nbre d'utilisation de chaque croisement
            new_generation.clear()
            Crossover_used_nbre.clear()

        ############################################## Final Algorithme Genetique

        end_final = time.time()

        print(end_final - start_final)
        end_generation  = time.time()

        final_completo = time.time()
        print(final_completo - comienzo)

        self.times_metre = times_metre
        self.vts_metre = vts_metre
        self.vts_metre_max = vts_metre_max

        self.EndingGeneticAlgorithmFunct()

        print("Algorithm Genetique Fini")


    def ObtainDataGM(self):

        ##-Récupération du trajet GoogleMaps

        now = datetime.now()
        directions_result = clientGM.directions(self.departure_name,
                                            self.arrival_name,
                                            mode="driving",
                                            traffic_model = 'optimistic',
                                            alternatives='True',
                                            departure_time=now)

        self.distance = directions_result[0]['legs'][0]['distance']['value']
        self.duration = directions_result[0]['legs'][0]['duration']['value']

        ## UpSample trajet GoogleMaps

        distance_sample = 1

        KeyPoints = len(directions_result[0]['legs'][0]['steps'])
        KeySegments = 1
        KeyPointsTemp = 0
        KeySegmentsTemp = 0
        TotalDist = 0
        j = 0

        self.CoordenatesDownSample = []
        points = []
        for steps in range(len(directions_result[0]['legs'][0]['steps'])):
            segment = polyline.decode(directions_result[0]['legs'][0]['steps'][steps]['polyline']['points'])
            for coordenate in range(len(segment)):
                self.CoordenatesDownSample.append(segment[coordenate])
                points.append([segment[coordenate]])

        self.LatList = []
        self.LonList = []

        for i in range(len(self.CoordenatesDownSample)):
            if i == len(self.CoordenatesDownSample)-1:
                n = 0
            else:
                DistTemp = getDistance(self.CoordenatesDownSample[i][0],self.CoordenatesDownSample[i][1],self.CoordenatesDownSample[i+1][0],self.CoordenatesDownSample[i+1][1])
                n = ceil(DistTemp/distance_sample)
            self.LatList.append(self.CoordenatesDownSample[i][0])
            self.LonList.append(self.CoordenatesDownSample[i][1])
            if n>1:
                for j in range(1,n):
                    self.LatList.append(self.CoordenatesDownSample[i][0]+(self.CoordenatesDownSample[i+1][0]-self.CoordenatesDownSample[i][0])/n*j)
                    self.LonList.append(self.CoordenatesDownSample[i][1]+(self.CoordenatesDownSample[i+1][1]-self.CoordenatesDownSample[i][1])/n*j)

        self.Coordenates = []
        for i in range(len(self.LatList)):
            self.Coordenates.append([self.LatList[i],self.LonList[i]])

        ## API Google Map altitudes -------------------------------
        elevations = []
        for i in range(int(np.ceil(len(self.Coordenates)/500))):
            if((i+1)*500<=len(self.Coordenates)):
                elevations_result = clientGM.elevation(self.Coordenates[i*500:(i+1)*500])
            else:
                elevations_result = clientGM.elevation(self.Coordenates[i*500:])
            elevations += elevations_result

        self.elev_list = []
        ResolHist = []
        new_geometry_Final = []

        for i in range(len(elevations)):
            self.elev_list.append(elevations[i]['elevation'])
            ResolHist.append(elevations[i]['resolution'])
            new_geometry_Final.append([elevations[i]['location']['lat'],elevations[i]['location']['lng'],elevations[i]['elevation']])


        #Filtre d'elev Goggle Maps

        self.ElevFiltre = []
        for i in range(0,len(self.elev_list)):
            self.ElevFiltre.append(float(self.elev_list[i]))

        OrdreFiltre = 10
        ElevFiltre1 = []
        for i in range(0,len(self.ElevFiltre)):
            if len(self.ElevFiltre)>1:
                if i==0:
                    ElevFiltre1.append(self.ElevFiltre[0])
                elif i==len(self.ElevFiltre)-1:
                    ElevFiltre1.append(self.ElevFiltre[len(self.ElevFiltre)-1])
                elif i<=OrdreFiltre/2:
                    #ElevFiltre1.append(sum(self.ElevFiltre[:int(OrdreFiltre/2)])/len(self.ElevFiltre[:int(OrdreFiltre/2)]))
                    ElevFiltre1.append(sum(self.ElevFiltre[:i*2])/len(self.ElevFiltre[:i*2]))
                elif i>=(len(self.ElevFiltre)-(OrdreFiltre/2)):
                    #ElevFiltre1.append(sum(self.ElevFiltre[len(self.ElevFiltre)-int(OrdreFiltre/2):])/len(self.ElevFiltre[len(self.ElevFiltre)-int(OrdreFiltre/2):]))
                    ElevFiltre1.append(sum(self.ElevFiltre[2*i-len(self.ElevFiltre)+1:])/len(self.ElevFiltre[2*i-len(self.ElevFiltre)+1:]))
                else:
                    ElevFiltre1.append(sum(self.ElevFiltre[i-int(OrdreFiltre/2):i+int(OrdreFiltre/2)])/len(self.ElevFiltre[i-int(OrdreFiltre/2):i+int(OrdreFiltre/2)]))

        for i in range(0,len(self.elev_list)):
            new_geometry_Final[i][2]=ElevFiltre1[i]
            self.elev_list[i]=ElevFiltre1[i]

        ## Calcule de la Pente

        DistNodesV = []
        DiffaltV  = [0]
        self.Pente = [0]
        self.DistCum = [0]
        DistInit = 0
        VarTemp = 0

        for i in range(len(new_geometry_Final)-1):
            DistNodes=getDistance(new_geometry_Final[i][0],new_geometry_Final[i][1],new_geometry_Final[i+1][0],new_geometry_Final[i+1][1])
            DiffAlt = (new_geometry_Final[i+1][2]-new_geometry_Final[i][2])
            DistNodesV.append(DistNodes)
            self.DistCum.append(DistInit+DistNodes)
            DistInit=DistInit+DistNodes
            if (DistNodes==0):
                VarTemp = VarTemp
                DiffaltV.append(DiffAlt)
                self.Pente.append(asin(VarTemp)) #Radians
            elif (abs(DiffAlt/DistNodes))>0.5:
                VarTemp = VarTemp
                DiffaltV.append(DiffAlt)
                self.Pente.append(asin(VarTemp)) #Radians
            else:
                VarTemp = DiffAlt/DistNodes
                DiffaltV.append(DiffAlt)
                self.Pente.append(asin(VarTemp)) #Radians

        ##Vittesse GoogleMaps
        # https://giscience.github.io/openrouteservice/documentation/travel-speeds/Travel-Speeds.html

        self.MaxSpeed = []
        DistKeyPoints = directions_result[0]['legs'][0]['steps'][0]['distance']['value']
        KeyPoints = len(directions_result[0]['legs'][0]['steps'])
        KeySegments = 0
        KeyPointsTemp = 0
        KeySegmentsTemp = 0

        TotalDist = 0
        i = 0
        while 1 :
            DistTemp = directions_result[0]['legs'][0]['steps'][KeyPointsTemp]['distance']['value']
            DuraTemp = directions_result[0]['legs'][0]['steps'][KeyPointsTemp]['duration']['value']

            if(DuraTemp==0):
                KeyPointsTemp = KeyPointsTemp + 1
            else:
                MaxSpeedTemp = (DistTemp/DuraTemp)
                self.MaxSpeed.append(MaxSpeedTemp)
                # print(DistTemp)
                # print(DuraTemp)
                # print(DistTemp/DuraTemp)

                if(self.DistCum[i]>=DistKeyPoints+TotalDist):
                    TotalDist = TotalDist+DistKeyPoints
                    KeyPointsTemp = KeyPointsTemp + 1
                    DistKeyPoints = DistKeyPoints + directions_result[0]['legs'][0]['steps'][KeyPointsTemp]['distance']['value']
                i=i+1

            if (len(self.MaxSpeed)==len(self.LatList)) :
                break

        for i in range(0, len(self.MaxSpeed)):
            #===============================================================================
            # initialisation des vitesses min a avoir en fonction des limitations de vitesse
            if self.MaxSpeed[i] <= 5.55: # >= 5.55: # 30 kmh
                self.MaxSpeed[i] = 5.55
            elif self.MaxSpeed[i] <= 8.33 and self.MaxSpeed[i] > 5.55: # >= 8.33 # 50 kmh
                self.MaxSpeed[i] = 8.33
            elif self.MaxSpeed[i] <= 13.88 and self.MaxSpeed[i] > 8.33: # >= 13.88  # 90 kmh
                self.MaxSpeed[i] = 13.88
            elif self.MaxSpeed[i] > 13.88 :   # 110 ou 130 kmh --> Vmin = 80 kmh
                self.MaxSpeed[i] = self.MaxSpeed[i]

        self.EndingDataReceptionFunct()

    def ObtainDataORS(self):

        ## -Récupération du trajet OpenRouteService

        coordinates = [[self.departure_long, self.departure_lat], [self.arrival_long, self.arrival_lat]]

        route = clientORS.directions(
            coordinates=coordinates,
            profile='driving-car',
            format='geojson',
            elevation=True,
            validate=False,
        )

        self.distance = route['features'][0]['properties']['summary']['distance']
        self.duration = route['features'][0]['properties']['summary']['duration']

        ## UpSample trajet OpenRouteService

        distance_sample = 1

        KeyPoints = len(route['features'][0]['properties']['segments'][0]['steps'])
        KeySegments = len(route['features'][0]['properties']['segments'])
        KeyPointsTemp = 0
        KeySegmentsTemp = 0
        TotalDist = 0
        j = 0

        self.LatList = []
        self.LonList = []


        for i in range(len(route['features'][0]['geometry']['coordinates'])):
            if i == len(route['features'][0]['geometry']['coordinates'])-1:
                n = 0
            else:
                DistTemp = getDistance(route['features'][0]['geometry']['coordinates'][i][1],route['features'][0]['geometry']['coordinates'][i][0],route['features'][0]['geometry']['coordinates'][i+1][1],route['features'][0]['geometry']['coordinates'][i+1][0])
                n = ceil(DistTemp/distance_sample)
            self.LatList.append(route['features'][0]['geometry']['coordinates'][i][1])
            self.LonList.append(route['features'][0]['geometry']['coordinates'][i][0])
            if n>1:
                for j in range(1,n):
                    self.LatList.append(route['features'][0]['geometry']['coordinates'][i][1]+(route['features'][0]['geometry']['coordinates'][i+1][1]-route['features'][0]['geometry']['coordinates'][i][1])/n*j)
                    self.LonList.append(route['features'][0]['geometry']['coordinates'][i][0]+(route['features'][0]['geometry']['coordinates'][i+1][0]-route['features'][0]['geometry']['coordinates'][i][0])/n*j)

        self.Coordenates = []
        for i in range(len(self.LatList)):
            self.Coordenates.append([self.LatList[i],self.LonList[i]])

        self.CoordenatesLonLat = []
        for i in range(len(self.LatList)):
            self.CoordenatesLonLat.append([self.LonList[i],self.LatList[i]])

        self.CoordenatesDownSample = []
        points = []
        for i in range(len(route['features'][0]['geometry']['coordinates'])):
            self.CoordenatesDownSample.append([route['features'][0]['geometry']['coordinates'][i][1],route['features'][0]['geometry']['coordinates'][i][0]])
            points.append([route['features'][0]['geometry']['coordinates'][i][1],route['features'][0]['geometry']['coordinates'][i][0]])

        ## API OpenRouteService altitudes -------------------------------

        elevations = []
        for i in range(int(np.ceil(len(self.CoordenatesLonLat)/2000))):
            if((i+1)*2000<=len(self.CoordenatesLonLat)):
                elevations_result = clientORS.elevation_line(
                    format_in='polyline',  # other options: geojson, encodedpolyline
                    format_out='geojson',
                    geometry=self.CoordenatesLonLat[i*2000:(i+1)*2000],
                )
            else:
                elevations_result = clientORS.elevation_line(
                    format_in='polyline',  # other options: geojson, encodedpolyline
                    format_out='geojson',
                    geometry=self.CoordenatesLonLat[i*2000:],
                )
            elevations += elevations_result['geometry']['coordinates']

        self.elev_list = []
        new_geometry_Final = []

        for i in range(len(elevations)):
            self.elev_list.append(elevations[i][2])
            new_geometry_Final.append([elevations[i][1],elevations[i][0],elevations[i][2]])

        #Filtre d'elev OpenRouteService

        self.ElevFiltre = []
        for i in range(0,len(self.elev_list)):
            self.ElevFiltre.append(float(self.elev_list[i]))

        OrdreFiltre = 15
        ElevFiltre1 = []
        for i in range(0,len(self.ElevFiltre)):
            if len(self.ElevFiltre)>1:
                if i==0:
                    ElevFiltre1.append(self.ElevFiltre[0])
                elif i==len(self.ElevFiltre)-1:
                    ElevFiltre1.append(self.ElevFiltre[len(self.ElevFiltre)-1])
                elif i<=OrdreFiltre/2:
                    #ElevFiltre1.append(sum(self.ElevFiltre[:int(OrdreFiltre/2)])/len(self.ElevFiltre[:int(OrdreFiltre/2)]))
                    ElevFiltre1.append(sum(self.ElevFiltre[:i*2])/len(self.ElevFiltre[:i*2]))
                elif i>=(len(self.ElevFiltre)-(OrdreFiltre/2)):
                    #ElevFiltre1.append(sum(self.ElevFiltre[len(self.ElevFiltre)-int(OrdreFiltre/2):])/len(self.ElevFiltre[len(self.ElevFiltre)-int(OrdreFiltre/2):]))
                    ElevFiltre1.append(sum(self.ElevFiltre[2*i-len(self.ElevFiltre)+1:])/len(self.ElevFiltre[2*i-len(self.ElevFiltre)+1:]))
                else:
                    ElevFiltre1.append(sum(self.ElevFiltre[i-int(OrdreFiltre/2):i+int(OrdreFiltre/2)])/len(self.ElevFiltre[i-int(OrdreFiltre/2):i+int(OrdreFiltre/2)]))

        for i in range(0,len(self.elev_list)):
            new_geometry_Final[i][2]=ElevFiltre1[i]
            self.elev_list[i]=ElevFiltre1[i]

        ## Calcule de la Pente

        DistNodesV = []
        DiffaltV  = [0]
        self.Pente = [0]
        self.DistCum = [0]
        DistInit = 0
        VarTemp = 0

        for i in range(len(new_geometry_Final)-1):
            DistNodes=getDistance(new_geometry_Final[i][0],new_geometry_Final[i][1],new_geometry_Final[i+1][0],new_geometry_Final[i+1][1])
            DiffAlt = (new_geometry_Final[i+1][2]-new_geometry_Final[i][2])
            DistNodesV.append(DistNodes)
            self.DistCum.append(DistInit+DistNodes)
            DistInit=DistInit+DistNodes
            if (DistNodes==0):
                VarTemp = VarTemp
                DiffaltV.append(DiffAlt)
                self.Pente.append(asin(VarTemp)) #Radians
            elif (abs(DiffAlt/DistNodes))>0.5:
                VarTemp = VarTemp
                DiffaltV.append(DiffAlt)
                self.Pente.append(asin(VarTemp)) #Radians
            else:
                VarTemp = DiffAlt/DistNodes
                DiffaltV.append(DiffAlt)
                self.Pente.append(asin(VarTemp)) #Radians

        ##Vittesse OpenRoute Service
        # https://giscience.github.io/openrouteservice/documentation/travel-speeds/Travel-Speeds.html

        self.MaxSpeed = []
        DistKeyPoints = route['features'][0]['properties']['segments'][0]['steps'][0]['distance']
        KeyPoints = len(route['features'][0]['properties']['segments'][0]['steps'])
        KeySegments = len(route['features'][0]['properties']['segments'])
        KeyPointsTemp = 0
        KeySegmentsTemp = 0

        TotalDist = 0
        i = 0
        while 1 :
            DistTemp = route['features'][0]['properties']['segments'][KeySegmentsTemp]['steps'][KeyPointsTemp]['distance']
            DuraTemp = route['features'][0]['properties']['segments'][KeySegmentsTemp]['steps'][KeyPointsTemp]['duration']

            if(DuraTemp==0):
                KeyPointsTemp = KeyPointsTemp + 1
            else:
                MaxSpeedTemp = (DistTemp/DuraTemp)
                self.MaxSpeed.append(MaxSpeedTemp)
                # print(DistTemp)
                # print(DuraTemp)
                # print(DistTemp/DuraTemp)

                if(self.DistCum[i]>=DistKeyPoints+TotalDist):
                    TotalDist = TotalDist+DistKeyPoints
                    KeyPointsTemp = KeyPointsTemp + 1
                    DistKeyPoints = DistKeyPoints + route['features'][0]['properties']['segments'][KeySegmentsTemp]['steps'][KeyPointsTemp]['distance']
                i=i+1

            if(KeyPointsTemp==KeyPoints):
                KeyPointsTemp = 0
                KeySegmentsTemp = KeySegmentsTemp+1
                KeyPoints = len(route['features'][0]['properties']['segments'][KeySegmentsTemp]['steps'])

            if (len(self.MaxSpeed)==len(self.LatList)) :
                break

        # for i in range(0, len(self.MaxSpeed)):
        #     #===============================================================================
        #     # initialisation des vitesses min a avoir en fonction des limitations de vitesse
        #     if self.MaxSpeed[i] <= 5.55: # >= 5.55: # 30 kmh
        #         self.MaxSpeed[i] = 5.55
        #     elif self.MaxSpeed[i] <= 8.33 and self.MaxSpeed[i] > 5.55: # >= 8.33 # 50 kmh
        #         self.MaxSpeed[i] = 8.33
        #     elif self.MaxSpeed[i] <= 13.88 and self.MaxSpeed[i] > 8.33: # >= 13.88  # 90 kmh
        #         self.MaxSpeed[i] = 13.88
        #     elif self.MaxSpeed[i] > 13.88 :   # 110 ou 130 kmh --> Vmin = 80 kmh
        #         self.MaxSpeed[i] = self.MaxSpeed[i]

        self.EndingDataReceptionFunct()

    @mainthread
    def UpGradeWattingTextFunct(self, Externaltext):
        self.dialog_Waitting.content_cls.ids.WaitingTextID.text= Externaltext

    @mainthread
    def EndingGeneticAlgorithmFunct(self):

        self.dialog_Waitting.dismiss()

        ## Plots

        try:
            self.root.ids.GraphPieChartID.clear_widgets()
        except:
            print('GraphPieChartID not used')
        try:
            self.root.ids.GraphElevID.clear_widgets()
        except:
            print('GraphElevID not used')
        try:
            self.root.ids.GraphPenteID.clear_widgets()
        except:
            print('GraphPenteID not used')
        try:
            self.root.ids.GraphSpeedID.clear_widgets()
        except:
            print('GraphSpeedID not used')

        y = np.array([35, 65])
        mycolors = ["#4b347b", "#673bb7"]
        mylabels = ["35%", "65%"]
        fig = plt.figure(facecolor='#121212')
        ax1 = fig.add_subplot(131)
        ax1.set_title('Dist[m]', y=0.5, va="top", weight='bold', fontsize=10)
        ax1.pie(y, labels = mylabels, colors = mycolors)
        ax2 = fig.add_subplot(132)
        ax2.pie(y, labels = mylabels, colors = mycolors)
        ax2.set_title('En[KWh]', y=0.5, va="top", weight='bold', fontsize=10)
        ax3 = fig.add_subplot(133)
        ax3.pie(y, labels = mylabels, colors = mycolors)
        ax3.set_title('Time[min]', y=0.5, va="top", weight='bold', fontsize=10)
        # ax1.title.set_text('Distance')
        # ax2.title.set_text('Energy')
        self.root.ids.GraphPieChartID.add_widget(FigureCanvasKivyAgg(plt.gcf()))

        signal = np.array(self.elev_list)
        signal1 = np.array(self.ElevFiltre)
        plt.figure(facecolor='#121212')
        ax = plt.axes()
        ax.set_facecolor("#121212")
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        plt.plot(signal, color='#673bb7', linestyle='--')
        plt.ylim(min(self.elev_list)*0.9,max(self.elev_list)*1.1)
        # plt.plot(signal1, color='white', linestyle='--')
        ax.set_title('Altitude [m]', y=1.06, va="top", fontsize=10)
        # plt.xlabel('Nodes')
        # plt.ylabel('Altitude [m]')
        # plt.title("Altitude")
        plt.grid(True, color='white', linewidth = "0.4", linestyle = "--")
        self.root.ids.GraphElevID.add_widget(FigureCanvasKivyAgg(plt.gcf()))

        signal = np.array(self.Pente)
        plt.figure(facecolor='#121212')
        ax = plt.axes()
        ax.set_facecolor("#121212")
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.set_title('Pente [rad]', y=1.06, va="top", fontsize=10)
        plt.plot(signal, color='#673bb7', linestyle='--')
        plt.ylim(min(self.Pente)*0.9,max(self.Pente)*1.1)
        # plt.xlabel('Nodes')
        # plt.ylabel('Pente [rad]')
        # plt.title("Pente")
        plt.grid(True, color='white', linewidth = "0.4", linestyle = "--")
        self.root.ids.GraphPenteID.add_widget(FigureCanvasKivyAgg(plt.gcf()))

        SpeedTimeSignal    = self.times_metre
        OptimalSpeedSignal = self.vts_metre
        MaximalSpeedSignal = self.vts_metre_max
        plt.figure(facecolor='#121212')
        ax = plt.axes()
        ax.set_facecolor("#121212")
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.set_title('Vitesse [m/s]', y=1.06, va="top", fontsize=10)
        plt.plot(SpeedTimeSignal, OptimalSpeedSignal, color='#673bb7', linestyle='-')
        plt.plot(SpeedTimeSignal, MaximalSpeedSignal, color='#c23328', linestyle='--')
        plt.ylim(min(MaximalSpeedSignal)*0.5,max(MaximalSpeedSignal)*1.1)
        # plt.xlabel('Nodes')
        # plt.ylabel('Vitesse [m/s]')
        # plt.title("Vitesse")
        plt.grid(True, color='white', linewidth = "0.4", linestyle = "--")
        self.root.ids.GraphSpeedID.add_widget(FigureCanvasKivyAgg(plt.gcf()))


        self.root.ids.MainScreen.remove_widget(self.CardsLayout)
        self.root.ids.MainScreen.add_widget(self.ButtonNavigationLayout)

        self.Navigline = Line(points=[0,0,0,self.root.height,self.root.width,self.root.height,self.root.width,0],
                        close=True,
                        width=20)

        with self.root.ids.map.canvas.after:
            Color(1,0,0,1)
            self.root.ids.map.grp1 = InstructionGroup()
            self.root.ids.map.grp1.add(self.Navigline)


        # Cambiar por coordenadas del GPS
        self.root.ids.map.lat = self.CoordenatesDownSample[0][0]
        self.root.ids.map.lon = self.CoordenatesDownSample[0][1]
        self.MapZoom = 17 # 10 Ville, 15 Rue, 19/20 Batiment, 1 Monde

        self.DrawItinerary()

        Snackbar(
            text="Speed optimized, Have a nice trip!",
            snackbar_x="10dp",
            snackbar_y="10dp",
            size_hint_x=(
                Window.width - (dp(10) * 2)
            ) / Window.width
        ).open()


if __name__ == '__main__':
    NAVecoApp().run()