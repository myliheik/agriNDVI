"""
MY 2022-10-12

safefinder creates paths to all files between start- and enddate 

17.8.2021 MY modified from pathfinder.py to find safe dirs
5.1.2023 MY modified: only if filename *.SAFE continue (other files are not interrupting no more)

RUN:
python 02-safefinder.py -s 20230501 -e 20230831  -d /scratch/project_2013001/Sentinel2

"""
import os
import userinput

import argparse
import textwrap
import pathlib


        
def makesafepaths(datadir, startdate, enddate):

    tilepath = datadir
    filepaths = []
    
    for filename in os.listdir(tilepath):
        if '.SAFE' in filename:
            date = filename.split('_')[2].split('T')[0]
            if not enddate is None and not startdate is None:
                if date <= enddate and date >= startdate:
                    filepath = os.path.join(tilepath,filename)
                    filepaths.append(filepath)
            else:
                filepath = os.path.join(tilepath,filename)
                filepaths.append(filepath)
        else:
            continue
    
    to_txt(filepaths)
            
def to_txt(paths):

    with open('../bin/safepaths.txt', 'w') as f:
        for item in paths:
            f.write("%s\n" % item)

        
def main(args):
    try:
        if not args.datapath:
            raise Exception('Missing input dir argument. Try --help .')

        print(f'\n\n02-safefinder.py')
        print(f'\n\nLists all SAFE directories within the start and end date.\n Writes the list to ../bin/safepaths.txt.')

        makesafepaths(args.datapath, args.startdate, args.enddate)
        
    except Exception as e:
        print('\n\nUnable to read input or write out files. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e

        
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))
    parser.add_argument('-d', '--datapath',
                        type=str,
                        help='Directory path to safe directories')
    parser.add_argument('-s', '--startdate',
                        type=str,
                        help='Start date, e.g. 20200501')
    parser.add_argument('-e', '--enddate',
                        help='End date, e.g. 20200901',
                        type=str,
                        default='.')

    args = parser.parse_args()
    main(args)
