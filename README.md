# ORDER BOOk


##### Do as i say:
1_run your postgres
2_make a test app and do some test view
3_handle authentication
4_manage authentication for you test app
5_try to connect to chain
6_make your data models and go on

try not to go so fast even if we said that we are going to take big bite


_see privilege go postgres


```
python -m venv venv
```

```
pip install django psycopg2-binary

```


```
django-admin startproject myproject
cd myproject

```


```
python manage.py migrate

```

```
python2 mange.py runserver
```

```
source venv/bin/activate
```


```
python3 manage.py createsuperuser

```

```
python3 manage.py migrate
```


```
python manage.py startapp testapp

```

```
python manage.py makemigrations
python manage.py migrate

```



```
pip install djangorestframework djangorestframework-simplejwt

```



```
pip install drf-yasg

```



models
flows
implementation and learning

Order Book Flows:




3: The user calls his balance then enquiry the chain and updates his balance in the table and gives him his balance.
get tokens
get my balance for given token



4: user register order we check his free balance lock some amount of it and and register order
5: a job looking for the matched order and settle them and change them in chain and db

We do lock and chain call before acting to be safe



6: user give token and some address and say what token to withdraw and we move the transfer in the chain and then in db

1: user call to register and give (username , password) with the application secret key in the chain one public key is generated and one record related to this user is created in the database that contains his personal info and public key.
1: user provide call for access token and refresh token and receive them
2: user calls and gives access token and receives his account number so he could use it for charging his balance.


