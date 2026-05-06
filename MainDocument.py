# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 14:56:37 2026

@author: Alex
"""

#%% Importera
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd




from kopplingPF import set_up_pf

# Set up PowerFactory

app,studycase=set_up_pf('Westeros','00 Load Flow - Active Power Balance','Static calculations') 
app.Show()              




#%%  Load Flow

import fref
selected_areas = ['Iron Islands']
#selected_areas = ['Dorne']
#selected_areas = ['Stormlands']

CNEC=fref.get_CNECs(app, selected_areas, loading=100, delta_loading=5,include_parallel=True)




#%% CNE


CNE=fref.get_CNEs(app,loading=80,both=True) # dictionary med CNE-namn och Fref

#fref.print_dict(CNE)




#%% GSK


import GSK

GSKtype='standard'
#GSKtype='produktionsfaktor'
#GSKtype='differens'
produktionstyp='Coal', 'Oil', 'Gas', 'Hydro', 'Pump storage', 'Biogas', 'Biomass', 'Other Biofuel', 'Peat', 'Waste', 'Other fossil fuel','Storage','Diesel','Other Static Generator',"Dragon Power"
#exkluderade_typer = ['Electrolyser', 'Reactive power compensation']

GSK.set_GSK1(app,produktionstyp,GSKtype)
#GSK.set_GSK(app,"ALL",GSKtype,exkluderade_typer)




#%% PTDF för Base Case

# kom ihåg att ändra filepath och ta bort tidigare resultat

import BaseCasePTDF

BaseCasePTDF.run_basecase_ptdf(app)



#%% Contingency PTDF

import PTDFcontingency

# innan man kör är det viktigt att plocka bort de befintliga filerna sedan förra körningen. man kan inte exportera om det finns en fil med samma namn
selected_areas = ['Reach','Westerlands','Iron Islands']
#selected_areas=['Iron Islands']
#selected_areas = ['Stormlands','Reach']


PTDFcontingency.run_ptdf_per_line_complete(app, selected_areas, include_parallel=True)





#%% Sortering resultat

import csv_reader

fp_ContingencyFolder= rf"C:\Users\Alex\Desktop\python\PTDFresultat"

fp_BaseCase= rf"C:\Users\Alex\Desktop\python\PTDFbase\BaseCasePTDF.csv"

#dataframeBASECASE=csv_reader.csv_to_df(fp_BaseCase)

dataframeCLASSIC=csv_reader.filter_df_contingency(fp_BaseCase,CNE,fp_ContingencyFolder,CNEC)




# --- STORMLANDS

#component = ['line_Tumbleton_Kings Landing_1','line_Grassy Vale_Tumbleton','line_Grassy Vale_Summerhall','line_Kings Landing_Highgarden','line_Highgarden_Summerhall_1']
#cont = ['line_Summerhall_Kings Landing']

#dataframeDELTA=csv_reader.compare_PTDF(fp_BaseCase, fp_ContingencyFolder,3,component,cont)

# --- IRON ISLANDS

component=['line_The Crag_Pyke','line_Faircastle_The Crag','line_Casterly Rock_Faircastle']
cont=['line_Pyke_Casterly Rock']


# --- DORNE
#component=["line_Starfall_Blackmont_1","line_Yronwood_Blackmont","line_The Tor_Yronwood_1","line_Ghost Hill_The Tor","line_Sunspear_Ghost Hill","line_Starfall_Sandstone_1",
#           "line_Sandstone_Hellholt","line_Hellholt_Vaith","line_Vaith_Salt Shore","line_Salt Shore_Lemonwood_1","line_Lemonwood_Sunspear_1"]
#cont=["line_Starfall_Sunspear"]

#dataframeDELTA=csv_reader.compare_PTDF(fp_BaseCase, fp_ContingencyFolder,3,component,cont)

dataframeBEFOREnAFTER=csv_reader.find_largest_PTDF(fp_BaseCase, fp_ContingencyFolder,3,component,cont)


#%%
import manuellcont



# --- STORMLANDS

#component = ['line_Tumbleton_Kings Landing_1','line_Grassy Vale_Tumbleton','line_Grassy Vale_Summerhall','line_Kings Landing_Highgarden','line_Highgarden_Summerhall_1']
#cont = ['line_Summerhall_Kings Landing_1','line_Summerhall_Kings Landing_2']

# --- IRON ISLANDS

component=['line_The Crag_Pyke','line_Faircastle_The Crag','line_Casterly Rock_Faircastle']
cont=['line_Pyke_Casterly Rock']

# --- DORNE
#component=["line_Starfall_Blackmont_1","line_Yronwood_Blackmont","line_The Tor_Yronwood_1","line_Ghost Hill_The Tor","line_Sunspear_Ghost Hill","line_Starfall_Sandstone_1",
#           "line_Sandstone_Hellholt","line_Hellholt_Vaith","line_Vaith_Salt Shore","line_Salt Shore_Lemonwood_1","line_Lemonwood_Sunspear_1"]

#cont=["line_Starfall_Sunspear_1","line_Starfall_Sunspear_2"]

results_mancont=manuellcont.manuell_contingency(app, cont, component,mode="P")

#%%

import csv_reader

#test=csv_reader.add_RAM(app, CLASSICrensad)
csv_reader.add_RAM(app, dataframeCLASSIC,results_mancont,F_RA=0,F_RM=0,F_AAC=0,RA_is_percent=False)





#%% RAM

import RAM

test3=RAM.calculate_RAM(app, dataframeBEFOREnAFTER,F_RA=0,F_RM=0,F_AAC=0,RA_is_percent=False,PositivRAM=True)

# Om olika värden på F_RA eller liknande

# F_RA = pd.Series({
#     'line_Antlers_Maidenpool': 40,
#     'line_Casterly Rock_Lannisport_1': 35
# })






