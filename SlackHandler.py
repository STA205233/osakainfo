from slack_sdk import WebClient


class SlackHandler:
    def __init__(self, token):
        self.client = WebClient(token=token)

    def send_message(self, channel, message):
        return self.client.chat_postMessage(channel=channel, text=message)

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

    def test(self):
        response = self.client.auth_test()
        return response["ok"]
