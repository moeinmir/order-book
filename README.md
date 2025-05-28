# ORDER BOOk
### We Tried to bring some flows that are used in integrating with blockchain network here

1. user can register
2. user can charge his account by the erc20 tokens
3. user can add limit or market orders for pairs of token
4. orders will be matched and executed
5. and finely user can withdraw his balance

note that this is just for the purpose of practice and we even use integer for prices and our fucus was to bring the main functionality in a very limited time



## Preparing the Environment
### This project uses the following services:

1. Kafka (without Zookeeper, using KRaft mode) as the message broker

2. PostgreSQL as the relational database

3. Redis for specific use cases

To spin up the required services, navigate to the compose/allatonce directory and run:

```
sudo docker-compose up
```

- Before starting the services, you need to generate a Kafka Cluster ID. This is required because we’re using a recent version of Kafka in KRaft mode:

```
cd compose/kafka/kafka-kraft
```
```
sudo docker-compose -f generate-cluster.yml

```

- Copy the generated Cluster ID into compose/allatonce directory.
- We've bundled Kafka, PostgreSQL, and Redis into a single Compose setup (allatonce) for convenience, but you can also run them separately if needed.
- Once the services are running:
- You can access Kafka UI via your browser on the specified port.
- You can also use pgAdmin for managing the PostgreSQL database through a graphical interface.


### How will it work:

after preparing the environment we will go the backend directory install the required python packages first of create a mnemonic by running the following command some where:
```
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip39WordsNum, Bip44Changes, Bip84, Bip84Coins
mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
print(f"Mnemonic string: {mnemonic}")
```
by running this you will get an mnemonic that your app will use to manage all account that will be derived from this. you should place it in your .env file at the root of the project.

then you can create a django super user by running the following the bellow command
```
python3 manage.py createsupersuer
```

you will run the app:


```
python3 manage.py runserver
```

you will go to the swagger dashboard of the project and create a user that will represent you main account for handling funds and tokens you will replace his eth_address and eth_index in the .env file at the root of your project.

to begin the process of finding orders run: 
```
python3 manage.py match_orders
```

to execute the orders run:

```
python3 manage.py execute_matches
```

you need some erc20 tokens that are deployed in sepolia network and you although need this to have eth for gas and some balance of these tokens so you could work with this, the process of matching order is done off chain but you need to charge account with little gas for the final and initial transfers

### Open concerns

- The mnemonic is stored in the .env file, which is not secure.

- The application's central wallet—intended to hold all funds—is treated like any other user, with its details hardcoded in the .env file.

- Prices are handled using plain integers, without precision or scaling.

- noting that the application is supposed to handle big number in the scale of 2**255 we should think of a safe way for calculation and storing the data

- Job scheduling is currently handled using Django’s BaseCommand, which could be replaced with a more robust and efficient tool.

- The accounting logic has not been properly tested, and overall test coverage is limited.

- Several areas of the application likely lack adequate test coverage.

- There's no clearly defined request/response contract for APIs.

- The data models are missing several useful fields and could be more expressive.

- Input validation is largely absent across the application.

- Many other issues may exist—but the goal of this project was to serve as hands-on practice rather than to build a production-grade system.

