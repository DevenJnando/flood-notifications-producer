## Introduction

This is the producer component to the flood notification system.
It runs as a scheduled job which triggers every 30 minutes and
retrieves any new flood updates from the Environmental Agency's API.

It then obtains the postcodes these floods intersect with and sends
notification messages through a RabbitMQ broker to any subscribers
who wish to receive flood updates for these postcodes.

The message receipt/notification handling is dealt with by the consumer
component.

Installing the producer on its own wouldn't make much sense. Make sure
that if you decide to clone/fork, you also do the same for the [consumer repository](https://github.com/DevenJnando/flood-notifications-consumer).
The installation steps for the consumer can be found in the repo.


# DANGER! TURN BACK NOW!

If you are building locally, or forking this repo, then I *strongly* recommend to disregard this notification system portion 
of the flood monitoring project entirely and just not bother installing.

There is a lot, and I do mean **a lot** of preamble/setup in order to make this work on your own machine.

Frankly, it isn't worth your time.

For those curious on the inner workings, potential employers, or those who just have a masochistic streak, you are very
welcome to follow the steps and give it a go.

Just don't say I didn't warn you.

## Prerequisites

### Python

Python 3 is necessary for this program to run. The latest version of python
can be found [here](https://www.python.org/downloads/).

You also need pip, which should be installed by default. If, for some reason it isn't,
you can install it with the following command:

`python get-pip.py`

### Database Instances

There are 2 databases - one SQL instance containing a table with email addresses joined to another table containing postcodes,
and one CosmosDB instance containing a complete list of all England postcodes and their associated geojson geometries - which make this whole thing go.

I am absolutely not willing to share either of these endpoints, and I'm certainly not sharing any credentials.
Therefore, it would be remiss of me not to be completely blunt and tell you that attempts to get this
producer to run on your own machine are fairly unlikely since you would need to create your own
SQL/NoSQL instances yourself and either copy the existing schema exactly, or re-engineer the code to fit the
schema you choose to use.

You would also have to shard, partition and populate these databases yourselves.
If you decide to use CosmosDB, as I did, you shall need a Microsoft Azure account, and 
shall also have to grant RBAC to the application using data plane.
A guide on this is available on [learn.microsoft](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-grant-data-plane-access?tabs=built-in-definition%2Ccsharp&pivots=azure-interface-cli)

Once you've done that, you would need to populate your SQL instance with dummy emails and postcodes. 

You would also need to populate the NoSQL database with postcode and geojson geometry data, 
breaking it down into area, district, and full postcode. The dataset I used to do this can
be found [here](https://longair.net/blog/2021/08/23/open-data-gb-postcode-unit-boundaries/)...good luck!

If you've not turned tail and fled by now, I'm sorry...but, once you've got all this horrid preamble out
of the way, you can go ahead and copy/paste your database connection strings and relevant database suffixes
into the `.env_template` file

### RabbitMQ

You will need to have a rabbitMQ broker instance running on your local machine
in order for the producer to work. Otherwise, it will have nothing to produce to!

There are installation steps if you want to run rabbitMQ as a local background process
on your operating system of choice which are available [here](https://www.rabbitmq.com/docs/download)

Alternatively, if you want to spin up a quick instance using docker (docker can be installed [here](https://docs.docker.com/engine/install/)),
you can do so with this command:

`# latest RabbitMQ 4.x
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4-management`

### Redis

Redis is not strictly necessary for this program to run, but it does reduce overhead
and will save you money if you do decide to fork/modify this program as it will significantly reduce the number of
calls/queries to the database(s).

Redis can be installed from their [website](https://redis.io/downloads/). I highly recommend choosing the open source
version since it is free, and can be downloaded as a docker image. Very convenient.

Once installed, copy/paste your hostname, port, severity and postcode suffixes
into the `.env_template` file


### Environment variables

If you have followed all the previous steps, all you have to do now is remove the `_template` portion of the 
`.env_template` file to give you your `.env` file which shall be referenced at runtime.


## Installation

### Virtual environment

While this step is not strictly necessary, it is recommended.

Once you have cloned/forked the repository, in the root directory create a python
virtual environment with this command:

#### Linux/macOS
`python3 -m venv <your-virtual-environment>`

#### Windows
`py -m venv <your-virtual-environment>`

and then activate it:

#### Linux/macOS
`source <your-virtual-environment>/bin/activate`

#### Windows
`<your-virtual-environment>\Scripts\activate`

### Install dependencies

Once you have created and activated your virtual environment (or if you want to 
install dependencies directly to your python directory) run the following command to install all dependencies:

#### Linux/macOS
`python3 pip install -r requirements.txt`

#### Windows
`py -m pip install -r requirements.txt`

### Run the script

Once all dependencies are installed, and your databases are online, ensure your instance of rabbitMQ is 
running (as well as your instance of redis) and then run the script with:

#### Linux/macOS
`python3 ./app/main.py`

#### Windows
`py ./app/main.py`

