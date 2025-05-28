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








