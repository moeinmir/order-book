# ORDER BOOk

## Preparing the Environment
### This project uses the following services:

1. Kafka (without Zookeeper, using KRaft mode) as the message broker

2. PostgreSQL as the relational database

3. Redis for specific use cases

To spin up the required services, navigate to the compose/allatonce directory and run:

```
cd compose/kafka/kafka-kraft
```

```
sudo docker-compose -f generate-cluster.yml run --rm generate-cluster-id

```


```
sudo docker-compose up

```

- Before starting the services, you need to generate a Kafka Cluster ID. This is required because we’re using a recent version of Kafka in KRaft mode:


- Copy the generated Cluster ID into compose/allatonce directory.

- We've bundled Kafka, PostgreSQL, and Redis into a single Compose setup (allatonce) for convenience, but you can also run them separately if needed.

- Once the services are running:

- You can access Kafka UI via your browser on the specified port (check the Compose file for the exact port).

- You can also use pgAdmin for managing the PostgreSQL database through a graphical interface.









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












1: read it and make it fine
2: add some tests for some parts if you wished to test the functionality after refactor and all
3: complete the readme
4: and thats it  


