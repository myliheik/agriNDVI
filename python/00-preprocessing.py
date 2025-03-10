"""
@author: MY

For creating field parcel sets from IACS parcel data (kasvulohkodata). AOI is determined by Sentinel-2 tiles.


Filterit: 

1) Filter out broken typologies -> None

2) Filteröidään pois lohkot alle FILTERED_OUT eli oletuksena 0.2ha.


***

After this run: 01-splitshp.py etc.


RUN:

python 00-preprocessing.py -i /Users/myliheik/Documents/GISdata/Kasvulohkot2023/Kasvulohkot2023.gpkg \
-s /Users/myliheik/Documents/GISdata/sentinel2_tiles_world/suomiTiles.shp \
-t VEM VEN VFM VFN VER VEQ VFR VFQ \
-o /Users/myliheik/Documents/myNDVI/agriNDVI/shp -g 0.2

python 00-preprocessing.py -i /Users/myliheik/Documents/GISdata/Kasvulohkot2022/kasvulohkot2022-mod.shp \
-s /Users/myliheik/Documents/GISdata/sentinel2_tiles_world/suomiTiles.shp \
-t VEM VEN VFM VFN VER VEQ VFR VFQ \
-o /Users/myliheik/Documents/myNDVI/agriNDVI/shp -g 0.2

python 00-preprocessing.py -i /Users/myliheik/Documents/GISdata/Kasvulohkot2021/kasvulohkot2021-mod.shp \
-s /Users/myliheik/Documents/GISdata/sentinel2_tiles_world/suomiTiles.shp \
-t VEM VEN VFM VFN VER VEQ VFR VFQ \
-o /Users/myliheik/Documents/myNDVI/agriNDVI/shp -g 0.2

python 00-preprocessing.py -i /Users/myliheik/Documents/GISdata/Kasvulohkot2020/kasvulohkot2020-mod.shp \
-s /Users/myliheik/Documents/GISdata/sentinel2_tiles_world/suomiTiles.shp \
-t VEM VEN VFM VFN VER VEQ VFR VFQ \
-o /Users/myliheik/Documents/myNDVI/agriNDVI/shp -g 0.2

"""


import pandas as pd
import geopandas as gpd
import numpy as np
import os.path
from pathlib import Path
import argparse
import textwrap
import math
import pickle
import warnings
warnings.filterwarnings("ignore")

excludedCrops0 = [9620, 9700, 9710, 5181, 5182, 5183, 5184, 5185, 5186, 5187, 5199, 9402, 9430, 9600, 9610, 9810, 9820,
5451, 5304, 5310, 5535, 5536, 5537, 5213, 5313, 5210, 5211, 5314, 5221, 5400, 5410, 5420, 5436, 5305, 5300, 5301, 5302, 5303, 5307, 4910, 4911, 4912, 5442, 5443, 8032, 8034, 8035, 8036, 5500, 5510, 5511, 5512, 5520, 5530,
6060, 4900, 4901, 4902, 4903, 5315, 6300, 6301, 6302, 5198, 6400, 8045, 5220, 8002, 8003, 8031, 9200, 9300, 9301, 9310, 9311, 9312, 5531, 5532, 5533, 5534, 7110, 7210, 8001, 9410, 6600, 6700, 6710, 6720, 9804, 9100, 9101, 9102, 9110, 9111]

excludedCrops = list(map(str, excludedCrops0))


with open('/Users/myliheik/Documents/myCROPMAPPING/data/kasviDict.pkl', 'rb') as fp:
    kasviDict = pickle.load(fp)
    

def readLPIS(fpkasvu, FILTERED_OUT):
    kasvulohko = gpd.read_file(fpkasvu)
    print(kasvulohko.columns)
    kasvulohko.rename(columns={"PLVUOSI_PERUSLOHKOTUNNUS": "PLOHKO", "KVI_KASVIKOODI": "KASVIKOODI", "KVI_KASVIK": "KASVIKOODI", "MAATILA_TUNNUS": "MAATILA_TU", "KLILM_TUNN": "KLILM_TUNNUS", "PLVUOSI_PE": "PLOHKO"
                              }, inplace=True)

    year = str(kasvulohko['VUOSI'][0])
    projection = kasvulohko.crs
    
    print(f'The total number of parcels: {len(kasvulohko)}')
    
    kasvulohko00 = kasvulohko[~kasvulohko.geometry.isna()].copy()
    kasvulohko0 = kasvulohko00[~kasvulohko00['KASVIKOODI'].isna()]
    
    if len(kasvulohko) - len(kasvulohko00) > 0:
        print(f'There were {len(kasvulohko) - len(kasvulohko00)} nas in parcel geometries! Excluded now.')
        
    kasvulohko0['P_ALA_HA'] = round(kasvulohko0.area/10000, 2)
 
    print(f'The mean area of parcels: {kasvulohko0["P_ALA_HA"].mean()}')
    
    row_mask = kasvulohko0.KASVIKOODI.isin(excludedCrops)
    filtered0 = kasvulohko0[~row_mask]
    
    #Filter out parcels < FILTERED_OUT
    filtered1 = filtered0[filtered0["P_ALA_HA"] > FILTERED_OUT].copy()

    print(f'LPIS was filtered by area (< {FILTERED_OUT} ha) and obsolete crop types. {len(filtered1)} parcels remains.')
    
    # drop broken typologies:
    row_mask2 = filtered1.geometry.is_valid
    filtered3 = filtered1[row_mask2]

    filtered3 = filtered3.rename(columns={'MAATILA_TU': 'farm_ID', 'KASVIKOODI': 'plant_ID'}).copy()
    print(f'Broken typologies were checked. {len(filtered3)} parcels remains.')
    
    filtered3['perimeter'] = filtered3.length.round(0)
    
    filtered3['parcelID'] = filtered3['KLILM_TUNNUS'].apply(lambda x: "{}{}{}".format(year,'_', x)) + '_' + filtered3['PLOHKO'].astype(str) + '_' + filtered3['plant_ID'].astype(str)
    
    print('\n--------')
    #print(f"The share of crop types in the data, by area and by number: \n{pd.concat([tmpala, tmpnr, alatotos, tmpnrkaikki, alatiacs], axis = 1)}")
    
    return filtered3, year, projection

