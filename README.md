# ORDER BOOk

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







