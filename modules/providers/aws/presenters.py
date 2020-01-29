"""
AWS Data Presenters
"""
from datetime import datetime


class AWSPresenter:

    SG_TAGS = {
        "name": "Name",
        "environment": "Environment",
        "role": "Role",
        "customer": "Customer",
    }

    IMAGE_TAGS_MAPPINGS = {
        "id": "ImageId",
        "name": "Name",
        "description": "Description",
        "creation_date": "CreationDate",
        "environment": "Environment",
        "role": "Role",
        "state": "State",
        "os": "OS",
        "version": "Version",
    }

    INSTANCE_TAGS_MAPPINGS = {
        "name": "Name",
        "public_dns": "PublicDns",
        "private_dns": "PrivateDns",
        "owner": "Owner",
        "environment": "Environment",
        "role": "Role",
        "stop_time": "StopTime",
        "start_time": "StartTime",
        "last_stop_at": "LastStopAt",
        "last_start_at": "LastStartAt",
        "weekend_off": "WeekendOff",
        "terminate_date": "TerminateDate",
        "terminate_time": "TerminateTime",
        "last_update_at": "LastUpdateAt",
        "ready_status": "ReadyStatus",
    }

    STATE_ACTIONS = {"running": ["stop"], "stopped": ["start", "terminate"]}

    def __init__(self, now=datetime.now()):
        self.now = now
        self.now_list = now.strftime("%d/%m/%Y %H:%M:%S").split(" ")
        self.now_date = self.now_list[0]
        self.now_hours = int(self.now_list[1][:2])
        self.now_min = int(self.now_list[1][3:5])

    def instances_list(self, describe_instances_response):
        """
        :param describe_instances_response:
        :param sort:
        :return: List
        """
        attributes = []
        stopped = {}
        running = {}
        terminated = {}

        for reservation in describe_instances_response.get("Reservations"):
            for instance in reservation.get("Instances"):
                tags = self.get_tracked_tags(
                    instance, self.INSTANCE_TAGS_MAPPINGS.values()
                )
                launch_time = (
                    instance.get("LaunchTime")
                    if str == type(instance.get("LaunchTime"))
                    else instance.get("LaunchTime").strftime("%d/%m/%Y %H:%M:%S")
                )
                owner = tags.get(self.INSTANCE_TAGS_MAPPINGS.get("owner"), "anonymous")
                data = {
                    "id": instance.get("InstanceId"),
                    "name": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("name")),
                    "public_dns": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("public_dns")
                    ),
                    "private_dns": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("private_dns")
                    ),
                    "owner": owner,
                    "state": instance.get("State").get("Name"),
                    "type": instance.get("InstanceType"),
                    "launch_time": launch_time,
                    "environment": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("environment")
                    ),
                    "stop_time": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("stop_time")),
                    "start_time": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("start_time")
                    ),
                    "last_stop_at": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("last_stop_at")
                    ),
                    "last_start_at": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("last_start_at")
                    ),
                    "terminate_date": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("terminate_date")
                    ),
                    "terminate_time": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("terminate_time")
                    ),
                    "last_update_at": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("last_update_at")
                    ),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "image_id": instance.get("ImageId"),
                    "key_name": instance.get("InstanceKeyName"),
                    "role": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("role")),
                    "actions": self.STATE_ACTIONS.get(
                        instance.get("State").get("Name"), []
                    ),
                    "ready_status": tags.get(
                        self.INSTANCE_TAGS_MAPPINGS.get("ready_status")
                    ),
                }
                state = data.get("state")
                if state in ["pending", "running"]:
                    if owner not in running:
                        running[owner] = []
                    running[owner].append(data)
                elif state in ["shutting-down", "terminated"]:
                    if owner not in terminated:
                        terminated[owner] = []
                    terminated[owner].append(data)
                else:
                    if owner not in stopped:
                        stopped[owner] = []
                    stopped[owner].append(data)

        running_sorted_owners = list(running.keys())
        running_sorted_owners.sort()
        stopped_sorted_owners = list(stopped.keys())
        stopped_sorted_owners.sort()
        terminated_sorted_owners = list(terminated.keys())
        terminated_sorted_owners.sort()

        for the_owner in running_sorted_owners:
            for the_instance in running.get(the_owner):
                attributes.append(the_instance)

        for the_owner in stopped_sorted_owners:
            for the_instance in stopped.get(the_owner):
                attributes.append(the_instance)

        for the_owner in terminated_sorted_owners:
            for the_instance in terminated.get(the_owner):
                attributes.append(the_instance)

        return attributes

    def instance(self, instance):
        """
        :param EC2 instance:
        :return: DICT
        """
        tags = self.get_tracked_tags(instance, self.INSTANCE_TAGS_MAPPINGS.values())
        instance_state = getattr(instance, "state", {}).get(
            self.INSTANCE_TAGS_MAPPINGS.get("name")
        )
        attributes = {
            "id": getattr(instance, "id", ""),
            "name": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("name")),
            "public_dns": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("public_dns")),
            "private_dns": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("private_dns")),
            "owner": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("owner")),
            "state": instance_state,
            "type": getattr(instance, "instance_type", ""),
            "launch_time": str(instance.launch_time),
            "environment": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("environment")),
            "stop_time": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("stop_time")),
            "start_time": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("start_time")),
            "last_stop_at": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("last_stop_at")),
            "last_start_at": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("last_start_at")),
            "terminate_date": tags.get(
                self.INSTANCE_TAGS_MAPPINGS.get("terminate_date")
            ),
            "terminate_time": tags.get(
                self.INSTANCE_TAGS_MAPPINGS.get("terminate_time")
            ),
            "last_update_at": tags.get(
                self.INSTANCE_TAGS_MAPPINGS.get("last_update_at")
            ),
            "private_ip": getattr(instance, "private_ip_address", ""),
            "public_ip": getattr(instance, "public_ip_address", ""),
            "image_id": getattr(instance, "image_id", ""),
            "key_name": getattr(instance, "key_name,", ""),
            "role": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("role")),
            "actions": self.STATE_ACTIONS.get(instance_state, []),
            "ready_status": tags.get(self.INSTANCE_TAGS_MAPPINGS.get("ready_status")),
        }

        return attributes

    def security_groups_list(self, describe_security_groups_response):
        """
        :param describe_security_groups_response:
        :return: List
        """
        attributes = []
        for security_group in describe_security_groups_response.get(
            "SecurityGroups", []
        ):
            tags = self.get_tracked_tags(security_group, self.SG_TAGS.values())
            attributes.append(
                {
                    "id": security_group.get("GroupId"),
                    "name": tags.get("Name", ""),
                    "group_name": security_group.get("GroupName", ""),
                    "environment": tags.get("Environment", ""),
                    "role": tags.get("Role", ""),
                    "ip_permissions": security_group.get("IpPermissions"),
                    "ip_permissions_egress": security_group.get("IpPermissionsEgress"),
                }
            )

        return attributes

    def images_list(self, describe_images_response):
        """
        :param describe_images_response:
        :return: List
        """
        attributes = []
        for ami in describe_images_response.get("Images"):
            tags = self.get_tracked_tags(ami, self.IMAGE_TAGS_MAPPINGS.values())
            attributes.append(
                {
                    "id": ami.get("ImageId"),
                    "name": tags.get("Name", ""),
                    "creation_date": ami.get(
                        self.IMAGE_TAGS_MAPPINGS.get("creation_date"), ""
                    ),
                    "environment": tags.get(
                        self.IMAGE_TAGS_MAPPINGS.get("environment"), ""
                    ),
                    "role": tags.get(self.IMAGE_TAGS_MAPPINGS.get("role"), ""),
                    "root_volume_size": self.root_device_size(
                        ami.get("BlockDeviceMappings")
                    ),
                    "state": ami.get(self.IMAGE_TAGS_MAPPINGS.get("state"), ""),
                    "os": tags.get(self.IMAGE_TAGS_MAPPINGS.get("os"), ""),
                    "version": tags.get(self.IMAGE_TAGS_MAPPINGS.get("version"), ""),
                }
            )
        return attributes

    def root_device_size(self, device_mappings):
        """
        :param device_mappings:
        :return: int
        """
        for device in device_mappings:
            if device.get("DeviceName") == "/dev/sda1":
                return device.get("Ebs").get("VolumeSize")
        return 0

    def get_tracked_tags(self, resource, tags_mapping):
        """
        :param resource:
        :param tags_mapping:
        :return: DICT
        """
        if isinstance(resource, dict) and "Tags" in resource:
            resource_tags = resource["Tags"]
        elif hasattr(resource, "tags"):
            resource_tags = resource.tags
        else:
            return {}

        tags = {
            tag["Key"]: tag["Value"]
            for tag in resource_tags
            if tag["Key"] in tags_mapping
        }

        return tags

    def fetch_resource_tags(self, resource, tags_to_fetch=None):
        tags = {}

        if "Tags" in resource:
            tags = {
                tag["Key"]: tag["Value"]
                for tag in resource.tags
                if tags_to_fetch is None or tag["Key"] in tags_to_fetch
            }
        return tags

    def get_resource_tags(self, entity):
        tags = []
        for i in self.INSTANCE_TAGS_MAPPINGS:
            attkey = self.INSTANCE_TAGS_MAPPINGS[i]
            attval = getattr(entity, i, None)
            if attval:
                tags.append({"Key": attkey, "Value": attval})
        return tags

    def get_instance_ready_status(self, launch_time, now=datetime.now()):
        self.now = now
        self.now_list = now.strftime("%d/%m/%Y %H:%M:%S").split(" ")
        self.now_date = self.now_list[0]
        self.now_hours = int(self.now_list[1][:2])
        self.now_min = int(self.now_list[1][3:5])

        instance_launch_time_list = launch_time.split(
            " "
        )  # launch_time="10/12/2019 17:24:17"
        print("instance_launch_time_list: {}".format(instance_launch_time_list))

        print(
            "self.now date: {}, hours: {}, min: {}".format(
                self.now_date, self.now_hours, self.now_min
            )
        )

        launch_date = instance_launch_time_list[0]
        launch_date_list = launch_date.split("/")
        year = int(launch_date_list[2])
        month = int(launch_date_list[1])
        day = int(launch_date_list[0])
        launch_hours = int(instance_launch_time_list[1][:2])
        launch_min = int(instance_launch_time_list[1][3:5])

        print(
            "Launch date: {}, hours: {}, min: {}".format(
                launch_date, launch_hours, launch_min
            )
        )

        if self.now_date == launch_date:
            laucnh_datetime = datetime(year, month, day, launch_hours, launch_min)
            date_time_difference = round(
                (self.now - laucnh_datetime).total_seconds() / 60
            )
            if date_time_difference <= 7:
                return "Bootstrapping Instance"

        return "Ready"

    def get_tag_filters(self, default_filters, filters=None):
        if default_filters is None and filters is None:
            raise Exception("{} Error: _set_tag_filter failed")

        if filters is None:
            return default_filters

        # custom_filters = [
        #     {
        #         'Name': "tag:{}".format(tag.capitalize()), 'Values': [filters.get(tag)]
        #     }
        #     for tag in ['owner', 'name']
        #     if filters.get(tag, None)
        # ]

        return default_filters + filters

    # def get_type(instance):
    #     return instance.describe_attribute('InstanceType')
