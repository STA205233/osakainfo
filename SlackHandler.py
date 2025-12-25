import requests
import os
from slack_sdk import WebClient


class SlackHandler:
    def __init__(self, token):
        self.client = WebClient(token=token)
        self.last_uploaded_file_ids = []

    def send_message(self, channel, message):
        return self.client.chat_postMessage(channel=channel, text=message)

    def send_message_block(self, channel, blocks, text=""):
        return self.client.chat_postMessage(channel=channel, blocks=blocks, text=text)

    def get_chat_info_from_url(self, url):
        parts = url.split('/')
        channel = parts[-2]
        ts = parts[-1].replace('p', '')
        ts = ts[:-6] + '.' + ts[-6:]
        return channel, ts

    def delete_message(self, channel, ts):
        return self.client.chat_delete(channel=channel, ts=ts)

    def delete_message_url(self, url):
        channel, ts = self.get_chat_info_from_url(url)
        return self.delete_message(channel, ts)

    def edit_message(self, channel, ts, message):
        return self.client.chat_update(channel=channel, ts=ts, text=message)

    def edit_message_block(self, channel, ts, blocks, text=""):
        return self.client.chat_update(channel=channel, ts=ts, blocks=blocks, text=text)

    def test(self):
        response = self.client.auth_test()
        return response["ok"]

    def reply_in_thread(self, channel, thread_ts, message):
        return self.client.chat_postMessage(channel=channel, text=message, thread_ts=thread_ts)

    def upload_file(self, file_path):
        if not os.path.isfile(file_path):
            print(f"The file {file_path} does not exist.")
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        file_size = os.path.getsize(file_path)
        ret = self.client.files_getUploadURLExternal(filename=file_path, length=file_size)
        upload_url = ret["upload_url"]
        with open(file_path, 'rb') as f:
            response = requests.post(upload_url, files={"file": f})
        if response.status_code != 200:
            print("File upload failed with status code:", response.status_code)
            return {"ok": False, "error": f"File upload failed with status code {response.status_code}"}
        return ret

    def send_image(self, channel, file_ids, thread_ts=None, titles=None):
        if titles is None:
            titles = ["" for _ in file_ids]
        files = [{"id": file_ids[i], "title": titles[i] if titles[i] else ""} for i in range(len(file_ids))]
        return self.client.files_completeUploadExternal(files=files, channel_id=channel, thread_ts=thread_ts)

    def upload_and_send_image(self, channel, file_paths, thread_ts=None, titles=None):
        if titles is None:
            titles = ["" for _ in file_paths]
        file_ids = []
        self.last_uploaded_file_ids = []
        for file_path in file_paths:
            upload_response = self.upload_file(file_path)
            file_id = upload_response["file_id"]
            file_ids.append(file_id)
            if upload_response["ok"]:
                self.last_uploaded_file_ids.append(file_id)

        return self.send_image(channel, file_ids, thread_ts=thread_ts, titles=titles)

    def delete_img(self, id):
        result = self.client.files_delete(file=id)
        return result

    def delete_last_uploaded_images(self):
        for file_id in self.last_uploaded_file_ids:
            self.delete_img(file_id)
        self.last_uploaded_file_ids = []

    def delete_all_uploaded_images(self, channel):
        response = self.client.files_list(channel=channel)
        result = response["files"]
        for file in result:
            self.delete_img(file["id"])

    def delete_all_messages_in_channel(self, channel):
        response = self.client.conversations_history(channel=channel)
        messages = response["messages"]
        for message in messages:
            try:
                self.delete_message(channel, message["ts"])
            except Exception as e:
                print(f"Failed to delete message {message['ts']}: {e}")
