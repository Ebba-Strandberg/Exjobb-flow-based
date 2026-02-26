# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 09:40:10 2026

@author: Alex
"""
import pandas as pd


def manuell_contingency(app, cont, component):
    """
    Kör manuell contingency och returnerar
    loading före, efter och skillnad.
    """

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

    base_loading = {
        name: line_lookup[name].GetAttribute('m:loading')
        for name in component
    }

    try:
        # --------------------------------------------------
        # 2. Koppla bort contingency
        # --------------------------------------------------
        for name in cont:
            line_lookup[name].outserv = 1

        ldf.Execute()

        cont_loading = {
            name: line_lookup[name].GetAttribute('m:loading')
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
        "Loading före fel (%)": pd.Series(base_loading),
        "Loading efter fel (%)": pd.Series(cont_loading),
    })

    result["Skillnad (procentenheter)"] = (
        result["Loading efter fel (%)"] -
        result["Loading före fel (%)"]
    )

    # Valfri relativ förändring
    result["Relativ förändring (%)"] = (
        result["Skillnad (procentenheter)"] /
        result["Loading före fel (%)"] * 100
    )

    return result