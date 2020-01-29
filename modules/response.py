from json import dumps


def success(message):
    body = dumps(message)

    response = {
        "statusCode": 200,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
    return response


def created(message):
    body = dumps(message)

    response = {
        "statusCode": 201,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
    return response


def error(message):
    response = {
        "statusCode": 400,
        "body": dumps(message),
        "headers": {"Access-Control-Allow-Origin": "*"},
    }
    return response


if __name__ == "__main__":
    pass