def filterByTiles(kasvulohkot, shpfile, tiles):
    epsg = kasvulohkot.crs.to_epsg()
    print('\n--------')
    print('Read Sentinel-2 tiles...')
    gdf = gpd.read_file(shpfile)
    print(f'Set projection to Finnish epsg {epsg}...')
    gdfTiles = gdf.to_crs(epsg) 
    
    # only save parcelIDs:
    parcels = []
    
    for tile in tiles:
        print(f'{tile}')
        xmin, ymin, xmax, ymax = gdfTiles[gdfTiles['Name'].str.endswith(tile)].total_bounds
    
        print(xmin, ymin, xmax, ymax)
        kasvulohkot_clipped = kasvulohkot.cx[xmin:xmax, ymin:ymax]
        parcels.extend(kasvulohkot_clipped['parcelID'])

    
    kasvulohkot2 = kasvulohkot[kasvulohkot['parcelID'].isin(list(set(parcels)))]

    print(f'Found {len(kasvulohkot2)} parcels in tiles {tiles}.')
   
    return kasvulohkot2


def savingParcels(kasvulohkot, out_dir_path, year):
    
    outputfile = os.path.join(out_dir_path, 'parcels-' + str(year) + '.shp')  
    outputfile2 = os.path.join(out_dir_path, 'parcels-' + str(year) + '.csv')  

    print(f'Saving geometries to {outputfile}')           
    kasvulohkot[['parcelID', 'geometry']].to_file(driver = 'ESRI Shapefile', filename = outputfile)
    
    print(f'Saving metafiles to {outputfile2}') 
    # append plant name:    
    kasvulohkot['plant_name'] = kasvulohkot['plant_ID'].map(kasviDict)    
    kasvulohkot.drop(columns = ['geometry']).to_csv(outputfile2, index = False)

    print('ParcelID is in format: YEAR_kasvulohkoID_peruslohkoID_CROPTYPE. Area is in hectares.')
    
    
# HERE STARTS MAIN:

def main(args):
    try:
        if not args.inputpath:
            raise Exception('Missing input filepath argument. Try --help .')

        print(f'\n00-preprecessing.py')
        print(f'\nLPIS data in: {args.inputpath}')
        
        # directory for output:
        out_dir_path = args.outputshppath
        Path(out_dir_path).mkdir(parents=True, exist_ok=True)
        
        # READ LPIS, filter out too small parcels and select only relevant crop types:
        kasvulohkot, year, projection = readLPIS(args.inputpath, args.filter)
        print(kasvulohkot.head())


        kasvulohkot = filterByTiles(kasvulohkot, args.shpfile, args.tiles)
        print(kasvulohkot.head())

        # Saving:  
        savingParcels(kasvulohkot, out_dir_path, year)
        
        print(f'\nDone.')

    except Exception as e:
        print('\n\nUnable to read input or write out. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))
    parser.add_argument('-i', '--inputpath',
                        help='Parcel geometries (LPIS)',
                        type=str)  
    parser.add_argument('-s', '--shpfile',
                        help='Filepath to Sentinel-2 tiles.',
                        type=str)  
    parser.add_argument('-t', '--tiles', action='store', dest='tiles',
                         type=str, nargs='*', default = ['VER', 'VEQ', 'VFR', 'VFQ', 'VEM', 'VEN', 'VFM', 'VFN'],
                         help='List of Sentinel-2 tiles. Can be multiple. E.g. -t VER VEQ.')
    parser.add_argument('-o', '--outputshppath',
                        help='Directory to save parcel geometries.',
                        type=str)  
    parser.add_argument('-g', '--filter',
                        help='Filter out parcels < threshold.',
                        default = 0.2,
                        type=float)   
    parser.add_argument('--debug',
                        help='Verbose output for debugging.',
                        action='store_true')

    args = parser.parse_args()
    main(args)
