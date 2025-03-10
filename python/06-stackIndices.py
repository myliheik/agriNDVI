"""
26.2.2025 MY

Make ndvi files into annual dataframes. Saves into outputdir_annuals.



getAttributesFromFilename() adds tile-, DOY ja band information from filename to data.

mergeAllGetNumpyArrays() makes one big dataframe for one year. Save to outputdir_annuals.

testing(outputfile) tests if output file is ok.

RUN: 

python 06-stackIndices.py -i /scratch/project_2013001/agriNDVI/cloudless/NDVI_2023/ -t TEMPDIRPATH

WHERE:
-i input: input dir
-o output: output dir
-b index: name of the index to calculate, e.g. NDVI


After this into stack2ARD.py.

In Puhti: module load geopandas (Python 3.8.) and also: pip install 'pandas==1.1.2' --user

"""

import os
import pandas as pd
import numpy as np
import pickle

from pathlib import Path

import argparse
import textwrap
from datetime import datetime


###### FUNCTIONS:

def load_intensities(filename):
    with open(filename, "rb") as f:
        data = pickle.load(f)
    return data

def save_intensities(filename, arrayvalues):
    with open(filename, 'wb+') as outputfile:
        pickle.dump(arrayvalues, outputfile)

def createMissingFiles(datadir):
    # List all files
    list_of_files = os.listdir(datadir)

    # median_35VNL_20200830_B8A.csv
    # This removes the .csv and splits the name to three parts
    list_of_filename_parts = [i.replace(".csv","").split("_") for i in list_of_files]
    
    # Makes a df of all filenames
    df = pd.DataFrame(list_of_filename_parts, columns=['histo','tile','date','band'])
    #print(df.head())

    # Group and iterate by date, see if bands are missing
    grouped_df = df.groupby(['date', 'tile'])

    # Bands as text that should exist
    bands = ['B02','B03','B04','B05','B06','B07','B08','B8A','B11','B12']
    
    # Iterate
    for name, date_group in grouped_df:
        #print(name[1])
        existing_bands = list(date_group['band'])
        for band in bands:
            if band not in existing_bands:
              	# Band is missing create a mockup dataframe and save
                print(f"For date {name} band {band} is missing!")

                ### Copy from existing band, same date, set all values to 0 (or np.nan)
                
                temp_filename = os.path.join(datadir,"median_" + name[1] + "_" + name[0] + "_" + existing_bands[0] + ".csv")
                #print(temp_filename)
                dftemp = pd.read_csv(temp_filename, encoding='utf-8', header = None)
                #print(dftemp.iloc[:, 1:])
                dftemp.iloc[:,1:] = 0
                #print(dftemp)

                output_filename = os.path.join(datadir,"median_" + name[1] + "_" + name[0] + "_" + band + ".csv")
                print(f"Saving a new file named {output_filename}")
                dftemp.to_csv(output_filename,encoding='utf-8',index=False, header=False)

def getAttributesFromFilename(datadir, data_folder2, vindex):
    ### Add date and band to every file as columns

    # Loop files in data_folder
    for filename in os.listdir(datadir):
        if filename.endswith('.csv') and filename.startswith(str.lower(vindex) + '_'):
            #print(filename)
            try:
                df = pd.read_csv(os.path.join(datadir,filename), encoding='utf-8', header = None)
            except pd.errors.EmptyDataError:
                print(f'{os.path.join(datadir,filename)} was empty. Skipping.')
                continue
            # Add tile, band and date from filename to columns
            df['tile'] = filename.split("_")[1]
            pvm = filename.split("_")[2]
            df['doy'] = datetime.strptime(pvm, '%Y%m%d').timetuple().tm_yday
            #print(doy)
            df['band'] = filename.split("_")[3].replace(".csv","")
            #print(band)
            #print(df)
            ### Write to data_folder2
            df.to_csv(os.path.join(data_folder2, filename), encoding='utf-8',index=False, header=False)
            
        
            
            
