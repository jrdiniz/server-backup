#!/usr/bin/python3
import boto3 
import os 
import tarfile
import time
import gzip
import datetime
import subprocess
import time
import click
import shutil
import logging
from dotenv import load_dotenv
from botocore.client import Config

# Globals
timestamp = datetime.datetime.now().strftime('%m%d%Y_%H%M')

# Working Directory
os.chdir(os.path.abspath(os.path.dirname(__file__)))

# Logging
logging.basicConfig(filename='wordpress-server-backup.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)

class Backup(object):
    def __init__(self):
        abspath = os.path.abspath(os.path.dirname(__file__))
        if os.path.isfile(os.path.join(abspath,'.env')):
            load_dotenv()

            # Bucket Credentials
            self.access_id = os.getenv("ACCESS_ID")
            self.secret_key = os.getenv("SECRET_KEY")
            self.region_name = os.getenv("REGION_NAME")
            self.endpoint_url = os.getenv("ENDPOINT_URL")
            self.bucket_name = os.getenv("BUCKET_NAME")
            self.bucket_directory = os.getenv("BUCKET_DIRECTORY")
    
            # MySQL Credentials
            self.mysql_address = os.getenv("MYSQL_ADDRESS")
            self.mysql_user = os.getenv("MYSQL_USER")
            self.mysql_password = os.getenv("MYSQL_PASSWORD")
            
        else:
            self._configure()

    def site(self, directory, retention):
        if os.path.exists(directory):
            # Backup file name
            filename = directory.split("/")[-1]
            backup_file = filename + '_' + str(timestamp) + '.tar.gz'

            # Create backup file using subprocess and tar
            logging.info(f'Creating backup file: {backup_file}')
            subprocess.call(f"tar -zcf {backup_file} {directory}", shell=True)
            
            # Send to bucket
            self._send_to_bucket(
                directory=f"{self.bucket_directory}/site",
                filename=f"{backup_file}"
            )
            # Remove local backup that was create
            logging.info(f'Removing local backup file {backup_file}')
            os.remove(backup_file)
            logging.info('Backup finished.')

            # Remove old backups
            self._retention(
                directory=f"{self.bucket_directory}/site",
                filename=filename,
                retention=retention
            )


    def database(self, retention):
        databases = subprocess.Popen(['mysql', '-u', self.mysql_user, '-h', self.mysql_address, f'-p{self.mysql_password}', '-Bse', 'show databases'], stdout=subprocess.PIPE)
        for database in databases.stdout.readlines():
            database = database.strip().decode('utf-8')
            database_backup_name = "{}_{}.sql".format(database,timestamp)
            logging.info('Dump database {}'.format(database))
            subprocess.call(f"mysqldump -u {self.mysql_user} -h {self.mysql_address} -p{self.mysql_password} --databases {database} --skip-lock-tables", stdout=open(database_backup_name,"w+"), stderr=subprocess.PIPE, universal_newlines=True, shell=True)
            # Compress dump
            logging.info("Compress dump {}".format(database))
            with open(f"{database_backup_name}", "rb") as dump:
                with gzip.open(f"{database_backup_name}.gz", "wb") as gz_file:
                    shutil.copyfileobj(dump, gz_file)
                    # Remove dump .sql
                    os.remove(database_backup_name)
            
            self._send_to_bucket(
                directory=f"{self.bucket_directory}/database",
                filename=f"{database_backup_name}.gz"
            )

            self._retention(
                directory=f"{self.bucket_directory}/database",
                filename=f"{database}",
                retention=retention
            )
            os.remove(f"{database_backup_name}.gz")

    def _configure(self):
        print('Initializing configuration wizard.')

        # Input
        env_variables = {}
        env_variables['access_id'] = click.prompt('ACCESS_ID: ')
        env_variables['secret_key'] = click.prompt('SECRET_ID: ')
        env_variables['region_name'] = click.prompt('REGION_NAME: ')
        env_variables['endpoint_url'] = click.prompt('ENDPOINT_URL: ')
        env_variables['bucket_name'] = click.prompt('BUCKET_NAME: ')
        env_variables['bucket_directory'] = click.prompt('BUCKET_DIRECTORY: ')
    
        # Input MySQL Credentials
        env_variables['mysql_address'] = click.prompt('MYSQL_ADDRESS: ')
        env_variables['mysql_user'] = click.prompt('MYSQL_USER: ')
        env_variables['mysql_password'] = click.prompt('MYSQL_PASSWORD: ')

        # Create .env file
        abspath = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(abspath, '.env'), 'w') as env_file:
            for key, value in env_variables.items():
                env_file.write(f'{key.upper()}={value}\n')

        logging.info('The environment file was create')

    def _send_to_bucket(self, directory, filename):
        # Send to bucket
        try:
            logging.info(f'Sending {filename} to bucket directory {self.bucket_name}/{directory}')
            client = self._client_session()
            client.upload_file(f"{filename}", self.bucket_name, f"{directory}/{filename}")    
        except:
            logging.error(f'Error to sending {filename} to bucket folder {self.bucket_name}/{directory}')

    def _retention(self, filename, directory, retention):
        # Remove old backup
        client = self._client_session()
        retention = datetime.datetime.today() - datetime.timedelta(days=int(retention))
        prefix = filename + '_' + str(retention.strftime('%m%d%Y'))
        backup_file_list = client.list_objects(
            Bucket=self.bucket_name,
            Prefix=f"{directory}/{prefix}"
        )
        if 'Contents' in backup_file_list:
            for prefix in backup_file_list['Contents']:
                client.delete_object(Bucket=self.bucket_name,Key=prefix['Key'])
                logging.info('Remove old backup {}.'.format(prefix['Key']))
        else:
            logging.warning(f'Nothing was removed.')

    def _client_session(self):
        session = boto3.session.Session()
        client = session.client('s3',
                        region_name=self.region_name,
                        endpoint_url=self.endpoint_url,
                        aws_access_key_id=self.access_id,
                        aws_secret_access_key=self.secret_key)
        return client

@click.group()
def cli():
    pass

@click.command()
@click.option('--directory', '-d', required=True, help='Enter the directory to backup.')
@click.option('--retention', '-r', default=7, help='Enter the backup retention.')
def site(directory, retention):    
    backup = Backup()
    backup.site(
        directory=directory,
        retention=retention
    )
cli.add_command(site)

@click.command()
@click.option('--retention', '-r', default=7, help='Enter the backup retention.')
def database(retention):    
    backup = Backup()
    backup.database(
        retention=retention
    )
cli.add_command(database)

if __name__ == "__main__":
    cli()