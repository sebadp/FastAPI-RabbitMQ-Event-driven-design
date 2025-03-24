# RabbitMQ Consumer Debugging Guide

This document outlines the steps taken to debug the RabbitMQ consumer, including commands run inside containers, network and environment variable checks, and additional installations.

## 1. Environment Variables Verification

Inside the container, we verified that the environment variables were correctly defined:

```bash
printenv RABBITMQ_HOST
# Expected output: rabbitmq

printenv RABBITMQ_USER
# Expected output: user

printenv RABBITMQ_PASS
# Expected output: password
```

## 2. Network Connectivity Verification

### 2.1. DNS Resolution Check

The resolution of the name rabbitmq was verified with:

```bash
getent hosts rabbitmq
```

Example output:

```bash
172.25.0.3      rabbitmq
```

### 2.2. /etc/hosts File Review

Inside the container, the content of the /etc/hosts file was checked to ensure there were no conflicting entries:

```bash
cat /etc/hosts
```

Typical output:

```makefile
127.0.0.1       localhost
::1             localhost ip6-localhost ip6-loopback
fe00::0         ip6-localnet
ff00::0         ip6-mcastprefix
ff02::1         ip6-allnodes
ff02::2         ip6-allrouters
172.25.0.5      30fcd172c5a0
```

### 2.3. Ping Verification

The following command was executed:

```bash
ping -c 4 rabbitmq
```

Example output:

```perl
PING rabbitmq (172.20.0.4) 56(84) bytes of data.
64 bytes from rabbitmq.real_time_orders_default (172.20.0.4): icmp_seq=1 ttl=64 time=0.191 ms
...
```

### 2.4. Port Check with nc (netcat)

The available variant of netcat (for example, netcat-openbsd) was installed and the following command was run:

```bash
apt-get update && apt-get install -y netcat-openbsd
nc -zv rabbitmq 5672
```

Expected output:

```perl
Connection to rabbitmq (172.20.0.4) 5672 port [tcp/amqp] succeeded!
```

## 3. Connection Test with a Python Script

A script called test_connection.py was created to validate the connection to RabbitMQ using Pika:

```python
import pika
import os

# Configuration using environment variables
rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
rabbitmq_user = os.environ.get("RABBITMQ_USER", "user")
rabbitmq_pass = os.environ.get("RABBITMQ_PASS", "password")

credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
connection_params = pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)

try:
    connection = pika.BlockingConnection(connection_params)
    print("✅ Successfully connected to RabbitMQ!")
    connection.close()
except Exception as e:
    print("❌ Connection error:", e)
```

How to Run It:

**Option A**: Create the file manually inside the container

Inside the container, run:

```bash
cat > test_connection.py << 'EOF'
(paste the script content here)
EOF
```

**Option B**: Mount the file from the host or use docker cp

For example:

```bash
docker cp test_connection.py event_consumers:/app/test_connection.py
```

Then, inside the container:

```bash
python test_connection.py
```

Expected output:

```css
✅ Successfully connected to RabbitMQ!
```

## 4. Debugging the Consumer Code

The consumer code (consumer.py) was reviewed, which includes:

**Retry Logic**:
Attempts to connect up to 5 times before throwing an error, with a 5-second pause between attempts.

**Environment Variables Usage**:
It was recommended to modify the code to read the connection values from environment variables:

```python
import os
rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
rabbitmq_user = os.environ.get("RABBITMQ_USER", "user")
rabbitmq_pass = os.environ.get("RABBITMQ_PASS", "password")
```

**Resolved IP Verification**:
Logging was added to print the IP that the host resolves to:

```python
import socket
resolved_ip = socket.gethostbyname(rabbitmq_host)
logger.info(f"Resolving {rabbitmq_host} to {resolved_ip}")
```

Example log:

```nginx
INFO - Resolving rabbitmq to 172.26.0.4
```

## 5. Consumer Behavior and Retries

During debugging, the following was observed:

**First Attempt**:
An attempt was made to connect to 172.26.0.4:5672, which returned "Connection refused". This is normal if RabbitMQ was not yet ready.

**Successful Retries**:
After a retry, the connection was successfully established and the channel was created. Finally, the log displayed:

```cpp
INFO - 🎧 Listening for events in queue: order_created_queue
```

## 6. Rebuilding and Verification with Docker Compose

The configuration in docker-compose.yml was verified for the RabbitMQ service and the consumer:

```yaml
services:
  rabbitmq:
    image: "rabbitmq:management"
    container_name: rabbitmq
    hostname: rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: user
      RABBITMQ_DEFAULT_PASS: password
    ports:
      - "5672:5672"
      - "15672:15672"
    restart: always

  consumers:
    build: .
    container_name: event_consumers
    depends_on:
      - rabbitmq
    environment:
      RABBITMQ_HOST: rabbitmq
      RABBITMQ_USER: user
      RABBITMQ_PASS: password
    restart: always
    command: ["bash", "consumer_entrypoint.sh"]
```

The image was rebuilt using:

```bash
docker-compose up --build
```
