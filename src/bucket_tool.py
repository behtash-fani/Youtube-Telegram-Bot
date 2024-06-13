import aioboto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError
import os
from datetime import datetime
import logging
import asyncio
from dotenv import load_dotenv
import threading
import time

load_dotenv()

class Bucket:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = Config(
            region_name='us-east-1',
            signature_version='s3v4'
        )
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.endpoint_url = 'https://s3.ir-thr-at1.arvanstorage.ir'

    async def get_object_detail(self, file_name=None):
        async with self.session.client(
                service_name='s3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                endpoint_url=self.endpoint_url,
                config=self.config) as conn:
            try:
                if file_name:
                    response = await conn.list_objects_v2(Bucket="pandadl-media", Prefix=file_name)
                    if 'Contents' in response:
                        obj = response['Contents'][0]
                        file_size = obj['Size']
                        return self.format_filesize(file_size)
                    else:
                        return "File not found"
                else:
                    objects_with_sizes = {}
                    response = await conn.list_objects_v2(Bucket="pandadl-media")
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            file_name = obj['Key']
                            file_size = obj['Size']
                            objects_with_sizes[file_name] = self.format_filesize(file_size)
                    return objects_with_sizes
            except NoCredentialsError:
                logging.error("Credentials not available")
                return {}

    def format_filesize(self, filesize):
        """Convert filesize from bytes to a human-readable format (MB or GB)."""
        if filesize is None:
            return 'N/A'

        size_mb = filesize / (1024 * 1024)
        if size_mb < 1024:
            return f"{size_mb:.2f} مگابایت"
        else:
            size_gb = size_mb / 1024
            return f"{size_gb:.2f} گیگابایت"

    async def upload_file(self, file_name, bucket_name, object_name=None):
        logging.info(f"File {file_name} start uploading")
        if object_name is None:
            object_name = file_name
        try:
            if not os.path.exists(file_name):
                logging.error(f"File {file_name} does not exist")
                return False

            async with self.session.client(
                    service_name='s3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    endpoint_url=self.endpoint_url,
                    config=self.config) as conn:
                await conn.upload_file(
                    file_name, bucket_name, object_name,
                    ExtraArgs={'ACL': 'public-read'}
                )
                await self.remove_local_file(file_name)
        except NoCredentialsError:
            logging.error("Credentials not available")
            return False
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False
        logging.info(f"File {file_name} uploaded successfully")
        return True

    async def remove_local_file(self, file_path):
        try:
            os.remove(file_path)
            logging.info(f"File {file_path} has been removed successfully.")
        except FileNotFoundError:
            logging.error(f"File {file_path} not found.")
        except Exception as e:
            logging.error(
                f"Error occurred while trying to remove the file: {e}")

    async def delete_files(self):
        async with self.session.client(
                service_name='s3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                endpoint_url=self.endpoint_url,
                config=self.config) as conn:
            try:
                response = await conn.list_objects_v2(Bucket="pandadl-media")
                if 'Contents' in response:
                    for obj in response['Contents']:
                        file_name = obj['Key']
                        last_modified = obj['LastModified']
                        current_time = datetime.now(last_modified.tzinfo)
                        if (current_time - last_modified).total_seconds() >= 3600:
                            await conn.delete_object(Bucket="pandadl-media", Key=file_name)
                            logging.info(
                                f"File {file_name} has expired and been deleted.")
                else:
                    logging.info("No files found.")
            except NoCredentialsError:
                logging.error("Credentials not available")
            except Exception as e:
                logging.error(f"An error occurred while deleting files: {e}")

bucket = Bucket()

def run_delete_files():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        loop.run_until_complete(bucket.delete_files())
        time.sleep(300)

delete_thread = threading.Thread(target=run_delete_files)
delete_thread.daemon = True
delete_thread.start()