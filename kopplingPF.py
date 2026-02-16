# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 09:30:19 2026

@author: Alex
"""

import os
os.environ["PATH"]=r'C:\Program Files\DIgSILENT\PowerFactory 2025 SP4'+os.environ["PATH"]
import sys
sys.path.append(r'C:\Program Files\DIgSILENT\PowerFactory 2025 SP4\Python\3.13')
import powerfactory as pf



# skapar funktioner som man kan kallapå för att använda för att hämta projekt, studycase och operationscenario
def set_up_pf(project,studycase,opscen='None'):
    app=pf.GetApplication()
    app.ClearOutputWindow() #rensar utskriftfönstret så man bara ser relevanta fel
    app.ActivateProject(project)
    project=app.GetActiveProject()
    if project is None:
        print('Project not found')
        app.PrintError("There is no active Project")
    else:
        app.PrintPlain("Project: " + project.loc_name)
    studycasefolder= app.GetProjectFolder('study')
    studycases=studycasefolder.GetContents()
    for sc in studycases:
        if studycase in str(sc):
            sc.Activate()
            active=sc
    if opscen!='None': 
        #Select Operation Scenario 
        opfolder= app.GetProjectFolder('scen') 
        ops=opfolder.GetContents() 
        op_check=False 
        for op in ops: 
            if opscen in str(op): 
                op.Activate() 
                active=op 
                op_check=True 
        if op_check==False: 
            app.PrintError("There is no active operation scenario") 
    return app, active