# wallbot

A Telegram bot for managing searches on Wallapop.

## Features
- Notifies you about new search results.
- Alerts you when an item's price drops.
- Allows you to manage your list of tracked items.

## Running the application

This project can be run using Docker or directly on your local machine. Both methods require a `.env` file for configuration.

### 1. Configuration

First, create a `.env` file in the root of the project by copying the example file:

```bash
# For Linux/macOS
cp .env.example .env

# For Windows (Command Prompt)
copy .env.example .env
```

###### 2. Run the Docker container

You will need a Telegram Bot Token to run the application. You can get one by talking to the [BotFather](https://t.me/botfather) on Telegram.

```bash
docker run --name wallbot --env BOT_TOKEN=<YOUR-TOKEN> z0r3f/wallbot-docker:latest
```

### 2. Without Docker (using a virtual environment)

This method is recommended if you want to run the application without Docker.

The setup script will create a virtual environment, install the required dependencies, and start the application.

- **For Windows:**

  ```powershell
  .\run.bat
  ```

- **For Linux/macOS**:

  ```bash
  chmod +x run.sh
  ./run.sh
  ```

The script will prompt you for your Telegram Bot Token if it's not already set as an environment variable.

The script will also create a `db.sqlite` file in the root of the project, and a `wallbot.log` file with the application logs.


## Docker

### Generate image docker

```bash
docker build --tag z0r3f/wallbot-docker:latest .
```

### Tag version

###### Windows

```ps
$version = Get-Content "VERSION"
```

###### Unix

```bash
version=`cat VERSION`
```

###### Tag

```bash
docker tag z0r3f/wallbot-docker:latest z0r3f/wallbot-docker:$version
```

###### Push

```bash
docker push z0r3f/wallbot-docker:latest 
docker push z0r3f/wallbot-docker:$version
```

### See images

```bash
docker images
```

### Run on container

```bash
docker run --name wallbot --env BOT_TOKEN=<YOUR-TOKEN> z0r3f/wallbot-docker:latest
```

### Export image

```bash
docker save -o wallbot-docker.tar z0r3f/wallbot-docker:latest
```

## Project Structure

```
wallapop_bot/
├── __init__.py
├── main.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── constants.py
├── database/
│   ├── __init__.py
│   ├── db_helper.py
│   └── models.py
├── telegram/
│   ├── __init__.py
│   ├── bot.py
│   ├── handlers.py
│   └── notifications.py
├── wallapop/
│   ├── __init__.py
│   ├── api_client.py
│   ├── api_models.py
│   ├── categories.py
│   └── monitor.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── version.py
├── web/
│   ├── app.py
│   └── templates/
│       ├── index.html
│       ├── manual_search.html
│       └── searches.html
└── requirements.txt
```