def mergeAllGetNumpyArrays(data_folder2, data_folder3, outputfile):
    ### Merge all files to one big dataframe

    df_array = []

    ### Read files to pandas, add the dataframes to the array
    for filename in os.listdir(data_folder2):
        df = pd.read_csv(os.path.join(data_folder2,filename), encoding="utf-8", header=None)
        df.rename(columns={0: 'parcel_ID', 4: 'doy', 3: 'tile', 2: 'std', 1: 'ndvi'}, inplace=True)

        try:
            df['parcelID'] = df['parcel_ID'] + '_' + df['tile']
        except Exception as e:
            print(f'\n\nThere is something wrong with file {os.path.join(data_folder2,filename)}...')
            print('Check that you have set the right number of bins!')
            raise e
            
        #print(df)   
        
        df = df[['parcelID', 'doy', 'ndvi', 'std', 'tile']]
        df_array.append(df)

    ### Make a big dataframe out of the list of dataframes
    all_files_df = pd.concat(df_array)
    ### And save to temp:
    save_intensities(os.path.join(data_folder3,outputfile), all_files_df)
    
    return all_files_df

def addDOYrank(all_files_df, out_dir_path, outputfile):
    #print(all_files_df.head())
    days = all_files_df.doy.sort_values().unique()
    days_dict = dict(zip(days, range(len(days))))
    #print(days_dict)
    all_files_df2 = all_files_df
    return all_files_df2
    
def testing(all_files_df, out_dir_path, outputfile):
    print("Output written to file: ", outputfile)
    #print(all_files_df.head())
    tmp2 = all_files_df.groupby(['doy', 'parcelID']).count()#.unstack().fillna(0)

    # kuinka monta tilaa mukana?
    print("How many parcels are observed from one or several S2 granules?:", len(all_files_df[['parcelID']].drop_duplicates()))
    
    # kuinka monta tilaa mukana oikeasti?
    parcelIDs = all_files_df['parcelID'].str.rsplit('_', n = 1).str[0] # drop 'tile'
    #print(parcelIDs)
    #print(len(parcelIDs))
    #print(all_files_df[['parcelID', 'doy']].drop_duplicates())
    
    print("How many parcels we really have?: ", len(parcelIDs.drop_duplicates()))
        
    # Kuinka monta havaintoa per tila koko kesältä, mediaani?
    print("How many observations per parcel in one season (median)?: ", float(all_files_df[['parcelID', 'doy']].drop_duplicates().groupby(['parcelID']).count().median()))

    # kuinka monta havaintoa per päivä, mediaani?
    print("How many observations per day (median)?: ", float(all_files_df[['parcelID', 'doy']].drop_duplicates().groupby(['doy']).count().median()))

              
def main(args):
    
    try:
        if not args.inputpath:
            raise Exception('Missing input or output dir argument. Try --help .')

        print(f'\n\n06-stackIndices.py')
        print(f'\nInput files in {args.inputpath}')


        datadir = args.inputpath
        
        # grep index and year from inputpath
        head, tail = os.path.split(Path(datadir))
        vindex = tail.split("_")[0]
        year = tail.split("_")[1]
        outputfile = str.lower(vindex) + '_' + year + '.pkl'

        if not args.outdir:
            out_dir_path = Path(os.path.join(head, 'dataStack'))
        else:
            out_dir_path = Path(os.path.expanduser(args.outdir))
        out_dir_path.mkdir(parents=True, exist_ok=True)
        
        
        bins = 1 # vain yksi feature eli index

        # temp directory for annual medians:
        data_folder2 = args.tmpdir
        Path(data_folder2).mkdir(parents=True, exist_ok=True)

        # directory for annual dataframes:
        data_folder3 = os.path.join(head, 'dataStack_annual')
        Path(data_folder3).mkdir(parents=True, exist_ok=True)


        #createMissingFiles(datadir)
        getAttributesFromFilename(datadir, data_folder2, vindex)
        
        # tämä tekee jo varsinaisen osuuden:
        all_files_df = mergeAllGetNumpyArrays(data_folder2, data_folder3, outputfile) 
        
        # loput on testausta:
        all_files_df = load_intensities(os.path.join(data_folder3,outputfile))
        #all_files_df = addDOYrank(all_files_df, out_dir_path, outputfile)
        testing(all_files_df, out_dir_path, os.path.join(data_folder3,outputfile))


    except Exception as e:
        print('\n\nUnable to read input or write out results. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))
    parser.add_argument('-i', '--inputpath',
                        type=str,
                        help='Path to the directory with index csv files.',
                        default='.')

    parser.add_argument('-o', '--outdir',
                        type=str,
                        help='Name of the output directory. Optional',
                        default=None)

    parser.add_argument('-t', '--tmpdir',
                        type=str,
                        help='Name of the temp directory.',
                        default='.')
    args = parser.parse_args()
    main(args)


