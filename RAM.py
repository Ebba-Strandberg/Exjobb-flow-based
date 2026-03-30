# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 13:37:15 2026

@author: Alex
"""



import fref
import pandas as pd
import numpy as np

def _calculate_F0(app, dataframe, results_mancont: pd.DataFrame | None = None, case_if_traditional: int | None = None):
    
    """
    Beräknar:
    F0 = F_ref - PTDF * NP_ref
    
    results_mancont
        if RAM for a before and after PTDF is to be calculated, include the manual contingecy dataframe for the case

    case_if_traditional 
        if RAM for a traditional PTDF is to be calculated, include case number 
        (1 = Iron Islands, 2 = Dorne, 3 = Stormlands)
    """

    # ==================================================
    # 1. HÄMTA NP_ref
    # ==================================================
    areas = app.GetCalcRelevantObjects('*.ElmArea')
    fref.run_ldf(app)
    np_ref = {a.loc_name: a.GetAttribute('c:InterP') for a in areas}
    np_series = pd.Series(np_ref).sort_index()


    # ==================================================
    # 2. RENGÖR PTDF
    # ==================================================
    df = dataframe.copy()
    
    # # Ta bort första raden (text-raden)
    # df = df.iloc[1:]
    
    # Ersätt "----" med 0
    df = df.replace("----", 0)
    
    # Konvertera till numerisk
    df = df.apply(pd.to_numeric, errors='coerce')
    
    # Ersätt ev NaN med 0
    df = df.fillna(0)


    # ==================================================
    # 3. HÄMTA F_ref AUTOMATISKT FRÅN KOLUMNNAMN
    # ==================================================

    F_ref={}
    if results_mancont is not None and case_if_traditional is None:
        print('hej')
        F_ref_list = []
        for i in range(dataframe.shape[1]//2):
            for j in range(2):
                F_ref_list.append(results_mancont.iloc[i,j])
        
        row_nbr = 0
        for col in dataframe.columns:
            F_ref[col]=F_ref_list[row_nbr]
            row_nbr+=1
        
        F_ref_series = pd.Series(F_ref)

    elif results_mancont is None and case_if_traditional is not None:
        CNEs = fref.get_CNEs(app,80,both=True)
        if case_if_traditional == 1:
            CNECs=fref.get_CNECs(app,['Iron Islands'],100,True,5)
        elif case_if_traditional == 2:
            CNECs=fref.get_CNECs(app,['Dorne'],100,True,5)
        elif case_if_traditional == 3:
            CNECs=fref.get_CNECs(app,['Stormlands'],100,True,5)
        for col in dataframe.columns:
            if 'cont' in col:
                F_ref[col]=CNECs[col]
            else:
                F_ref[col]=CNEs[col]
        F_ref_series=pd.Series(F_ref)

    else: raise Exception('Include either manual contingency datafram OR case number')



    # ==================================================
    # 4. MATRISPRODUKT
    # ==================================================
    flow_correction = df.T.dot(np_series)


    # ==================================================
    # 5. BERÄKNA F0
    # ==================================================
    F0 = F_ref_series - flow_correction

    return F0




def _calculate_Fmax(app, dataframe):
    """
    Beräknar Fmax för alla ledningar (ElmLne) i PTDF-dataframen.

    Fmax = |F| / loading * 100
    """

    # Hämta alla ledningar
    lines = app.GetCalcRelevantObjects('*.ElmLne')

    # Skapa lookup-dictionary
    line_lookup = {l.loc_name: l for l in lines}

    Fmax = {}

    for col in dataframe.columns:

        # Ta bort eventuell "cont:"-del
        clean_name = col.split(" cont:")[0].strip()

        if clean_name not in line_lookup:
            raise ValueError(f"{clean_name} hittades inte i modellen eller är inte en ledning")

        obj = line_lookup[clean_name]

        fref.run_ldf(app)
        loading = obj.GetAttribute('m:loading')

        if loading is None or loading == 0:
            raise ValueError(f"{clean_name} har loading = 0 %, kan ej beräkna Fmax")

        # Aktiv effekt från bus1
        F = obj.GetAttribute('m:P:bus1')

        # Använd absolutbelopp (viktigt om flödet är negativt)
        Fmax[col] = abs(F) / loading * 100

    return pd.Series(Fmax)




def calculate_RAM(app, dataframe:pd.DataFrame,results_mancont: pd.DataFrame | None = None,case_if_traditional: int | None = None,
                  F_RA=0, F_RM=0, F_AAC=0,
                  RM_is_percent=False,
                  PositivRAM=True):
    """
    Beräknar RAM enligt:

    RAM = Fmax + F_RA - F_RM - F_AAC - F0

    Parametrar
    ----------
    dataframe : PTDF dataframe
    results_mancont: if RAM for a before and after PTDF is to be calculated, 
        include the manual contingecy dataframe for the case
    case_if_traditional: if RAM for a traditional PTDF is to be calculated, include case number 
        (1 = Iron Islands, 2 = Dorne, 3 = Stormlands)
    F_RA : MW 
    F_RM : MW eller procent (om RM_is_percent=True)
    F_AAC : MW
    PositivRAM : True = positiv riktning, False = negativ
    """

    # --------------------------------------------------
    # 1. Hämta F0 och Fmax
    # --------------------------------------------------
    F0 = _calculate_F0(app, dataframe,results_mancont,case_if_traditional)
    Fmax = _calculate_Fmax(app, dataframe)

    if not PositivRAM:
        Fmax = -Fmax

    # --------------------------------------------------
    # 2. Om RA är procent
    # --------------------------------------------------
    if RM_is_percent:
        if F_RM > 1:
            F_RM = F_RM / 100

        RAM = (Fmax - F0) * F_RM
        return RAM

    # --------------------------------------------------
    # 3. Säkerställ Series-format
    # --------------------------------------------------
    index = Fmax.index

    def ensure_series(x):
        if isinstance(x, pd.Series):
            return x.reindex(index)
        else:
            return pd.Series(x, index=index)

    F_RA = ensure_series(F_RA)
    F_RM = ensure_series(F_RM)
    F_AAC = ensure_series(F_AAC)
    F0 = F0.reindex(index)

    # --------------------------------------------------
    # 4. RAM-beräkning
    # --------------------------------------------------
    RAM = Fmax + F_RA - F_RM - F_AAC - F0

    return RAM
    




