# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 11:04:30 2026

@author: Alex
"""
import os
def run_basecase_ptdf(app):

    # ----- Kör PTDF -----
    ptdf = app.GetFromStudyCase("ComVstab")

    ptdf.frmElmFilt4Res = 0
    ptdf.iopt_method = 0   
    ptdf.factors4bus = 1
    ptdf.calcPtdf = 1
    ptdf.isContSens = 0
    ptdf.calcRegionSens = 1
    ptdf.calcBoundSens = 1
    ptdf.calcShiftKeySens = 1
    ptdf.dpflim = 0.01

    ptdf.Execute()

    # ----- Exportera -----
    folder = r'C:\Users\Alex\Desktop\python\PTDFresultat'

    if not os.path.exists(folder):
        os.mkdir(folder)

    resultat = app.GetCalcRelevantObjects('*.ElmRes')
    res = app.GetFromStudyCase("ComRes")

    res.SetAttribute('pResult', resultat[0])
    res.iopt_exp = 6

    res.f_name = os.path.join(folder, 'BaseCasePTDF.csv')

    res.ExportFullRange()

   