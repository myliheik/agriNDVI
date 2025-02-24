"""

2020-06-01 MY
2022-11-04 MY for SISA
2024-06-18 cropyield2024
2025-02-24 major update

Usage:
python 01-split-shp-by-tile.py --s2tiles /Users/myliheik/Documents/GISdata/sentinel2_tiles_world/suomiTiles.shp \
--fullshapefile /Users/myliheik/Documents/myNDVI/agriNDVI/shp/parcels-2023.shp  \
--outshpdir /Users/myliheik/Documents/myNDVI/agriNDVI/shp/shpPerTile/ \
--out_file /Users/myliheik/Documents/myNDVI/agriNDVI/shp/parcelIDtile.tsv

Note: this may help if GDAL fails: 
export GDAL_DATA=/Users/myliheik/anaconda3/envs/myGIS/share/gdal

Modified version of Samantha's splitshp.py

"""

import os
from osgeo import osr
import subprocess
import sys

import pandas as pd
import geopandas as gpd

import argparse
import textwrap
import pathlib


def main(args):
    try:
        if not args.fullshapefile or not args.s2tiles:
            raise Exception('Missing shapefile argument. Try --help .')

        print(f'\n\n01-splitshp-shadow.py')
        print(f'\nSentinel2 tiles: {args.s2tiles}')
        print(f'ESRI shapefile parcels: {args.fullshapefile}')
        out_dir_path = pathlib.Path(os.path.expanduser(args.outshpdir))
        out_dir_path.mkdir(parents=True, exist_ok=True)


        out_file = args.out_file


        # filename:
        originalname = os.path.splitext(os.path.split(args.fullshapefile)[-1])[0]



        # Tehdään loput geopandalla:


        parcelshp = gpd.read_file(args.fullshapefile)
        # bring tiles to crs of parcels:
        epsg = str(parcelshp.crs.to_epsg())
        
        print('\n--------')
        print('Read Sentinel-2 tiles...')
        tiles = gpd.read_file(args.s2tiles)
        tilesepsg = str(tiles.crs.to_epsg())

        if tilesepsg == epsg:
            print(f'INFO: input shapefile has EPSG {epsg}, that works!')
        else:
            print(f'Set tile projection to parcel epsg {epsg}...')
            head, tail = os.path.split(args.s2tiles)
            root, ext = os.path.splitext(tail)   

            reprojectedshape = os.path.join(head, root + '_reprojected_' + epsg + ext)
            if not os.path.exists(reprojectedshape):
                reprojectcommand = 'ogr2ogr -t_srs EPSG:' + epsg + ' ' + reprojectedshape + ' ' + myshp
                subprocess.call(reprojectcommand, shell=True)
                
            tiles = gpd.read_file(reprojectedshape)
        
        print('\n--------')
        
        print(f'There are ', len(parcelshp), ' parcels in the input shapefile.')
        
        # for bookkeeping
        df_list = []
        
        for index, row in tiles.iterrows(): # Looping over all tiles
            tilename = row['Name']
            
            # is there any parcels on this tile's BBOX:
            xmin, ymin, xmax, ymax = row['geometry'].bounds
            parcels = parcelshp.cx[xmin:xmax, ymin:ymax]

            if not parcels.empty:
                try:
                    res_intersection = parcels['geometry'].within(row['geometry'])
                    print(f'There are {res_intersection.sum()} parcels in tile {tilename}.')
                    if any(res_intersection):
                        parcelsToFile = parcels[res_intersection]
                        outshpname = os.path.join(args.outshpdir,originalname + '_' + str(tilename)+'.shp')
                        parcelsToFile.crs = '+proj=utm +zone=35 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'
                        parcelsToFile.to_file(outshpname)

                        writeparcels = pd.DataFrame(parcelsToFile['parcelID'])
                        writeparcels['Tile'] =  tilename
                        #print(writeparcels)
                        #writeparcels.to_csv(out_file, mode='a', header=False)

                        df_list.append(writeparcels) 
                        
                except Exception as ee:
                    print(f'\n\nSome error in reading parcels in {tilename}. Continue to next tile...')
                    continue
        
        df_list_mapped = list(map(lambda df: df, df_list)) 
        combined_df = pd.concat(df_list_mapped, ignore_index = True)
        print(f'Intersecting parcelIDs and tiles saved to {out_file}')
        combined_df.to_csv(out_file, sep = '\t', index = False)

        print(f'\nDone.')

    except Exception as e:
        print('\n\nUnable to read input or write out files. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))
    parser.add_argument('-s', '--s2tiles',
                        type=str,
                        help='Sentinel-2 tiles.')
    parser.add_argument('-a', '--fullshapefile',
                        type=str,
                        help='ESRI shapefile containing a set of polygons (.shp with its auxiliary files)')
    parser.add_argument('-d', '--outshpdir',
                        help='Directory for output shp files',
                        type=str,
                        default='.')
    parser.add_argument('-o', '--out_file',
                    help='Output (e.g. .tsv) tab-separated file containing parcelID and the tile it was found at.',
                    type=str,
                    default='parcelIDtile.tsv')

    args = parser.parse_args()
    main(args)
    