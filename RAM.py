# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 13:37:15 2026

@author: Alex
"""











import pandas as pd
import numpy as np

def calculate_F0(app, element_names):
    
    
    # funktionen hämtar just nu active power från HIGH VOLTAGE sidan från trafo, ska detta bytas?
    
    import csv_reader
    element_dict = {name: None for name in element_names}
    dataframe=csv_reader.csv_to_df(r'C:\Users\Alex\Desktop\python\PTDFresultat\BaseCasePTDF.csv',sep=';')
    
    ptdf_selected=csv_reader.filter_df(dataframe, element_dict)
    
    numeric_matrix = ptdf_selected.iloc[1:,:] # remove metadata
    numeric_matrix = numeric_matrix.replace("----", 0)
    numeric_matrix = numeric_matrix.applymap(lambda x: 0 if str(x).strip() == "----" else x)
    numeric_matrix = numeric_matrix.astype(float)
    

    #print(numeric_matrix)
    

    

    # 3. Hämta NP_ref
    areas = app.GetCalcRelevantObjects('*.ElmArea')
    np_ref = {a.loc_name: a.GetAttribute('c:InterP') for a in areas}
    np_series = pd.Series(np_ref).sort_index()

    #print(np_series)


    flow_shift = numeric_matrix.T.dot(np_series)
    
    #print(flow_shift)


    # 5. Hämta F_ref
    F_ref = {}
    
    # Hämta alla linjer och trafos i studiefallet
    lines = app.GetCalcRelevantObjects('*.ElmLne')
    trafos = app.GetCalcRelevantObjects('*.ElmTr2')
    all_objects=lines+trafos

    for name in element_names:
        
        # hitta objektet med rätt namn
        obj = next((o for o in all_objects if o.loc_name == name), None)
        
        if obj is None:
            raise ValueError(f"{name} hittades inte i modellen")
    
        # Hämta aktiv effekt beroende på typ
        if obj.GetClassName() == 'ElmLne':
            F_ref[name] = obj.GetAttribute('m:P:bus1')
    
        elif obj.GetClassName() == 'ElmTr2':
            F_ref[name] = obj.GetAttribute('m:P:bushv:A')
    
    F_ref_series = pd.Series(F_ref)


    #print(F_ref_series)


    # 6. F0
    F0 = F_ref_series - flow_shift
    

    #print(F0)
    return F0






def calculate_Fmax(app, element_names):

    Fmax = {}

    lines = app.GetCalcRelevantObjects('*.ElmLne')
    trafos = app.GetCalcRelevantObjects('*.ElmTr2')
    all_objects = lines + trafos

    for name in element_names:

        obj = next((o for o in all_objects if o.loc_name == name), None)

        if obj is None:
            raise ValueError(f"{name} hittades inte i modellen")

        loading = obj.GetAttribute('m:loading')

        if loading == 0:
            raise ValueError(f"{name} har loading = 0 %, kan ej beräkna Fmax")

        if obj.GetClassName() == 'ElmLne':
            F = obj.GetAttribute('m:P:bus1')

        elif obj.GetClassName() == 'ElmTr2':
            F = obj.GetAttribute('m:P:bushv:A')

        Fmax[name] = F / loading * 100

    return pd.Series(Fmax)




def calculate_RAM(app, element_names, F_RA=0, F_RM=0, F_AAC=0, RA_is_percent=False, PositivRAM=True):

    if PositivRAM:
        # Hämta F0 och Fmax
        F0 = calculate_F0(app, element_names)
        Fmax = calculate_Fmax(app, element_names)
    
        # Säkerställ procentform (10 → 0.1)
        if RA_is_percent:
            if F_RA > 1:
                F_RA = F_RA / 100
    
            RAM = (Fmax - F0) * F_RA
    
        else:
            # Gör till Series om det behövs
            if not isinstance(F_RA, pd.Series):
                F_RA = pd.Series(F_RA, index=element_names)
    
            if not isinstance(F_RM, pd.Series):
                F_RM = pd.Series(F_RM, index=element_names)
    
            if not isinstance(F_AAC, pd.Series):
                F_AAC = pd.Series(F_AAC, index=element_names)
    
            # Säkerställ samma index
            F_RA = F_RA.reindex(Fmax.index)
            F_RM = F_RM.reindex(Fmax.index)
            F_AAC = F_AAC.reindex(Fmax.index)
            F0 = F0.reindex(Fmax.index)
    
            RAM = Fmax + F_RA - F_RM - F_AAC - F0
            
    else:
        # Hämta F0 och Fmax
        F0 = calculate_F0(app, element_names)
        Fmax = -calculate_Fmax(app, element_names)
    
        # Säkerställ procentform (10 → 0.1)
        if RA_is_percent:
            if F_RA > 1:
                F_RA = F_RA / 100
    
            RAM = (Fmax - F0) * F_RA
    
        else:
            # Gör till Series om det behövs
            if not isinstance(F_RA, pd.Series):
                F_RA = pd.Series(F_RA, index=element_names)
    
            if not isinstance(F_RM, pd.Series):
                F_RM = pd.Series(F_RM, index=element_names)
    
            if not isinstance(F_AAC, pd.Series):
                F_AAC = pd.Series(F_AAC, index=element_names)
    
            # Säkerställ samma index
            F_RA = F_RA.reindex(Fmax.index)
            F_RM = F_RM.reindex(Fmax.index)
            F_AAC = F_AAC.reindex(Fmax.index)
            F0 = F0.reindex(Fmax.index)
    
            RAM = Fmax + F_RA - F_RM - F_AAC - F0 
            
    return RAM
    




