import random
from datetime import datetime
from datetime import timedelta
import re


class Instance:

    MAX_LEN_NAME = 50
    MIN_LEN_NAME = 3

    def __init__(self, input_data, account):
        """
        :type input_data: dict
        :type account: Account object
        """
        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        self.account = account

        self.id = input_data.get("id", None)
        self.environment = input_data.get(
            "environment"
        )  # based on environment we set the name (with domain)
        self.name = input_data.get("name", "")

        self.public_dns = self.name
        self.private_dns = self.name

        self.owner = input_data.get("owner", "")
        self.type = input_data.get("type", "")

        self.stop_time = input_data.get("stop_time", None)
        self.start_time = input_data.get("start_time", "")
        self.last_stop_at = input_data.get("last_stop_at", "")
        self.last_start_at = input_data.get("last_start_at", "")
        self.terminate_date = input_data.get(
            "terminate_date", (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y"),
        )
        self.terminate_time = input_data.get("terminate_time", str(23))
        self.last_update_at = current_datetime if self.id is None else ""

        self.image_id = input_data.get("image_id", "")
        self.key_name = input_data.get("key_name", account.key_name)
        self.security_groups = input_data.get("security_groups", [])
        self.availability_zone = input_data.get(
            "availability_zone", random.choice(account.availability_zones)
        )

        self.profile = input_data.get("instance_profile", account.instance_profile)

        self.subnet_id = input_data.get(
            "subnets", account.subnets.get(self.availability_zone)
        )
        self.region = account.region
        self.role = account.tag_role

        self.attributes = {
            "name": self.__name,
            "owner": self.owner,
            "type": self.type,
            "environment": self.__environment,
            "stop_time": self.__stop_time,
            "start_time": self.__start_time,
            "termination_date": self.terminate_date,
            "last_update_at": self.last_update_at,
            "image_id": self.image_id,
            "key_name": self.key_name,
            "role": self.role,
        }

    @property
    def name(self):
        return self.__name

    @property
    def public_dns(self):
        return self.__public_dns

    @property
    def private_dns(self):
        return self.__private_dns

    @property
    def environment(self):
        return self.__environment

    @property
    def stop_time(self):
        return self.__stop_time

    @property
    def start_time(self):
        return self.__start_time

    @property
    def owner(self):
        return self.__owner

    @property
    def type(self):
        return self.__type

    @property
    def image_id(self):
        return self.__image_id

    @property
    def security_groups(self):
        return self.__security_groups

    @name.setter
    def name(self, name):
        if not self.valid_name(name):
            name = name[0 : name.find(".")]

        if not self.valid_name(name):
            raise Exception(
                "{} Invalid name: {}, use \w and {} to {} chars".format(
                    self.__class__.__name__, name, self.MIN_LEN_NAME, self.MAX_LEN_NAME,
                )
            )

        self.__name = "{}".format(name.lower())

    @public_dns.setter
    def public_dns(self, name):
        dns_zone = self.account.hosted_zone_names.get("public")
        self.__public_dns = "{}.{}".format(name.lower(), dns_zone)

    @private_dns.setter
    def private_dns(self, name):
        dns_zone = self.account.hosted_zone_names.get("private")
        self.__private_dns = "{}.{}".format(name.lower(), dns_zone)

    @owner.setter
    def owner(self, owner):
        if not owner:
            raise Exception("{} missing argument owner".format(self.__class__.__name__))
        self.__owner = owner

    @type.setter
    def type(self, type):
        if not type:
            raise Exception("{} missing argument type".format(self.__class__.__name__))
        self.__type = type

    @image_id.setter
    def image_id(self, image_id):
        if not image_id:
            raise Exception(
                "{} missing argument image_id".format(self.__class__.__name__)
            )
        self.__image_id = image_id

    @environment.setter
    def environment(self, environment):
        environments = self.account.environments
        if not environment or environment not in environments:
            raise Exception(
                "{} environment {} is not enabled on the account settings".format(
                    self.__class__.__name__, environment
                )
            )
        self.__environment = environment

    """
    All scheduled events use UTC time zone and the minimum precision 
    for schedules is 1 minute.
    UTC = -2h Amsterdam - Amsterdam is 2 hours ahead of
    Coordinated Universal Time
    """

    @stop_time.setter
    def stop_time(self, stop_time):
        if not stop_time:
            self.__stop_time = ""
            return

        if stop_time and (0 <= int(stop_time) <= 24):
            self.__stop_time = stop_time
        else:
            raise Exception(
                "{} invalid stop_time {}, valid value: 0 to 24 hrs".format(
                    self.__class__.__name__, stop_time
                )
            )

    @start_time.setter
    def start_time(self, start_time):
        if not start_time:
            self.__start_time = ""
            return

        if start_time and (0 <= int(start_time) <= 24):
            self.__start_time = start_time
        else:
            raise Exception(
                "{} Error: invalid start_time {}, valid value: 0 to 24 hrs".format(
                    self.__class__.__name__, start_time
                )
            )

    @security_groups.setter
    def security_groups(self, security_groups):
        sg = security_groups
        asg = self.account.security_groups
        self.__security_groups = [*sg, *asg]

    def valid_name(self, name):
        return not (
            self.MIN_LEN_NAME > len(name)
            or len(name) > self.MAX_LEN_NAME
            or not re.match(r"^[\w_-]+$", name)
        )


if __name__ == "__main__":
    pass
