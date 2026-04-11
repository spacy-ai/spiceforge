### Setup

Need to have ngspice setup locally as a prerequisite

Install dependencies

``` 
pip install -r requirements.txt 
```

Database:
- Setup Postgres DB locally
- create database
- create user
- grant all permissions on the database to user
- add the url to `.env` check `sample.env

Run migrations

```
python manage.py migrate
```

Create new migrations (after model changes)

```
python manage.py makemigrations
```

Run the server

```
python manage.py runserver
```
