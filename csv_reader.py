import pandas as pd
import os

# Functions that start with _ are only meant to be used inside the file

def csv_to_df(csvFile: str, sep: str = ',') -> pd.DataFrame:
    """
    Takes a csv file path and separator and returns a dataframe with index name 
    changed to areas in Westeros system and removes irrelevant variables/units for sensitivity.
    
    Parameters
    ----------  
    csvFile : str
        The file path of the csv file to be read.
    sep : str, optional
        The separator used in the csv file. Default is ','.
    Returns
    -------
    DataFrame
        A pandas DataFrame containing the data from the csv file with index name changed to areas in Westeros system..
    """
    df=pd.read_csv(csvFile, sep=sep, index_col=0)
    _change_df_index_name(df)

    df=df.iloc[:,2:]
    
    # 'Branch Sensitivity dPbranch/dPbus/HV-Side',

    var = 'Branch Sensitivity dPbranch/dPbus/Terminal i'

    mask = df.iloc[0].str.contains(var, na=False)

    filtered = df.loc[:, mask]

    return filtered

def _change_df_index_name(df: pd.DataFrame) -> None: # Change index name to areas, only called inside csv_to_df function

    df.index =  ['Area:','Crownlands', 'Dorne', 'Essos', 'Iron Islands', 'North', 'Reach',
                    'Riverlands', 'Stormlands', 'Vale', 'Westerlands']

def filter_df(df: pd.DataFrame,CNEs: dict | list) -> pd.DataFrame:
    """
    Take dataframe of PTDFs and dict with CNEs as keys or list of CNEs and return PTDFS for given CNEs

    Parameters
    ----------
    df : DataFrame
        dataframe
    CNEs : dict | list
        Dictionary containing CNE element names as keys or list of CNE element names

    Returns
    -------
    DataFrame
    """
    if isinstance(CNEs,dict):

        CNEList = []

        for key in CNEs.keys():
            CNEList.append(key)

    else: CNEList=CNEs

    regex = "|".join(CNEList)   

    filtered_df = df.filter(regex=regex)
    
    return filtered_df

def filter_df_contingency(filepathBaseCase: str, CNEs: dict | list,
                          filepathToFolder: str, CNECs: dict | list,) -> pd.DataFrame:
    """
    Takes the filepath to the base case PTDF, a list or dict of CNEs, a file path to the folder where the contingency
    PTDFs are located, and a list or dict of CNECs

    returns a datafram complete with all PTDFs of CNEs and CNECs

    Parameters
    ----------
    filepathBaseCase
        File path to base case PTDF csv file
    CNECs : dict | list
        Dict of CNEC element names as keys or list of CNEC element names
    CNEs : dict | list 
        Dict of CNE element names as keys or list of CNEC element names
    filepathToFolder : str
        The filepath to the folder where CNEC PTDF csv files are located
    
    Returns
    -------
    DataFrame
        A DataFrame containing PTDFs for all CNEs and CNECs.
    
    """
    cont_dfs={}
    CNECList = []

    baseCase_df = csv_to_df(filepathBaseCase)
    df=filter_df(baseCase_df,CNEs)

    if isinstance(CNECs,dict):
        for key in CNECs.keys():
            CNECList.append(key)
    else: CNECList=CNECs

    for CNEC in CNECList:
        line, cont = CNEC.split(' cont: ') # split line from contingency in key
        if cont not in cont_dfs.keys():
            df_cont=csv_to_df(f'{filepathToFolder}/PTDF_{cont}.csv') # find and read contingency df
            cont_dfs[cont]=df_cont # add contingecy df with the contingency as key to the dict
        df_filtered = filter_df(cont_dfs[cont], [f'{line}']) # use filter_df to find CNEC in df
        df_filtered.columns.values[0] += f' cont: {cont}' # rename column to include contingency in name
        df=df.join(df_filtered) # add new CNEC to current df by index
    
    return df

def find_largest_PTDF(filepathBaseCase: str, filepathContingencyFolder: str, include: int = 1) -> pd.DataFrame:
    """
    Takes a file path to a csv-file including base case PTDFs and a file path to a folder 
    including contingency case PTDFs, and returns the specified number of columns containing the largest values.

    Parameters
    ----------
    filepathBaseCase : str
        The file path of the csv file containing base case PTDFs.
    filepathContingencyFolder : str
        The file path to the folder containing the contingency case PTDFs.
    include : int
        Includes the columns containing the x largest values.

    Returns
    -------

    DataFrame
    """

    df = csv_to_df(filepathBaseCase)
    
    for name in os.listdir(filepathContingencyFolder):
        cont_name = name.removeprefix('PTDF_').removesuffix('.csv')
        path = os.path.join(filepathContingencyFolder,name)
        df_cont=csv_to_df(path)
        df_cont.columns = [oldColName + " cont: " + cont_name for oldColName in df_cont.columns]
        df=df.join(df_cont)
    
    return _find_largest_PTDF(df, include)

