# YouTube Telegram Bot

A Telegram bot that downloads YouTube videos and uploads them to a cloud storage, providing users with a direct download link.

## Technologies and Packages Used

- **Python**: The main programming language used for the bot.
- **Aiogram**: A modern and fully asynchronous framework for Telegram Bot API.
- **SQLite**: A lightweight database used to store user data.
- **dotenv**: A package to load environment variables from a `.env` file.
- **yt-dlp**: A command-line program to download videos from YouTube and other video sites.
- **Docker**: Used to containerize the application.
- **Nginx**: Used as a reverse proxy server.

## Setting Up the Project

### Prerequisites

- Python 3.12
- Docker
- Docker Compose

### Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/behtash-fani/youtube-telegram-bot.git
    cd youtube-telegram-bot
    ```

2. **Create a virtual environment**:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Create a [.env](http://_vscodecontentref_/5) file** in the root directory with the following content:
    ```properties
    API_TOKEN=your_telegram_bot_api_token
    DOWNLOAD_DIR=../downloads/
    DOMAIN=your_domain
    ```

### Running the Project

1. **Run the bot**:
    ```sh
    python src/main.py
    ```

2. **Using Docker**:
    - Build the Docker image:
        ```sh
        docker-compose build
        ```
    - Run the Docker container:
        ```sh
        docker-compose up
        ```

### Environment Variables

- `API_TOKEN`: Your Telegram bot API token.
- `DOWNLOAD_DIR`: The directory where downloaded files will be stored.
- `DOMAIN`: The domain name used for generating download links.

## Usage

1. Start the bot by sending the `/start` command.
2. Send a YouTube video or playlist link to the bot.
3. The bot will download the video or playlist and provide you with a direct download link.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.


