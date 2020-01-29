import json
from modules.providers.aws.sts import assume_role_session


class Dispatcher:
    def __init__(self, sns_settings):
        session = assume_role_session(
            sns_settings.get("account_name"),
            sns_settings.get("role"),
            sns_settings.get("region"),
        )

        self.client = session.client("sns")
        self.topic_arn = sns_settings.get("sns_topic_arn")

    def send(self, level, payload):
        message = {
            "level": level,
            "payload": payload,
        }

        self.client.publish(
            TargetArn=self.topic_arn,
            Message=json.dumps({"default": json.dumps(message)}),
            MessageStructure="json",
        )

        return
