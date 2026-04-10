### Setup

Need to have ngspice setup locally as a prerequisite

Install dependencies

``` 
pip install -r requirements.txt 
```

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
