# Script to Backup Standalone Worpdress Server - v0.1


## Backup 

# Create Backup User

``` CREATE USER 'backup'@'localhost' IDENTIFIED BY 'password';```

``` GRANT SELECT, SHOW VIEW, LOCK TABLES, PROCESS, RELOAD ON *.* TO 'backup'@'localhost'; ```
