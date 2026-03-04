# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 13:37:15 2026

@author: Alex
"""




import pandas as pd
import numpy as np

def _calculate_F0(app, dataframe):
    
    """
    Beräknar:
    F0 = F_ref - PTDF * NP_ref
    """

    # ==================================================
    # 1. HÄMTA NP_ref
    # ==================================================
    areas = app.GetCalcRelevantObjects('*.ElmArea')
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
    lines = app.GetCalcRelevantObjects('*.ElmLne')

    # skapa lookup-dict (snabbare än next i loop)
    line_lookup = {l.loc_name: l for l in lines}

    F_ref = {}

    for col in df.columns:

        # om kolumnen innehåller "cont:" → ta bort den delen
        clean_name = col.split(" cont:")[0].strip()

        if clean_name not in line_lookup:
            raise ValueError(f"{clean_name} hittades inte i modellen")

        obj = line_lookup[clean_name]

        # Aktiv effekt från bus1
        F_ref[col] = obj.GetAttribute('m:P:bus1')

    F_ref_series = pd.Series(F_ref)


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

        loading = obj.GetAttribute('m:loading')

        if loading is None or loading == 0:
            raise ValueError(f"{clean_name} har loading = 0 %, kan ej beräkna Fmax")

        # Aktiv effekt från bus1
        F = obj.GetAttribute('m:P:bus1')

        # Använd absolutbelopp (viktigt om flödet är negativt)
        Fmax[col] = abs(F) / loading * 100

    return pd.Series(Fmax)




def calculate_RAM(app, dataframe,
                  F_RA=0, F_RM=0, F_AAC=0,
                  RA_is_percent=False,
                  PositivRAM=True):
    """
    Beräknar RAM enligt:

    RAM = Fmax + F_RA - F_RM - F_AAC - F0

    Parametrar
    ----------
    dataframe : PTDF dataframe
    F_RA : MW eller procent (om RA_is_percent=True)
    F_RM : MW
    F_AAC : MW
    PositivRAM : True = positiv riktning, False = negativ
    """

    # --------------------------------------------------
    # 1. Hämta F0 och Fmax
    # --------------------------------------------------
    F0 = _calculate_F0(app, dataframe)
    Fmax = _calculate_Fmax(app, dataframe)

    if not PositivRAM:
        Fmax = -Fmax

    # --------------------------------------------------
    # 2. Om RA är procent
    # --------------------------------------------------
    if RA_is_percent:
        if F_RA > 1:
            F_RA = F_RA / 100

        RAM = (Fmax - F0) * F_RA
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
    




