import requests
import os
from slack_sdk import WebClient


class SlackHandler:
    def __init__(self, token, logger=None):
        self.client = WebClient(token=token)
        self.last_uploaded_file_ids = []
        self.logger = logger
        if self.logger:
            self.logger.info("Initialized SlackHandler")
        ret = self.client.auth_test()
        if self.logger:
            if ret["ok"]:
                self.logger.info("Slack auth test successful")
                self.logger.info(self.get_info())
            else:
                self.logger.error(f"Slack auth test failed: {ret['error']}")

    def get_info(self, teams=None):
        ret = self.client.auth_test()
        if ret["ok"]:
            ret2 = self.client.auth_teams_list()
            name = None
            if ret2["ok"]:
                if teams:
                    for team in ret2["teams"]:
                        if team["id"] == teams:
                            name = team["name"]
                else:
                    name = []
                    for team in ret2["teams"]:
                        name.append(team["name"])
                string = f"Authenticated as user: {ret['user']} in team: {name}\n"
            else:
                string = f"Authenticated as user: {ret['user']} but failed to get team list: {ret2['error']}\n"
        else:
            string = f"Slack auth test failed: {ret['error']}"
        return string

    def return_wrapper(self, response):
        if self.logger:
            self.logger.debug(f"Slack API response: {response}")
        return response

    def send_message(self, channel, message):
        if self.logger:
            self.logger.info(f"Sending message to channel {channel}")
            self.logger.debug(f"Sending message to channel {channel}: {message}")
        return self.return_wrapper(self.client.chat_postMessage(channel=channel, text=message))

    def send_message_block(self, channel, blocks, text=""):
        if self.logger:
            self.logger.info(f"Sending block message to channel {channel}")
            self.logger.debug(f"Sending block message to channel {channel}: {blocks}")
        return self.return_wrapper(self.client.chat_postMessage(channel=channel, blocks=blocks, text=text))

    def get_chat_info_from_url(self, url):
        parts = url.split('/')
        channel = parts[-2]
        ts = parts[-1].replace('p', '')
        ts = ts[:-6] + '.' + ts[-6:]
        return channel, ts

    def delete_message(self, channel, ts):
        if self.logger:
            self.logger.info(f"Deleting message in channel {channel} with ts {ts}")
        return self.return_wrapper(self.client.chat_delete(channel=channel, ts=ts))

    def delete_message_url(self, url):
        channel, ts = self.get_chat_info_from_url(url)
        if self.logger:
            self.logger.info(f"Deleting message from URL {url} in channel {channel} with ts {ts}")
        return self.delete_message(channel, ts)

    def edit_message(self, channel, ts, message):
        if self.logger:
            self.logger.info(f"Editing message in channel {channel} with ts {ts}")
        return self.return_wrapper(self.client.chat_update(channel=channel, ts=ts, text=message))

    def edit_message_block(self, channel, ts, blocks, text=""):
        if self.logger:
            self.logger.info(f"Editing block message in channel {channel} with ts {ts}")
        return self.return_wrapper(self.client.chat_update(channel=channel, ts=ts, blocks=blocks, text=text))

    def test(self):
        response = self.client.auth_test()
        return response["ok"]

    def reply_in_thread(self, channel, thread_ts, message):
        return self.return_wrapper(self.client.chat_postMessage(channel=channel, text=message, thread_ts=thread_ts))

    def upload_file(self, file_path):
        if self.logger:
            self.logger.info(f"Uploading file {file_path} to Slack")
        if not os.path.isfile(file_path):
            if self.logger:
                self.logger.error(f"The file {file_path} does not exist.")
            else:
                print(f"The file {file_path} does not exist.")
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        file_size = os.path.getsize(file_path)
        ret = self.client.files_getUploadURLExternal(filename=file_path, length=file_size)
        upload_url = ret["upload_url"]
        with open(file_path, 'rb') as f:
            response = requests.post(upload_url, files={"file": f})
        if response.status_code != 200:
            if self.logger:
                self.logger.error(f"File upload failed with status code {response.status_code}")
            else:
                print(f"File upload failed with status code {response.status_code}")
            return {"ok": False, "error": f"File upload failed with status code {response.status_code}"}
        return self.return_wrapper(ret)

    def send_image(self, channel, file_ids, thread_ts=None, titles=None):
        if titles is None:
            titles = ["" for _ in file_ids]
        if self.logger:
            self.logger.info(f"Sending images to channel {channel} in thread {thread_ts if thread_ts else 'main thread'}")
        files = [{"id": file_ids[i], "title": titles[i] if titles[i] else ""} for i in range(len(file_ids))]
        return self.return_wrapper(self.client.files_completeUploadExternal(files=files, channel_id=channel, thread_ts=thread_ts))

    def upload_and_send_image(self, channel, file_paths, thread_ts=None, titles=None):
        if titles is None:
            titles = ["" for _ in file_paths]
        file_ids = []
        self.last_uploaded_file_ids = []
        for file_path in file_paths:
            upload_response = self.return_wrapper(self.upload_file(file_path))
            file_id = upload_response["file_id"]
            file_ids.append(file_id)
            if upload_response["ok"]:
                self.last_uploaded_file_ids.append(file_id)
        return self.return_wrapper(self.send_image(channel, file_ids, thread_ts=thread_ts, titles=titles))

    def delete_img(self, id):
        if self.logger:
            self.logger.info(f"Deleting image with id {id} from Slack")
        result = self.return_wrapper(self.client.files_delete(file=id))
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
