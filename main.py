import datetime
import SlackHandler
import os
from screenshot import make_screenshot
import time
import mysqlIO


def fetch_latest_ups_data(connector):
    result = connector.query("SELECT * FROM bench_test.Turbo_UPS ORDER BY time DESC LIMIT 1")
    return result[0]


def fetch_latest_pressure_data(connector):
    result = connector.query("SELECT * FROM Osaka_Dec_2025.pressure ORDER BY time DESC LIMIT 1")
    return result[0]


def convert2Pa(torr):
    return float(torr) * 133.3223684211


def push_screenshot_to_slack(slack_handler: SlackHandler.SlackHandler, channel, image_path, thread_ts=None):
    return slack_handler.upload_and_send_image(channel, [image_path], titles=["Osaka Micrograms Dashboard Screenshot"], thread_ts=thread_ts)


def make_screenshot_and_push_to_slack(slack_handler: SlackHandler.SlackHandler, channel, thread_ts=None):
    screenshot_path = "osaka_micrograms_dashboard.png"
    make_screenshot(screenshot_path)
    result = push_screenshot_to_slack(slack_handler, channel, screenshot_path, thread_ts=thread_ts)
    return result


def main():
    channel = "#osaka-micrograms-info"
    duration_img = 60 * 60 * 24  # 24 hours
    duration_txt = 10 * 60  # 10 minutes
    last_img_push_time = None
    last_txt_push_time = None
    init_ = True
    host = "192.168.10.99"
    user = os.environ['DB_USER']
    password = os.environ['DB_PASSWD']
    last_ts = None
    slack_handler = SlackHandler.SlackHandler(os.environ['SLACK_TOKEN'])
    connector1 = mysqlIO.mysqlIO(host, user, password, "")
    while True:
        current_time = datetime.datetime.now()
        if last_txt_push_time is not None and current_time - last_txt_push_time < datetime.timedelta(seconds=duration_txt):
            time.sleep(1)
            continue
        text_title = f"Current Osaka MicroGRAMS Status ({time.strftime('%Y-%m-%d %H:%M:%S')})"
        try:
            blocks = []
            block = {"type": "header", "text": {"type": "plain_text", "text": text_title}}
            blocks.append(block)
            text = ""
            pressure_data = fetch_latest_pressure_data(connector1)
            text += "_________________Pressure__________________"
            text += "\nPressure 1: ".ljust(12) + f"{pressure_data['PR1']:.4e}".rjust(6) + " Torr, " + f"{convert2Pa(pressure_data['PR1']):.4e}".rjust(6) + " Pa"
            text += "\nPressure 2: ".ljust(12) + f"{pressure_data['PR2']:.4e}".rjust(6) + " Torr, " + f"{convert2Pa(pressure_data['PR2']):.4e}".rjust(6) + " Pa"
            text += "\nPressure 3: ".ljust(12) + f"{pressure_data['PR3']:.4e}".rjust(6) + " Torr, " + f"{convert2Pa(pressure_data['PR3']):.4e}".rjust(6) + " Pa"
            text += "\nPressure 4: ".ljust(12) + f"{pressure_data['PR4']:.4e}".rjust(6) + " Torr, " + f"{convert2Pa(pressure_data['PR4']):.4e}".rjust(6) + " Pa"
            text += "\nPressure 5: ".ljust(12) + f"{pressure_data['PR5']:.4e}".rjust(6) + " Torr, " + f"{convert2Pa(pressure_data['PR5']):.4e}".rjust(6) + " Pa"
            text += "\n___________________________________________\n"
            ljust_value = 32
            text += "\n___________________Turbo____________________"
            ups_data = fetch_latest_ups_data(connector1)
            text += "\nActual Turbo Rotation: ".ljust(ljust_value) + f"{ups_data["ActualSpd"]:5}" + " rpm"
            text += "\nTemperature Pump Bottom Part: ".ljust(ljust_value) + f"{ups_data["TempPmpBot"]:5}" + " °C"
            text += "\nTemperature Motor: ".ljust(ljust_value) + f"{ups_data["TempMotor"]:5}" + " °C"
            text += "\nTemperature Electric: ".ljust(ljust_value) + f"{ups_data["TempElec"]:5}" + " °C"
            text += "\nTemperature Bearing: ".ljust(ljust_value) + f"{ups_data["TempBearng"]:5}" + " °C"
            text += "\n___________________________________________\n"
            block = {"type": "context", "elements": [{"type": "mrkdwn", "text": f"```{text}```"}]}
            blocks.append(block)
            if init_:
                response = slack_handler.send_message_block(channel, blocks=blocks, text=text_title + "\n" + text)
                init_ = False
                last_ts = response["ts"]
                channel = response["channel"]
                result = make_screenshot_and_push_to_slack(slack_handler, channel, thread_ts=last_ts)
                last_img_push_time = current_time
                last_txt_push_time = last_img_push_time
            else:
                slack_handler.edit_message_block(channel, last_ts, blocks, text)
                last_txt_push_time = current_time
                if (current_time - last_img_push_time).total_seconds() >= duration_img:
                    make_screenshot_and_push_to_slack(slack_handler, channel, thread_ts=last_ts)
                    last_img_push_time = current_time
                    slack_handler.delete_last_uploaded_images()
        except KeyboardInterrupt:
            break
        except Exception as e:
            last_img_push_time = datetime.datetime.now()
            print("Error occurred:", e)
            time.sleep(60)  # wait for a minute before retrying


if __name__ == "__main__":
    main()
