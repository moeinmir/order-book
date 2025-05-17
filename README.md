# ORDER BOOk

### How to run this project:
this is not yet completed but to run the project you should install the go to the compose/postgres directory and run the docker-compose file for the db,
create a database named orderbook from pgadmin panel if you wish, then go to django directory and install the requirements and:

```
python3 manage.py makemigrations
python3 manage.py migrate
python3 mange.py runserver
```

```
python3 manage.py match_orders
```


### Create Mnememonic
```python3
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum

mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)


```


