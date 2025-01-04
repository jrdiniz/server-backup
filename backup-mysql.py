import os
import gzip
import shutil
import subprocess
import datetime
import logging
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()

# Determine full logging file path
abspath = os.path.abspath(os.path.dirname(__file__))

# Logging
logging.basicConfig(filename=f'{abspath}/server-backup.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)

def main():
    # MySQL Credentials
    mysql_address = os.getenv("MYSQL_ADDRESS")
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    
    # Logging starting mysql backup script
    logging.info('Starting mysql backup script')
    
    # Backup file name
    timestamp = datetime.datetime.now().strftime('%d%m%Y_%H%M')
    
    # Get a list of all databases using subprocess and mysql
    databases = subprocess.check_output(f"mysql -h {mysql_address} -u {mysql_user} -p{mysql_password} -e 'show databases;' | grep -Ev 'Database|information_schema|performance_schema|mysql|sys'", shell=True).decode('utf-8').split()
    
    # Execute backup for each database
    for database in databases:
        database = database.strip()
        backup_file = f'{database}_{str(timestamp)}.sql'
        
        # Logging create backup from database
        logging.info(f'Creating backup file for database: {database}')

        # Create backup file using subprocess and mysqldump
        subprocess.call(f"mysqldump -h {mysql_address} -u {mysql_user} -p{mysql_password} {database} > {backup_file}", shell=True)
        
        # Compress dump with gzip
        gzip_compress_file(backup_file, f'{backup_file}.gz')
        
        # Logging remove dump .sql
        logging.info(f'Removing dump file {backup_file}')
        
        # Uplaod to S3
        if upload_to_s3(f'{backup_file}.gz', 'db', f'{database}_{str(timestamp)}.sql.gz'):
            # Remove dump .sql
            os.remove(backup_file)
            
            # Logging backup file for database created
            logging.info(f'Backup file for database {database} created, dump file {backup_file}.')
            
            # Remove local backup that was create
            os.remove(f'{backup_file}.gz')
            
            # Logging backup file for database removed
            logging.info(f'Local backup file for database {database} removed, dump file {backup_file}.')
        else:
            # Logging error in upload
            logging.error(f'Error in upload file {backup_file}.')
            
            # Logging local backup file for database not removed
            logging.info(f'Local backup file for database {database} not removed, dump file {backup_file}.')
            
    
def gzip_compress_file(input_file, output_file):
    with open(input_file, 'rb') as f_in:
        with gzip.open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            
            
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
    
if __name__ == "__main__":
    main()