import time
from datetime import datetime
import modules.logs as logs
import modules.exceptions.exception as exception
from modules.providers.aws.sts import assume_role_session
from modules.providers.aws.presenters import AWSPresenter as Presenter


class AwsAccountProvider(object):
    now = datetime.now()
    owners_file = "users.list"
    save_path = "/tmp/users.list"
    bucket_name = "cloud-init"
    instance_attributes = {
        "type": "instanceType",
        "protected": "disableApiTermination",
    }

    def __init__(self, account_entity, settings):
        """
        :type account_entity: Account Entity
        :type settings: Settings object
        """
        self.settings = settings
        self.account = account_entity
        self.presenter = Presenter()
        logs.info(
            "AWSAccountProvider", "account_entity = {}".format(account_entity.__dict__),
        )
        logs.info(
            "AWSAccountProvider", "account_entity.id = {}".format(account_entity.id),
        )
        logs.info(
            "AWSAccountProvider",
            "account_entity.sts_role = {}".format(account_entity.sts_role),
        )
        logs.info(
            "AWSAccountProvider",
            "account_entity.region = {}".format(account_entity.region),
        )
        session = self.get_new_session(
            account_entity.id, account_entity.sts_role, account_entity.region
        )

        self.ec2_resource = session.resource("ec2")
        self.ec2_client = session.client("ec2")
        self.route53 = session.client("route53")

        self.hosted_zone_names = account_entity.hosted_zone_names

        self.hosted_zone_ids = account_entity.hosted_zones_ids

        self.instance_filters = account_entity.tag_filters.get("instances")
        self.image_filters = account_entity.tag_filters.get("images")
        self.security_groups_filters = account_entity.tag_filters.get("security_groups")

        # Attributes set after object Creation
        # AWS Resource Only when start, stop, terminate, create, create_image
        self.instance = None

        # [] Only when list, stop_tagged_instances, terminate_tagged_instances, start_tagged_instances
        self.instance_list = None

        # [] Only when list_images
        self.images_list = None

        # [] Only when list_security_groups
        self.security_groups_list = None

    def get_provider_resource(self, instance_id):
        return self.ec2_resource.Instance(instance_id)

    def get_instance(self, instance_id=None):
        logs.info(self.__class__.__name__, "get_instance {}".format(instance_id))

        if self.instance is None and instance_id is None:
            raise Exception("Instance is not set")
        elif instance_id:
            self.instance = self.ec2_resource.Instance(instance_id)

        self.instance.reload()
        return self.presenter.instance(self.instance)

    def find_by_name(
        self, name, state_names=("pending", "running", "stopping", "stopped")
    ):
        """
        :type name: str
        :type state_names: list
        """
        # state_names
        # 0:  pending
        # 16: running
        # 32: shutting - down
        # 48: terminated
        # 64: stopping
        # 80: stopped

        filter = [{"Name": "tag:Name", "Values": [name]}]

        if state_names:
            filter.append({"Name": "instance-state-name", "Values": state_names})

        return self.list_instances(filter)

    # todo: add integration test
    def list_instances(self, filters=None):
        tags_filters = self.presenter.get_tag_filters(self.instance_filters, filters)
        logs.info(
            self.__class__.__name__,
            "attributes instances by tags {}".format(tags_filters),
        )
        self.instance_list = self.ec2_client.describe_instances(Filters=tags_filters)
        instances = self.presenter.instances_list(self.instance_list)
        logs.info(
            self.__class__.__name__,
            "attributes found {} instances".format(len(instances)),
        )
        return instances

    def list_images(self):
        logs.info(
            self.__class__.__name__,
            "attributes images by tags {}".format(self.image_filters),
        )
        self.images_list = self.ec2_client.describe_images(Filters=self.image_filters)
        images = self.presenter.images_list(self.images_list)
        logs.info(
            self.__class__.__name__, "attributes found {} images".format(len(images)),
        )
        return images

    def list_security_groups(self):
        logs.info(
            self.__class__.__name__,
            "attributes security_groups by tags {}".format(
                self.security_groups_filters
            ),
        )
        self.security_groups_list = self.ec2_client.describe_security_groups(
            Filters=self.security_groups_filters
        )
        security_groups = self.presenter.security_groups_list(self.security_groups_list)
        logs.info(
            self.__class__.__name__,
            "attributes found {} security_groups".format(len(security_groups)),
        )
        return security_groups

    def start(self):
        logs.info(self.__class__.__name__, "start {}".format(self.instance))
        self.instance.start()
        self.instance.create_tags(
            Tags=[
                {
                    "Key": self.presenter.INSTANCE_TAGS_MAPPINGS.get("last_start_at"),
                    "Value": self.now.strftime("%d/%m/%Y %H:%M:%S"),
                }
            ]
        )
        self.instance = self.wait_for_public_ip(self.instance, 1)
        return self.presenter.instance(
            self.instance
        )  # Fetch info again so it includes up-to-date data

    def stop(self):
        logs.info(self.__class__.__name__, "stop {}".format(self.instance))
        self.instance.stop()
        self.instance.create_tags(
            Tags=[
                {
                    "Key": self.presenter.INSTANCE_TAGS_MAPPINGS.get("last_stop_at"),
                    "Value": self.now.strftime("%d/%m/%Y %H:%M:%S"),
                }
            ]
        )

    def terminate(self):
        logs.info(self.__class__.__name__, "terminate {}".format(self.instance))
        self.instance.create_tags(
            Tags=[
                {
                    "Key": self.presenter.INSTANCE_TAGS_MAPPINGS.get("terminate_date"),
                    "Value": self.now.strftime("%d/%m/%Y %H:%M:%S"),
                }
            ]
        )
        self.instance.terminate()

    def create(self, entity):
        logs.info(self.__class__.__name__, "create {}".format(entity.attributes))
        created_instance = self.ec2_resource.create_instances(
            ImageId=entity.image_id,
            InstanceType=entity.type,
            KeyName=entity.key_name,
            MaxCount=1,
            MinCount=1,
            Monitoring={"Enabled": False},
            Placement={"AvailabilityZone": entity.availability_zone,},
            UserData=entity.cloud_init,
            IamInstanceProfile={"Arn": entity.profile},
            DryRun=False,
            NetworkInterfaces=[
                {
                    "AssociatePublicIpAddress": True,
                    "DeleteOnTermination": True,
                    "DeviceIndex": 0,
                    "Groups": entity.security_groups,
                    "SubnetId": entity.subnet_id,
                },
            ],
            InstanceInitiatedShutdownBehavior="stop",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": self.presenter.get_resource_tags(entity),
                }
            ],
        )
        logs.info(
            self.__class__.__name__, "instance created {}".format(created_instance[0]),
        )
        self.instance = self.wait_for_public_ip(created_instance[0], 1)
        return self.presenter.instance(self.instance)

    def create_image(self, name, instance):
        image = self.instance.create_image(
            Name=name, Description="Created with EC2Manager"
        )

        image.create_tags(
            Tags=[
                {"Key": "Role", "Value": "ec2manager"},
                {"Key": "Name", "Value": name},
                {"Key": "Owner", "Value": instance.get("owner")},
            ]
        )

        return

    def update(self, entity):
        logs.info(self.__class__.__name__, "update {}".format(entity.attributes))
        self.instance.create_tags(Tags=self.presenter.get_resource_tags(entity))
        self.instance.reload()

    # @staticmethod
    # def is_protected(instance):
    #     return instance.describe_attribute('disableApiTermination')

    def stop_instances(self, instances_ids):
        self.ec2_client.stop_instances(
            InstanceIds=instances_ids, DryRun=False,
        )

        self.ec2_client.create_tags(
            DryRun=False,
            Resources=instances_ids,
            Tags=[
                {
                    "Key": self.presenter.INSTANCE_TAGS_MAPPINGS.get("last_stop_at"),
                    "Value": "{} - scheduled".format(
                        self.now.strftime("%d/%m/%Y %H:%M:%S")
                    ),
                }
            ],
        )

    def start_instances(self, instances_ids):
        logs.info(self.__class__.__name__, "start_instances {}".format(instances_ids))

        self.ec2_client.start_instances(
            InstanceIds=instances_ids, DryRun=False,
        )

        self.ec2_client.create_tags(
            DryRun=False,
            Resources=instances_ids,
            Tags=[
                {
                    "Key": self.presenter.INSTANCE_TAGS_MAPPINGS.get("last_start_at"),
                    "Value": "{} - scheduled".format(
                        self.now.strftime("%d/%m/%Y %H:%M:%S")
                    ),
                }
            ],
        )

    def terminate_instances(self, instances_ids):
        logs.info(
            self.__class__.__name__, "terminate_instances {}".format(instances_ids),
        )

        self.ec2_client.terminate_instances(
            InstanceIds=instances_ids, DryRun=False,
        )

        self.ec2_client.create_tags(
            DryRun=False,
            Resources=instances_ids,
            Tags=[
                {
                    "Key": self.presenter.INSTANCE_TAGS_MAPPINGS.get("terminate_date"),
                    "Value": "{} - scheduled".format(
                        self.now.strftime("%d/%m/%Y %H:%M:%S")
                    ),
                }
            ],
        )

    def set_ready_state_tags(self, instance_id):
        logs.info(
            self.__class__.__name__, "set_ready_state_tags {}".format(instance_id),
        )
        self.ec2_client.create_tags(
            DryRun=False,
            Resources=[instance_id],
            Tags=[
                {
                    "Key": self.presenter.INSTANCE_TAGS_MAPPINGS.get("ready_status"),
                    "Value": "Ready",
                }
            ],
        )

    def modify_attribute(self, attribute, value):
        if attribute not in self.instance_attributes.values():
            raise Exception("attribiute {} not allowed to modify".format(attribute))

        logs.info(
            self.__class__.__name__,
            "instance modify_attribute {} value {}".format(attribute, value),
        )
        return self.instance.modify_attribute(attribute, value)

    def create_instance_dns_records(self, instance):
        self.create_private_dns_record(instance)
        self.create_public_dns_record(instance)

    def remove_instance_dns_records(self, instance):
        self.remove_private_dns_record(instance)
        self.remove_public_dns_record(instance)

    def create_public_dns_record(self, instance):
        logs.info(self.__class__.__name__, "create_dns_record {}".format(instance))

        if not instance.get("public_dns"):
            raise exception.DnsRecordsTagsMissing(
                "public_dns missing from instance, fix it by updating it (click update->save)"
            )

        self.dns_record(
            "UPSERT",
            instance.get("public_dns"),
            instance.get("public_ip"),
            self.hosted_zone_ids.get("public"),
        )

    def create_private_dns_record(self, instance):
        logs.info(
            self.__class__.__name__, "create_private_dns_record {}".format(instance),
        )

        if not instance.get("private_dns"):
            raise exception.DnsRecordsTagsMissing(
                "private_dns missing from instance, fix it by updating it (click Edit -> Update)"
            )

        self.dns_record(
            "UPSERT",
            instance.get("private_dns"),
            instance.get("private_ip"),
            self.hosted_zone_ids.get("private"),
        )

    def remove_public_dns_record(self, instance):
        logs.info(
            self.__class__.__name__, "remove_public_dns_record {}".format(instance),
        )
        self.remove_dns_record(
            instance.get("public_dns"), self.hosted_zone_ids.get("public")
        )

    def remove_private_dns_record(self, instance):
        logs.info(
            self.__class__.__name__, "remove_private_dns_record {}".format(instance),
        )
        self.remove_dns_record(
            instance.get("private_dns"), self.hosted_zone_ids.get("private")
        )

    def remove_dns_record(self, name, hosted_zone_id):
        logs.info(self.__class__.__name__, "remove_dns_record {}".format(name))

        record_set = self.route53.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=name,
            StartRecordType="A",
            MaxItems="1",
        )
        record_sets = record_set.get("ResourceRecordSets")
        if not bool(record_sets):
            logs.info(
                self.__class__.__name__,
                "No record set found to delete".format(self.__class__.__name__),
            )
            return

        if record_sets[0]["Name"] != "{0}.".format(name):
            logs.info(
                self.__class__.__name__,
                "Record names don't match, skipping deletion {} != {}".format(
                    record_sets[0]["Name"], "{0}.".format(name)
                ),
            )
            return

        value = record_sets[0]["ResourceRecords"][0]["Value"]
        self.dns_record("DELETE", name, value, hosted_zone_id)

    def dns_record(self, action, name, value, hosted_zone_id):
        if value is None or name is None:
            logs.info(
                self.__class__.__name__,
                "dns_record name is {} and value is {}".format(name, value),
            )
            return

        logs.info(
            self.__class__.__name__,
            "{} change_resource_record_sets {} with value {}".format(
                action, name, value
            ),
        )
        self.route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                "Comment": "{} record set".format(action),
                "Changes": [
                    {
                        "Action": action,
                        "ResourceRecordSet": {
                            "Name": name,
                            "Type": "A",
                            "TTL": 0,
                            "ResourceRecords": [{"Value": value},],
                        },
                    }
                ],
            },
        )

    def userdata_cloud_init(self):
        return self.settings.cloud_config

    def userdata_cloud_init_platform(self, platform_input_data):
        return self.settings.cloud_config_platform

    def key_pair_exist(self, target_key):
        resp = self.ec2_client.describe_key_pairs()
        print("Checking if AWS key pair", target_key, "exists")
        for kn in resp["KeyPairs"]:
            key_name = kn["KeyName"]
            if key_name == target_key:
                print("Found AWS Key Pair:", key_name)
                return True

        print("WARNING:", target_key, "AWS Key Pair Not Found")
        return False

    def wait_for_public_ip(self, instance, iteration, required=False):
        logs.info(
            self.__class__.__name__,
            "wait_for_public_ip {} iteration {}".format(instance, iteration),
        )
        limit = 10

        if iteration > limit:
            logs.info(
                self.__class__.__name__,
                "Failed to get public IP address".format(self.__class__.__name__),
            )
            if required:
                raise Exception(
                    "{} Failed to get public IP address".format(self.__class__.__name__)
                )
            return instance

        if not instance.public_ip_address and iteration <= limit:
            logs.info(
                self.__class__.__name__,
                "Cannot to get public IP address, retrying in 5 sec...".format(
                    self.__class__.__name__
                ),
            )
            time.sleep(5)
            instance.reload()
            return self.wait_for_public_ip(instance, iteration + 1)

        logs.info(
            self.__class__.__name__,
            "Found instance.public_ip_address {}".format(instance.public_ip_address),
        )
        return instance

    def get_new_session(self, account_name, role, region):
        logs.info(
            "AwsAccountProvider",
            "assume_role_session({}, {}, {})".format(account_name, role, region),
        )
        return assume_role_session(account_name, role, region)
