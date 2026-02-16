# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 11:58:06 2026

@author: Alex
"""



def set_GSK(produktionstyp,GSKtype):
    import powerfactory as pf # måste jag ha med dessa två rader? lyser rött annars
    app=pf.GetApplication()
    
    
    AllaArea=app.GetCalcRelevantObjects('*.ElmArea') #hämtar alla områden
    Generatorer = app.GetCalcRelevantObjects('*.ElmSym') + app.GetCalcRelevantObjects('*.ElmGenStat') # plockar ut alla generatorer
    gen_per_area = {} # skapar dictionary för att hålla alla generatorer i varje area, blir som tabell
    
    
    #GSKtype='produktionsfaktor'
    #produktionstyp='Coal', 'Oil', 'Gas', 'Hydro', 'Pump storage', 'Biogas', 'Biomass', 'Other Biofuel', 'Peat', 'Waste', 'Other fossil fuel','Storage'
    
    
    for area in AllaArea:
        gen_per_area[area.loc_name] = []
    
        for gen in Generatorer:
            if gen.cpArea == area:
                gen_per_area[area.loc_name].append(gen) # lägger till varje generator till varje area
    
    
    if GSKtype == 'differens':
        for zone_name in gen_per_area:
            summa_diff=0.0 #skapar variabel för differensen för en zon
            for gen in gen_per_area[zone_name]: # denna del plockar fram nämnaren vilket är summan av alla diferenser i arean
                generatortyp = gen.GetAttribute('cCategory') #kollar kategori för generatorn
                if generatortyp in produktionstyp:
                    pmax = gen.GetAttribute('Pmax_uc') # högsta rated
                    pact = gen.GetAttribute('pgini') # aktiv effekt som produceras nu
                    
                    diff=pmax-pact
                    if diff > 0:
                        summa_diff += diff # om differensen är större än noll så läggs den till. om den skulle vara noll så är generatorn redan på max
            if summa_diff == 0: # bara för att undvika division med noll
                continue
                    
            for gen in gen_per_area[zone_name]: #denna del beräknar differensen för generatorn och relativa GSK
                generatortyp = gen.GetAttribute('cCategory')
                
                if generatortyp in produktionstyp:
                    pmax = gen.GetAttribute('Pmax_uc')
                    pact = gen.GetAttribute('pgini')
                    
                    diff=pmax-pact
                    
                    if diff > 0:
                       gsk = diff / summa_diff * 100
                    else:
                        gsk = 0
                    
                    gen.SetAttribute('genShiftKey', gsk)
                
                else:
                    gen.SetAttribute('genShiftKey', 0)
    
    elif GSKtype == 'produktionsfaktor': # Förutbestämda PF parametrar men plockar bort generationstyper som man inte vill ha
        for zone_name in gen_per_area:
            for gen in gen_per_area[zone_name]:
                generatortyp = gen.GetAttribute('cCategory')
                
                if generatortyp in produktionstyp:
                    gen.SetAttribute('genShiftKey',100)
                else:
                    gen.SetAttribute('genShiftKey',0)
                
        
    elif GSKtype == 'standard': # standard i den mening att det är förutbestämda värden av PF, 100% oavsett gnerationstyp
        for zone_name in gen_per_area:
            for gen in gen_per_area[zone_name]:
                #print(zone_name, gen.loc_name)
                gen.SetAttribute('genShiftKey',100) # loopar igenom alla generatorer och sätter GSK till 100%
        
    else:
        print("Okänd GSK-typ")
        
        

