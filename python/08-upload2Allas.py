"""
2025-03-04 MY

RUN:
python 08-upload2Allas.py -i /scratch/project_2013001/agriNDVI/cloudless/dataStack/ndvi_mean_2023.csv -b agriNDVI
python 08-upload2Allas.py -i /scratch/project_2013001/agriNDVI/cloudless/dataStack/ndvi_std_2023.csv -b agriNDVI



# initializing:
module load allas
allas-conf --mode s3cmd
s3cmd mb s3://agriNDVI

"""

import os.path

import argparse
import textwrap

import boto3


# HERE STARTS MAIN:

def main(args):
    try:
        if not args.inputpath:
            raise Exception('Missing input filepath argument. Try --help .')

        print(f'\n08-upload2Allas.py')
        print(f'\nFile to upload in: {args.inputpath}')
        print(f'\nSaved in s3 bucket: {args.bucketname}')

        s3_resource = boto3.resource('s3', endpoint_url='https://a3s.fi')
        my_bucketname = args.bucketname
        
        fp = args.inputpath
        head, tail = os.path.split(fp)
        boto3file = tail        
        
        print(f'\nRead the file {fp}...')

                
        # boto3:               
        print(f'Saving {boto3file} into Allas bucket {my_bucketname}')
        s3_resource.Object(my_bucketname, boto3file).upload_file(fp, ExtraArgs={'ACL':'public-read'})
                
                


        # If you want to see the list of Allas files:
        print(f'My files in Allas {my_bucketname}:')

        my_bucket = s3_resource.Bucket(my_bucketname)

        for my_bucket_object in my_bucket.objects.all():
            print(my_bucket_object.key)

        print(f'\nDone.')

    except Exception as e:
        print('\n\nUnable to read input or write out statistics. Check prerequisites and see exception output below.')
        parser.print_help()
        raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=textwrap.dedent(__doc__))

    parser.add_argument('-i', '--inputpath',
                        help='Filepath of predictions.',
                        type=str)
    parser.add_argument('-b', '--bucketname',
                        help='Give a name of an existing bucket in S3.',
                        type=str)

    args = parser.parse_args()
    main(args)