def _find_largest_PTDF(df: pd.DataFrame, include: int = 1) -> pd.DataFrame:
    """
    Returns the specified number of columns containing the largest values.

    Parameters
    ----------
    df : DataFrame
        Dataframe to filter.
    include : int
        Includes the columns containing the x largest values.

    Returns
    -------

    DataFrame
    """

    num = df.iloc[1:,:] # remove metadata

    num=num.apply(pd.to_numeric, errors='coerce')
    
    num = num.dropna(axis=1, how='all')

    if num.shape[1] == 0:
        raise ValueError('This data frame contains no numeric values')

    col_max = num.abs().max()

    # Sort columns by their max values descending
    top_cols = col_max.sort_values(ascending=False).index[:include]

    # Keep only top columns from original DataFrame (including metadata row/cols)
    # Adjust index offset for the first two metadata columns
    top_cols_full = [df.columns[ df.iloc[1:,:].columns.get_loc(c)] for c in top_cols]

    # Return new DataFrame with all rows but only the top columns
    return df.loc[:, top_cols_full]

def compare_PTDF(filepathBaseCase: str, filepathContingencyFolder: str, include: int = 1, CNECs: list[str] | None = None,
                  contingencies: list[str] | None = None) -> pd.DataFrame:
    """
    Takes a file path to a csv-file including base case PTDFs and a file path to a folder 
    including contingency case PTDFs, and returns the specified number of columns containing the largest differences.

    Parameters
    ----------
    filepathBaseCase : str
        The file path of the csv file containing base case PTDFs.
    filepathContingencyFolder : str
        The file path to the folder containing the contingency case PTDFs.
    include : int
        Include the columns containing the x largest differences.
    
    Returns
    -------
    DataFrame
    """

    BaseCase_df = csv_to_df(filepathBaseCase)

    df = pd.DataFrame()

    for name in os.listdir(filepathContingencyFolder):
        cont_name = name.removeprefix('PTDF_').removesuffix('.csv')
        path = os.path.join(filepathContingencyFolder,name)
        df_cont=csv_to_df(path)
        diff = _compare_PTDF(BaseCase_df,df_cont)
        diff.columns = [oldColName + " cont: " + cont_name for oldColName in diff.columns]
        df = pd.concat([df, diff], axis=1)
    
    if CNECs != None and contingencies != None:

        include_list = []

        for cnec in CNECs:
            for cont in contingencies:
                include_list.append(f'{cnec} cont: {cont}')

        return(filter_df(df,include_list))

    return _find_largest_PTDF(df, include)

def _compare_PTDF(df1: pd.DataFrame, df2: pd.DataFrame, include: int = 1) -> pd.DataFrame:
    """
    Takes two dataframes and subtracts all the numerical values in the corresponding cells,
    then returns a dataframe with the difference between the two original.

    Parameters
    ----------
    df1 : DataFrame
        First dataframe to compare.
    df2 : DataFrame
        Second dataframe to compare.
    include : int
        Includes the columns containing the x largest values.

    Returns
    -------

    DataFrame
    """
    df1, df2 = df1.align(df2, join="inner", axis=None) # align both index and columns, keeping only common ones

    metadata = df1.iloc[[0]]

    # --- REMOVE METADATA ---
    num1 = df1.iloc[1:, :]   # rows 1:end, all columns
    num2 = df2.iloc[1:, :]

    # Convert to numeric safely
    num1 = num1.apply(pd.to_numeric, errors="coerce") 
    num2 = num2.apply(pd.to_numeric, errors="coerce")

    # Align again after cleanup
    num1, num2 = num1.align(num2, join="inner", axis=1)

    if num1.shape[1] == 0:
        raise ValueError("No common PTDF columns to compare.")

    # --- COMPUTE DIFFERENCE ---
    diff = (num1 - num2).abs()

    # --- REATTACH METADATA ---
    complete_df = pd.concat([metadata,diff])

    return complete_df


