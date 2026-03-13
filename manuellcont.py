# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 09:40:10 2026

@author: Alex
"""
import pandas as pd


def manuell_contingency(app, cont, component, mode="loading"):
    """
    Kör manuell contingency och returnerar
    loading eller aktiv effekt före, efter och skillnad.
    
    mode:
        "loading" -> m:loading
        "P"       -> m:P:bus1
    """

    # -------------------------------
    # Välj attribut
    # -------------------------------
    if mode == "loading":
        attr = "m:loading"
        col_name = "Loading (%)"
    elif mode == "P":
        attr = "m:P:bus1"
        col_name = "Aktiv effekt (MW)"
    else:
        raise ValueError("mode måste vara 'loading' eller 'P'")

    # Säkerställ listformat
    if isinstance(cont, str):
        cont = [cont]
    if isinstance(component, str):
        component = [component]

    # Hämta alla ledningar
    lines = app.GetCalcRelevantObjects('*.ElmLne')
    line_lookup = {l.loc_name: l for l in lines}

    for name in cont + component:
        if name not in line_lookup:
            raise ValueError(f"{name} hittades inte i modellen")

    ldf = app.GetFromStudyCase('ComLdf')

    # --------------------------------------------------
    # 1. Basfall
    # --------------------------------------------------
    ldf.Execute()

    base_values = {
        name: line_lookup[name].GetAttribute(attr)
        for name in component
    }

    try:
        # --------------------------------------------------
        # 2. Koppla bort contingency
        # --------------------------------------------------
        for name in cont:
            line_lookup[name].outserv = 1

        ldf.Execute()

        cont_values = {
            name: line_lookup[name].GetAttribute(attr)
            for name in component
        }

    finally:
        # --------------------------------------------------
        # 3. Återställ nätet
        # --------------------------------------------------
        for name in cont:
            line_lookup[name].outserv = 0

        ldf.Execute()

    # --------------------------------------------------
    # 4. Skapa resultat-tabell
    # --------------------------------------------------
    result = pd.DataFrame({
        f"{col_name} före fel": pd.Series(base_values),
        f"{col_name} efter fel": pd.Series(cont_values),
    })

    result["Skillnad"] = (
        result[f"{col_name} efter fel"] -
        result[f"{col_name} före fel"]
    )

    result["Relativ förändring (%)"] = (
        result["Skillnad"] /
        result[f"{col_name} före fel"] * 100
    )

    return result


