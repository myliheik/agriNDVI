"""
2025-02-25 MY


RUN: python 04-calculateIndex.py -i input -o output -b NDVI 

WHERE:
-i input: array reads
-o output: optional output dir
-b index: name of the index to calculate, e.g. NDVI


"""



import os
import numpy as np
import sys
import csv
import os

import argparse
import textwrap
import pathlib

            
def to_csv(csvfile, myarray, vindex):

    csvfile = csvfile.replace('array_', str.lower(vindex) + '_')
    #print(f'Saving results to {csvfile}')
    
    #with open(csvfile, "w") as f:
    with open(csvfile, "w", newline='') as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerows(myarray)


def main(args):
    try:
        if not args.inputpath or not args.vindex:
            raise Exception('Missing input dir argument or index (e.g. NDVI). Try --help .')

        print(f'\n\n04-calculateIndex.py')
        print(f'\nInput files in {args.inputpath}')
        print(f'Index: {args.vindex}')
        datadir = args.inputpath
        vindex = args.vindex

        if args.outdir:
            out_dir_path = pathlib.Path(os.path.expanduser(args.outdir))
        else:
            out_dir_path = pathlib.Path(datadir.replace('results_', vindex + '_'))
        out_dir_path.mkdir(parents=True, exist_ok=True)


        if vindex == 'NDVI':
            band04 = 'B04'
            band08 = 'B08'
        else:
            print(f'Formula for {vindex} not known!')
        
        #print('Reading arrayfiles...')

        files = [f for f in os.listdir(datadir) if f.endswith(band04 + '.csv')]

        for arrayfile in files:
            
            if arrayfile.startswith('array_'):
                band08filepath = arrayfile.replace(band04, band08)
                #print(arrayfile, band08filepath)
                results = []
                arraypath04 = os.path.join(datadir, arrayfile)
                arraypath08 = os.path.join(datadir, band08filepath)
 
                outputpath = os.path.join(out_dir_path, arrayfile)

                if os.path.isfile(arraypath08):
            
                    with open(arraypath04, "r") as file04, open(arraypath08, 'r') as file08:
                        reader04 = csv.reader(file04)
                        reader08 = csv.reader(file08)

                        for line in reader04:
                            #print(line)

                            myid = [line[0]]
                            #print(myid[0])

                            #if myid:
                            RED = np.array([int(elem) for elem in line if not '_' in elem])
                            #print(RED)

                            # Find band08 values:
                            for line08 in reader08:
                                #print(line08[0])

                                if line08[0] == myid[0]:
                                    NIR = np.array([int(elem) for elem in line08 if not '_' in elem])
                                    #print(NIR)
                                    if len(RED) == len(NIR):
                                        #print(f'Length of RED and NIR values match.\nReady to calculate NDVI!')
                                        NDVI = (NIR - RED) / (NIR + RED)
                                        NDVIstats = [np.round(np.mean(NDVI), 3), np.round(np.std(NDVI), 3)]
                                        #print(NDVIstats)
                                    else:
                                        print(f'Length of RED and NIR values do not match! We take the next.')

                                    break
                                else:
                                    continue


                            myid.extend(NDVIstats)
                            #print(myid)
                            results0 = myid

                            results.append(results0)
                    to_csv(outputpath, results, vindex)
                    
                else:
                    print(f'File {arraypath08} does not exit! We take the next.')
                    continue


                    
                    
    except Exception as e:
        print('\n\nUnable to read input or write out results. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))
    parser.add_argument('-i', '--inputpath',
                        type=str,
                        help='Path to the directory with array csv files.',
                        default='.')
    parser.add_argument('-b', '--vindex',
                        help='Name of the index, e.g. NDVI',
                        type=str)
    parser.add_argument('-o', '--outdir',
                        type=str,
                        help='Name of the output directory. Optional.',
                        )

    args = parser.parse_args()
    main(args)
