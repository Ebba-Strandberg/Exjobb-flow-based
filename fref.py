

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
            if line.GetAttribute('c:loading')>= loading and line.GetAttribute('e:cpArea').loc_name in areas: 
                CNEs[line.loc_name] = line.GetAttribute('m:P:bus1')
        for transformer in transformers: # loop through all transformers to check if loading AND area criteria are met
            if transformer.GetAttribute('c:loading')>= loading and transformer.GetAttribute('e:cpArea').loc_name in areas:
                CNEs[transformer.loc_name] = transformer.GetAttribute('m:P:bushv')
    else:
        for line in lines: # loop through all lines to check if loading OR area criteria are met
            if line.GetAttribute('c:loading')>= loading or line.GetAttribute('e:cpArea').loc_name in areas: 
                CNEs[line.loc_name] = line.GetAttribute('m:P:bus1')
        for transformer in transformers: # loop through all transformers to check if loading OR area criteria are met
            if transformer.GetAttribute('c:loading')>= loading or transformer.GetAttribute('e:cpArea').loc_name in areas:
                CNEs[transformer.loc_name] = transformer.GetAttribute('m:P:bushv')
    return CNEs

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