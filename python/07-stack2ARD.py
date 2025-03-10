"""
2025-03-03 MY

From long to wide (date as columns). One year data.

"""
import glob
import os
import pandas as pd
import numpy as np
import pickle

from pathlib import Path

import argparse
import textwrap
from datetime import datetime


###### FUNCTIONS:

def reshapeAndSave(filepath, outputfile, indexi):  
    
    final = pd.read_pickle(filepath)
    
    # reshape and save data to 3D:
    print(f"\nLength of the data stack dataframe: {len(final)}")

    if final.isna().any().any():
        print(final[final.isna().any(axis=1)])

    # koko kausi:
    parcels = final.parcelID.nunique()
    doys = final['doy'].nunique()

    if final[['parcelID', 'doy']].duplicated(keep = False).any():
        print(f"There are {final[['parcelID', 'band', 'doy']].duplicated(keep = False).sum()} duplicates out of {parcels} parcels. We take the first obs. only.")
        final2 = final.drop_duplicates(subset=['parcelID', 'band', 'doy'], keep='first')
        final = final2.copy()
        print(f"Are there duplicates anymore: {final[['parcelID', 'band', 'doy']].duplicated(keep = False).any()}")

    else:
        print('No duplicates in the data.')

    pivoted1 = final[['parcelID', 'doy', indexi]].pivot(index = 'parcelID', columns = 'doy', values = indexi).reset_index()
    pivoted1['parcelID2'] = pivoted1['parcelID'].str.rsplit('_', n = 1).str[0] # drop 'tile'
    pivoted11 = round(pivoted1.groupby('parcelID2').mean(numeric_only = True).reset_index(), 3)
    pivoted11.rename(columns={'parcelID2': 'parcelID'}, inplace = True)
    print(pivoted11.head())
    
    print(f"Output {indexi} in file: {outputfile}")
    pivoted11.to_csv(outputfile, index = False)
    
    if 'std' in final.columns:
        pivoted2 = final[['parcelID', 'doy', 'std']].pivot(index = 'parcelID', columns = 'doy', values = 'std').reset_index()
        pivoted2['parcelID2'] = pivoted2['parcelID'].str.rsplit('_', n = 1).str[0] # drop 'tile'
        pivoted22 = round(pivoted2.groupby('parcelID2').mean(numeric_only = True).reset_index(), 3)
        pivoted22.rename(columns={'parcelID2': 'parcelID'}, inplace = True)
        print(pivoted22.head())
        
        outputfile2 = outputfile.replace('mean', 'std')
        print(f"Output std in file: {outputfile2}")
        pivoted22.to_csv(outputfile2, index = False)     
        
    else:
        print('Std not found in the data. Check if it should be there. Continue.')
    
    
def main(args):
    
    try:
        if not args.outdir or not args.ylist:
            raise Exception('Missing output dir argument or year. Try --help .')

        print(f'\n\n07-stack2ARD.py')
        print(f'\nInput files in {args.inputdir}')

        # directory for input, i.e. annual results:
        data_folder3 = args.inputdir
        
        # directory for outputs:
        out_dir_path = args.outdir
        Path(out_dir_path).mkdir(parents=True, exist_ok=True)
        
        # years:
        years = args.ylist
        
        #if args.index in ['ndvi']
        
        print("\nPresuming preprocessing done earlier. If not done previously, please, run with 06-stackIndices.py first!")
        
        for year in years:
        
            inputfile = args.index + '_' + year + '.pkl'
            outputfile = args.index + '_mean_' + year + '.csv'
            reshapeAndSave(os.path.join(args.inputdir, inputfile), os.path.join(out_dir_path, outputfile), args.index)
        

                

        # print("\nCombining the years...")
        # TODO
        

    except Exception as e:
        print('\n\nUnable to read input or write out results. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))

    parser.add_argument('-i', '--inputdir',
                        type=str,
                        help='Name of the input directory (where annual dataframes are).',
                        default='.')
    parser.add_argument('-o', '--outdir',
                        type=str,
                        help='Name of the output directory.',
                        default='.')
    parser.add_argument('-y', '--years', action='store', dest='ylist',
                       type=str, nargs='*', default=['2018', '2019', '2020', '2021', '2022', '2023'],
                       help="Optionally e.g. -y 2018 2019, default all")
    
    parser.add_argument('-d', '--index',
                        type=str,
                        help='Name of the index.',
                        default='ndvi')
        
    args = parser.parse_args()
    main(args)


