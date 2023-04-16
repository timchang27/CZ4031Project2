# CZ4031Project2 
# Project 2 - Understanding Query Plans during Data Exploration

## Introduction
This project aims to design and implement a user-friendly GUI application that can retrieve and display information about two Query Execution Plans (QEPs) P1 and P2 from a PostgreSQL database, based on two SQL queries Q1 and Q2 from a user. It should automatically **generate a user-friendly explanation (e.g. natural and visual language description) of the changes to the QEPs and the reason(s) why.**

## Database Setup
1. Clone the repository.
    ```
    git clone https://github.com/timchang27/CZ4031Project2
    ```

2. Change the working directory to the `database` folder.
    ```
    cd database
    ```

3. Download the `database-dump.sql`, `CSV` and `Dockerfile` files from my onedrive, save it in the database folder in Step 2. 
    ```
    https://entuedu-my.sharepoint.com/:f:/g/personal/myeow003_e_ntu_edu_sg/Eqyar15zBddEqB89XAwbRC8BkB-GxYekhazyMuMURrF96A?e=918vcy
    ```

## Instantiate the containers
1. Use `docker-compose` to bring up the containers. During first creation, the database dump will be imported to the database automatically.
    ```
    cd ..
    docker-compose up -d
    ```

2. The database is accessible on port `5432`, pgadmin is accessible on port `8080`, and web-app is accesible on port `5000`.

## Contributors
- [TIMOTHY CHANG ZU'EN]
- [YEOW MING XUAN]
- [CHOI SEUNGHWAN]
- [MUHAMMAD RIAZ BIN JAMALULLAH]