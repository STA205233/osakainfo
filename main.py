import SlackHandler
import os
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


def main():
    channel = "#osaka-micrograms-info"
    duration_img = 60 * 60 * 24  # 24 hours
    duration_txt = 60 * 10  # 10 minutes
    init_ = True
    host = "192.168.10.99"
    user = os.environ['DB_USER']
    password = os.environ['DB_PASSWD']
    last_ts = 0
    slack_handler = SlackHandler.SlackHandler(os.environ['SLACK_TOKEN'])
    connector1 = mysqlIO.mysqlIO(host, user, password, "")
    while True:
        text = f"Current Osaka Micrograms Status ({time.strftime('%Y-%m-%d %H:%M:%S')})"
        try:
            pressure_data = fetch_latest_pressure_data(connector1)
            text += "\n_________________Pressure__________________"
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
            if init_:
                response = slack_handler.send_message(channel, text)
                init_ = False
                last_ts = response["ts"]
                channel = response["channel"]
            else:
                slack_handler.edit_message(channel, last_ts, text)
            time.sleep(duration_txt)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
