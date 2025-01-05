import os
import logging
import datetime
import boto3
import tarfile
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()

# Determine full logging file path
abspath = os.path.abspath(os.path.dirname(__file__))

# Logging
logging.basicConfig(filename=f'{abspath}/server-backup.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)


def main():
    webpoint_root_directory = os.getenv("WEBPOINT_ROOT_DIRECTORY")
    
    # Logging starting webpoint backup script
    logging.info('Starting webpoint backup script')
    
    # Get a list of directories in the webpoint root directory
    webpoints = os.listdir(webpoint_root_directory)
    
    # Get a list of directories to ignore
    ignore_list = os.getenv("WEBPOINT_IGNORE_LIST").split(',')
    
    for webpoint in webpoints:
        # Logging starting webpoint backup script
        logging.info(f'Starting webpoint backup script for {webpoint}')
        
        # Backup file name
        timestamp = datetime.datetime.now().strftime('%d%m%Y_%H%M')
        
        # Check it ignore list directories exist in the webpoint directory
        ignore_list = [os.path.join(webpoint_root_directory, webpoint, ignore) for ignore in ignore_list if os.path.exists(os.path.join(webpoint_root_directory, webpoint, ignore))]
        
        # Create backup file using tar
        create_tarfile(f'{webpoint_root_directory}/{webpoint}', f'{webpoint}_{str(timestamp)}.tar.gz', ignore_list)
        
        # Uplaod to S3
        if upload_to_s3(f'{webpoint}_{str(timestamp)}.tar.gz', 'webpoint', f'{webpoint}_{str(timestamp)}.tar.gz'):
            # Logging backup file for webpoint created
            logging.info(f'Backup file for webpoint {webpoint} created, dump file {webpoint}_{str(timestamp)}.')
            
            # Remove local backup that was create
            os.remove(f'{webpoint}_{str(timestamp)}.tar.gz')
    
def create_tarfile(input_directory, output_filename, ignore_list=None):
    with tarfile.open(output_filename, "w:gz") as tar:
        for root, dirs, files in os.walk(input_directory):
            # Remove directories to ignore from the list of directories to walk
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in ignore_list]
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=input_directory)
                tar.add(file_path, arcname=arcname)

def upload_to_s3(local_file, subdirectory, s3_file):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        endpoint_url=os.environ.get('AWS_ENDPOINT_URL'),
        region_name='auto'
    )
    try:
        s3.upload_file(local_file, os.environ.get('AWS_BUCKET_NAME'), f"{subdirectory}/{s3_file}")
        # Logging Upload Successful
        logging.info(f'Upload Successful: {local_file} to {os.environ.get("AWS_BUCKET_NAME")}/{subdirectory}/{s3_file}')
        return True
    except FileNotFoundError:
        # Logging File not found
        logging.error(f'The file was not found: {local_file}')
        return False
    except NoCredentialsError:
        # Logging Credentials not available
        logging.error('Credentials not available')
        return False
    except PartialCredentialsError:
        # Logging Incomplete credentials provided
        logging.error('Incomplete credentials provided')
        return False
    except Exception as e:
        # Logging Error
        logging.error(f'Error: {str(e)}')
        return False


if __name__ == '__main__':
    main()