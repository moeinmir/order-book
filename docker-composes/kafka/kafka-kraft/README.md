# How to create docker compose for running Kafka in Kraft mode

After starting kafka cluster we can create topic:

`docker exec -ti kafka1 /usr/bin/kafka-topics --create  --bootstrap-server kafka1:19092,kafka2:19093,kafka3:19094 --replication-factor 2 --partitions 4 --topic topic1`

Send the data:

`docker exec -ti kafka1 /usr/bin/kafka-console-producer --bootstrap-server kafka1:19092,kafka2:19093,kafka3:19094 --topic topic1`

Read the data:

`docker exec -ti kafka1 /usr/bin/kafka-console-consumer --bootstrap-server kafka1:19092,kafka2:19093,kafka3:19094 --topic topic1 --from-beginning`
