# Script to Backup Standalone Worpdress Server - v0.1

# Installation 

``` git clone https://github.com/jrdiniz/server-backup.git ```

``` cd server-backup ```

``` python3 -m venv env ```

``` source env/bin/activate ```

``` pip install -r requeriments.txt ``` 

## Create .env file with credentials

``` touch .env ```

```
MYSQL_ADDRESS=
MYSQL_USER=
MYSQL_PASSWORD=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_ENDPOINT_URL=
AWS_BUCKET_NAME=

```

## Backup MySQL

# Create Backup User

``` CREATE USER 'backup'@'localhost' IDENTIFIED BY 'password';```

``` GRANT SELECT, SHOW VIEW, LOCK TABLES, PROCESS, RELOAD ON *.* TO 'backup'@'localhost'; ```


## Schedule Script with CRON

### Run every day at 23:59

Create run.sh script

```

#!/bin/bash
source /path/to/your/venv/bin/activate
python /path/to/your/backup-mysql.py
deactivate

```


```chmod +x /path/to/run.sh ```

``` 23 59 * * * <full_path/env/bin/python3 backup-mysql.py ```