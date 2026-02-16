# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 09:26:14 2026

@author: Alex
"""

# area_cont = [Dorn,Stormlands...]
# feltyp = 1, 2 eller 3







def get_lines_in_areas(app, selected_areas, includeHVDC=False):

    lines = app.GetCalcRelevantObjects('*.ElmLne')
    selected_lines = []

    for line in lines:
        area_name = line.GetAttribute('e:cpArea').loc_name

        if area_name in selected_areas:
            if '380' in line.typ_id.loc_name:
                if 'Reinforcement' not in line.typ_id.loc_name:
                    selected_lines.append(line)

            if includeHVDC and 'DC' in line.typ_id.loc_name:
                selected_lines.append(line)

    return selected_lines



def run_ptdf(app):

    ptdf = app.GetFromStudyCase("ComVstab")
    #ptdf.p_bus.Clear()

    AllaArea = app.GetCalcRelevantObjects('*.ElmArea')

    for area in AllaArea:
        ptdf.p_bus.AddRef(area)

    ptdf.frmElmFilt4Res = 0
    ptdf.iopt_method = 0  # det här indikerar AC men jag tycker nästan vi borde köra DC då vår teori bygger på det
    ptdf.factors4bus = 1
    ptdf.calcPtdf = 1
    ptdf.isContSens = 0
    ptdf.calcRegionSens = 1
    ptdf.calcBoundSens = 1
    ptdf.calcShiftKeySens = 1
    ptdf.dpflim = 0.01

    ptdf.Execute()


import os

def export_ptdf(app, line_name):



    resultat=app.GetCalcRelevantObjects('*.ElmRes')
    # Collect results of distribution factor calculation (via conversion to csv)
    res=app.GetFromStudyCase("ComRes")
    
    res.SetAttribute('pResult',resultat[0])
    res.iopt_exp=6            
                 # 6: csv

    
    
    res.f_name = rf'C:\Users\Alex\Desktop\python\PTDFresultat\PTDF_{line_name}.csv'
    res.ExportFullRange()

    
    # denna funktion kopplar bort alla ledningar en efter en och kör en ptdf
    
def run_ptdf_per_line(app, selected_areas, include_parallel=False):

    lines = get_lines_in_areas(app, selected_areas)

    for line in lines:

        print("Outaging:", line.loc_name)

        # Koppla bort ledning
        line.SetAttribute('outserv', 1)

        # Kör PTDF
        run_ptdf(app)

        # Unikt filnamn
        #filename = f"PTDF_{line.loc_name}.csv"

        # Exportera
        export_ptdf(app, line.loc_name)

        # Koppla tillbaka ledning
        line.SetAttribute('outserv', 0)

        print("Restored:", line.loc_name)




## denna funktion inkluderar parallella ledningar
# om det är två parallella ledningar så kopplar den bort båda de parallella, är det tre parallella så kopplar den bort 2 av de 3 parallella

import itertools

def run_ptdf_per_line_complete(app, selected_areas, include_parallel=False):

    lines = get_lines_in_areas(app, selected_areas)

    # Skapa en dict som grupperar parallella ledningar
    parallel_groups = {}
    if include_parallel:
        for line in lines:
            group_name = "_".join(line.loc_name.split("_")[:-1]) #den här kollar namnet på ledningen utan den sista siffran
            if group_name not in parallel_groups:
                parallel_groups[group_name] = []
            parallel_groups[group_name].append(line)

    visited_groups = set()  # för att inte köra samma grupp flera gånger

    for line in lines:

        # Kontrollera om vi redan har hanterat denna grupp
        if include_parallel:
            group_name = "_".join(line.loc_name.split("_")[:-1])
            if group_name in visited_groups:
                continue  # hoppa över, gruppen redan hanterad
            visited_groups.add(group_name)

            # Hämta alla parallella ledningar i denna grupp
            group_lines = parallel_groups[group_name]

            # N-2 logik
            if len(group_lines) == 2:
                lines_to_outage = group_lines
            elif len(group_lines) >= 3:
                lines_to_outage = group_lines[:2]  # ta de två första
            else:
                lines_to_outage = group_lines
        else:
            lines_to_outage = [line]

        # Koppla bort ledningarna
        for l in lines_to_outage:
            l.SetAttribute('outserv', 1)

        print("Outaging:", [l.loc_name for l in lines_to_outage])

        # Kör PTDF
        run_ptdf(app)

        # Exportera PTDF med unikt namn
        for l in lines_to_outage:
            export_ptdf(app, l.loc_name)

        # Koppla tillbaka ledningarna
        for l in lines_to_outage:
            l.SetAttribute('outserv', 0)

        print("Restored:", [l.loc_name for l in lines_to_outage])

#%%


# innan man kör är det viktigt att plocka bort de befintliga filerna sedan förra körningen. man kan inte exportera om det finns en fil med samma namn
selected_areas = ['Dorne', 'Reach', 'Crownlands']
import powerfactory as pf
app=pf.GetApplication()

run_ptdf_per_line_complete(app, selected_areas, include_parallel=True)

