import pandas as pd

def change_df_index_name(df): # Change index name to areas, only called inside csv_to_df function

    df.index =  ['Area:','Crownlands', 'Dorne', 'Essos', 'Iron Islands', 'North', 'Reach',
                    'Riverlands', 'Stormlands', 'Vale', 'Westerlands']

def csv_to_df(csvFile,sep=','):
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
    change_df_index_name(df)

    df=df.iloc[:,2:]
    
    var = ['Branch Sensitivity dPbranch/dPbus/HV-Side','Branch Sensitivity dPbranch/dPbus/Terminal i']

    regex2="|".join(var)

    mask = df.iloc[0].str.contains(regex2, na=False)

    filtered = df.loc[:, mask]

    return filtered

def filter_df(df: pd.DataFrame,CNEs: dict) -> pd.DataFrame:
    """
    Take CSVfile of PTDFs and dict of CNEs and return PTDFS for given CNEs

    Parameters
    ----------
    df : DataFrame
        dataframe
    CNEs : dict
        Dictionary containing CNE element names as keys

    Returns
    -------
    DataFrame
    """

    CNEList = []

    for key in CNEs.keys():
        CNEList.append(key) 

    regex = "|".join(CNEList)   

    filtered_df = df.filter(regex=regex)
    
    return filtered_df

def find_largest_ptdf(df: pd.DataFrame, include: int = 1) -> pd.DataFrame:
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



def compare_ptdf(df1: pd.DataFrame, df2: pd.DataFrame, include: int = 1) -> pd.DataFrame:
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

    # --- REMOVE METADATA ---
    num1 = df1.iloc[1:, :]   # rows 1:end, all columns
    num2 = df2.iloc[1:, :]

    # Convert to numeric safely
    num1 = num1.apply(pd.to_numeric, errors="coerce") 
    num2 = num2.apply(pd.to_numeric, errors="coerce")

    # Drop columns that contain no numeric data
    num1 = num1.dropna(axis=1, how="all")
    num2 = num2.dropna(axis=1, how="all")

    # Align again after cleanup
    num1, num2 = num1.align(num2, join="inner", axis=1)

    if num1.shape[1] == 0:
        raise ValueError("No common PTDF columns to compare.")

    # --- COMPUTE DIFFERENCE ---
    diff = (num1 - num2).abs()

    col_max = diff.max()

    # Sort columns by their max values descending
    top_cols = col_max.sort_values(ascending=False).index[:include]

    # Keep only top columns from original DataFrame (including metadata row/cols)
    # Adjust index offset for the first two metadata columns
    top_cols_full = [diff.columns[ diff.iloc[1:,:].columns.get_loc(c)] for c in top_cols]

    # Return new DataFrame with all rows but only the top columns
    return diff.loc[:, top_cols_full].fillna('----')
