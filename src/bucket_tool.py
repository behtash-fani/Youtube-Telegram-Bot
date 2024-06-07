import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
import os
from datetime import datetime, timedelta
import logging

class Bucket:
    def __init__(self):
        session = boto3.session.Session()
        self.conn = session.client(
            service_name='s3',
            aws_access_key_id='109456c6-6a0f-4791-9a38-862c145b1d7e',
            aws_secret_access_key='750860b05b20879359504c092a24787382f7f6452969b7d68bd50247d637a43a',
            endpoint_url='https://s3.ir-thr-at1.arvanstorage.ir',
            config=Config(signature_version='s3v4')
        )

    def get_object_detail(self, file_name=None):
        try:
            if file_name:
                response = self.conn.list_objects_v2(Bucket="pandadl-media", Prefix=file_name)
                if 'Contents' in response:
                    obj = response['Contents'][0]
                    file_size = obj['Size']
                    return self.format_filesize(file_size)
                else:
                    return "File not found"
            else:
                objects_with_sizes = {}
                response = self.conn.list_objects_v2(Bucket="pandadl-media")
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
            return f"MB {size_mb:.2f}"
        else:
            size_gb = size_mb / 1024
            return f"GB {size_gb:.2f}"

    def upload_file(self, file_name, bucket_name, object_name=None):
        if object_name is None:
            object_name = file_name
        try:
            if not os.path.exists(file_name):
                logging.error(f"File {file_name} does not exist")
                return False

            self.conn.upload_file(
                file_name, bucket_name, object_name,
                ExtraArgs={'ACL': 'public-read'}
            )
            self.remove_local_file(file_name)
        except NoCredentialsError:
            logging.error("Credentials not available")
            return False
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False
        logging.info(f"File {file_name} uploaded successfully")
        return True

    def remove_local_file(self, file_path):
        try:
            os.remove(file_path)
            logging.info(f"File {file_path} has been removed successfully.")
        except FileNotFoundError:
            logging.error(f"File {file_path} not found.")
        except Exception as e:
            logging.error(f"Error occurred while trying to remove the file: {e}")

    def delete_files(self):
        try:
            response = self.conn.list_objects_v2(Bucket="pandadl-media")
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_name = obj['Key']
                    last_modified = obj['LastModified']
                    current_time = datetime.now(last_modified.tzinfo)
                    if (current_time - last_modified).total_seconds() >= 3600:
                        self.conn.delete_object(Bucket="pandadl-media", Key=file_name)
                        logging.info(f"File {file_name} has expired and been deleted.")
            else:
                logging.info("No files found.")
        except NoCredentialsError:
            logging.error("Credentials not available")
        except Exception as e:
            logging.error(f"An error occurred while deleting files: {e}")

bucket = Bucket()
# bucket.delete_files()
