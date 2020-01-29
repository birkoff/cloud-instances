from json import dumps
from datetime import datetime


def info(class_name, message):
    log("info", class_name, message)


def error(class_name, message):
    log("error", class_name, message)


def warning(class_name, message):
    log("warning", class_name, message)


def log(level, class_name, message):
    now = datetime.now()
    log_message = {
        level: {
            "datetime": now.strftime("%d/%m/%Y %H:%M:%S"),
            "class": class_name,
            "message": message,
        }
    }
    print(dumps(log_message))
