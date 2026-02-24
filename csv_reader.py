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

def filter_df_contingency(df: pd.DataFrame, CNECs: dict | list, CNEs: dict | list | None = None, 
                          filepathToFolder: str = './ptdf_results') -> pd.DataFrame:
    """
    Takes a dataframe with PTDFs for CNEs AND a list or dictionary of CNECs
                            OR
    an unfiltered dataframe it all basecase PTDFs AND a list or dictionary of CNEs AND 
    a list or dictionary of CNECs

    also takes a the filepath to the folder where CNEC PTDFs are located

    returns a datafram complete with all PTDFs of CNEs and CNECs

    Parameters
    ----------
    df : DataFrame
        DataFrame with PTDFs for CNEs or unfiltered dataframe with all basecase PTDFs
    CNECs : dict | list
        Dictionary containing CNEC element names as keys or list of CNEC element names
    CNEs : dict | list | None
        Dictionary containing CNE element names as keys or list of CNE element names, if df is unfiltered. 
        If df is already filtered with CNEs, this parameter can be left out.
    filepathToFolder : str
        The filepath to the folder where CNEC PTDF csv files are located. Default is './ptdf_results'.
    
    Returns
    -------
    DataFrame
        A DataFrame containing PTDFs for all CNEs and CNECs.
    
    """
    cont_dfs={}
    CNECList = []

    if CNEs != None:
        df=filter_df(df,CNEs)

    if isinstance(CNECs,dict):
        for key in CNECs.keys():
            CNECList.append(key)
    else: CNECList=CNECs

    for CNEC in CNECList:
        line, cont = CNEC.split(' cont: ') # split line from contingency in key
        if cont not in cont_dfs.keys():
            df_cont=csv_to_df(f'{filepathToFolder}/PTDF_{cont}.csv') # find and read contingency df
            cont_dfs[cont]=df_cont # add contingecy df with the contingency as key to the dict
        df_filtered = filter_df(cont_dfs[cont], {line: CNECs[CNEC]}) # use filter_df to find CNEC in df
        print (df_filtered) # print filtered df to check that it is correct
        df_filtered.columns.values[0] += f' cont: {cont}' # rename column to include contingency in name
        df=df.join(df_filtered) # add new CNEC to current df by index
    
    return df

def find_largest_PTDF(filepathBaseCase: str, filepathContingencyFolder: str, include: int = 1, exclude: list[str] | dict | None = None) -> pd.DataFrame:
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

    if exclude != None:

        exclude_list = []

        if isinstance(exclude,dict):
            for key in exclude.keys():
                exclude_list.append(key)
        else: exclude_list=exclude

        regex = "|".join(exclude_list)

        df = df.loc[:, ~df.columns.str.contains(regex, na=False)]

    print(df.shape[1])
    
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

def compare_PTDF(filepathBaseCase: str, filepathContingencyFolder: str, include: int = 1, exclude: str = None) -> pd.DataFrame:
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
    df = None
    for name in os.listdir(filepathContingencyFolder):
        cont_name = name.removeprefix('PTDF_').removesuffix('.csv')
        path = os.path.join(filepathContingencyFolder,name)
        df_cont=csv_to_df(path)
        diff = _compare_PTDF(BaseCase_df,df_cont)
        diff.columns = [oldColName + " cont: " + cont_name for oldColName in diff.columns]
        df = pd.concat([df, diff], axis=1)
    

    if exclude != None:
        df = df.loc[:, ~df.columns.str.contains(exclude)]
    
    return _find_largest_PTDF(df, include)

def _compare_PTDF(df1: pd.DataFrame, df2: pd.DataFrame, include: int = 1) -> pd.DataFrame:
    """
    Takes two dataframes and subtracts all the numerical values in the corresponding cells,
    then returns a dataframe including the specified number of columns containing the largest difference.

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


