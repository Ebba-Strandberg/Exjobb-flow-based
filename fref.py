

def run_ldf(app, refbus=None): 
    """
    Runs a load flow in the PowerFactory application with a spefied bus as reference bus.
    
    Parameters
    ----------
    app : application object
        The PowerFactory application object.
    refbus : busbar object, optional
        THe busbar to be used as reference bus. If None, the default reference bus in the Westeros system is used.
    Returns
    -------
    None
    """ 

    if refbus is None:
        refbus = app.GetCalcRelevantObjects('*BB2_KiLa380.ElmTerm')[0] # get first busbar as reference busbar
    ldf = app.GetFromStudyCase('ComLdf') # Calling ldf Command object (ComLdf)
    ldf.iopt_apdist = 0 # set active power control to "as Dispatched"
    ldf.iPbalancing = 0 # set balancing to "by reference machine"
    ldf.rembar=refbus # set reference busbar
    ldf.Execute() # executing the load flow command



def get_CNEs(app, loading=0, areas=None, both=False):
    """
    Get Critical Network Elements (CNEs) and corresponding f_ref value based on loading and area criteria. 
    (A load flow must be run before calling this function to get updated loading values.)
    
    Parameters
    ----------
    app : application object
        The PowerFactory application object.
    loading : float, optional
        The loading threshold for identifying CNEs. Default is 0.
    areas : list of str, optional
        A list of area names to consider for identifying CNEs. If None, all areas are considered.
    both : bool, optional
        If True, CNEs must meet both loading and area criteria. If False, CNEs can meet either criterion. Default is False.
    
    Returns
    -------
    dict
        A dictionary with CNE element names as key and their corresponing f_ref values (flow in MW) as values.
    """
    if areas is None:
        areas = [area.loc_name for area in app.GetCalcRelevantObjects('*.ElmArea')] # get areas
    lines = app.GetCalcRelevantObjects('*.ElmLne') # get lines
    transformers = app.GetCalcRelevantObjects('*.ElmTr2') # get transformers
    CNEs={}
    if both:
        for line in lines: # loop through all lines to check if loading AND area criteria are met
            if line.outserv == 0: # check if line is in service
                if line.GetAttribute('c:loading')>= loading and line.GetAttribute('e:cpArea').loc_name in areas: 
                    CNEs[line.loc_name] = line.GetAttribute('m:P:bus1')
        for transformer in transformers: # loop through all transformers to check if loading AND area criteria are met
            if transformer.GetAttribute('c:loading')>= loading and transformer.GetAttribute('e:cpArea').loc_name in areas:
                CNEs[transformer.loc_name] = transformer.GetAttribute('m:P:bushv')
    else:
        for line in lines: # loop through all lines to check if loading OR area criteria are met
            if line.outserv == 0:
                if line.GetAttribute('c:loading')>= loading or line.GetAttribute('e:cpArea').loc_name in areas: 
                    CNEs[line.loc_name] = line.GetAttribute('m:P:bus1')
        for transformer in transformers: # loop through all transformers to check if loading OR area criteria are met
            if transformer.GetAttribute('c:loading')>= loading or transformer.GetAttribute('e:cpArea').loc_name in areas:
                CNEs[transformer.loc_name] = transformer.GetAttribute('m:P:bushv')
    return CNEs

from PTDFcontingency import get_lines_in_areas

def get_CNECs(app, selected_areas: list[str], loading: int, include_parallel: bool=False):

    """
    Gets critical network element contingencies (CNECs) and their corresponding f_ref values
    (flow in MW) for a given set of areas, loading threshold, and parallel line inclusion criteria.
    Contingencies included are all transmission lines (n-1) and all pairs of parallel transmission lines (n-2) 
    within the selected areas.
    
    Parameters
    ----------
    app : application object
        The PowerFactory application object.
    loading : float, optional
        The loading threshold for identifying CNECs.
    selected_areas : list of str, optional
        A list of area names to consider for identifying CNCs. 
    include_parallel : bool, optional
        If True, include n-2 contingencies for parallel lines in the analysis. Default is False.

    Returns
    -------
    dict{str: float}
        A dictionary with CNEC names as keys and their corresponding f_ref values (flow in MW) as values.
        Example: {"Line1 cont: Line2": 150.0}
    """

    lines = get_lines_in_areas(app, selected_areas)
    CNECs_final = {}

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

        if lines_to_outage[0].loc_name[-1].isalpha() or lines_to_outage[0].loc_name.endswith('1'):

            # Koppla bort ledningarna
            for l in lines_to_outage:
                l.SetAttribute('outserv', 1)

            print("Outaging:", [l.loc_name for l in lines_to_outage])

            # bestämma namn på contingency baserat på om det är en eller två ledningar som kopplas bort
            if line.loc_name[-1].isdigit():
                cont_name = lines_to_outage[0].loc_name[:-2]
            else:
                cont_name = lines_to_outage[0].loc_name

            # Kör load flow
            run_ldf(app)

            # Hämta cnecs
            CNECs=get_CNEs(app,loading=loading,both=True)
            CNECs = {f"{k} cont: {cont_name}": v for k, v in CNECs.items()}

            # Koppla tillbaka ledningarna
            for l in lines_to_outage:
                l.SetAttribute('outserv', 0)

            print("Restored:", [l.loc_name for l in lines_to_outage])

            CNECs_final.update(CNECs)

    return CNECs_final

def get_transmission_lines(app,includeHVDC=False):
    """
    Get transmission lines frot Westeros system, with option to include HVDC lines.

    Parameters
    ----------
    app : aplication object
        The PowerFactory application object.
    includeHVDC : bool, optional
        Whether to include HVDC lines in the result.

    Returns
    -------
    dict
        A dictionary with line names as keys and line types and area names as values.
    """
    lines = app.GetCalcRelevantObjects('*.ElmLne') # get lines
    transmissionLines = {}
    for line in lines:
        if '380' in line.typ_id.loc_name: # check if line is a transmission line
            if 'Reinforcement' not in line.typ_id.loc_name: # check if line is not a reinforcement line
                transmissionLines[line.loc_name]='Line Type 380kV in '+line.GetAttribute('e:cpArea').loc_name
            else:
                transmissionLines[line.loc_name]='Line Type 380kV_Reinforcement in '+line.GetAttribute('e:cpArea').loc_name
        if includeHVDC:
            if 'DC' in line.typ_id.loc_name: # check if line is a HVDC line
                transmissionLines[line.loc_name]= 'Line Type DC in '+line.GetAttribute('e:cpArea').loc_name
    return transmissionLines #value is a str that starts with line type and ends with area name 


def print_dict(dict): 
    """
    Prints keys and values from dictionary in format "key: value

    Parameters
    ----------
    dict : dict
        The dictionary to be printed.
    
    Returns
    -------
    None
    """
    for key, value in dict.items():
        print(f'{key}: {value}')