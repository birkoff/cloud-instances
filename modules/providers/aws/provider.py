import json
import time
from datetime import datetime
import boto3
from boto3 import Session
from botocore.exceptions import ClientError
import modules.logs as logs
import modules.providers.aws.presenters as Presenter


class Aws(object):
    now = datetime.now()
    owners_file = 'users.list'
    save_path = '/tmp/users.list'
    bucket_name = 'cloud-init'
    instance_attributes = {
        'type': 'instanceType',
        'protected': 'disableApiTermination'
    }

    def __init__(self, account, settings):
        """

        :type account: Account object
        :type settings: Settings object
        """
        self.settings = settings
        self.account = account

        session = self.get_new_session(account.id, account.sts_role, account.region)

        self.ec2_resource = session.resource('ec2')
        self.ec2_client = session.client('ec2')
        self.route53 = session.client('route53')

        self.hosted_zone_names = account.hosted_zone_names

        self.hosted_zone_ids = account.hosted_zones_ids

        self.machine_filters = account.tag_filters.get('instances')
        self.image_filters = account.tag_filters.get('images')
        self.security_groups_filters = account.tag_filters.get('security_groups')

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

    def get_machine(self, machine_id=None):
        logs.info(self.__class__.__name__, "get_machine {}".format(machine_id))
        if self.instance is None and machine_id is None:
            raise Exception("Machine is not set")
        elif self.instance is None and machine_id:
            self.set_machine(machine_id)
        self.instance.reload()
        return Presenter.machine(self.instance)

    # todo: fix
    def set_machine(self, machine_id):
        logs.info(self.__class__.__name__, "set_machine {}".format(machine_id))
        self.instance = self.ec2_resource.Instance(machine_id)

    def list_machines(self, filters=None):
        tags_filters = Presenter.get_tag_filters(self.machine_filters, filters)
        logs.info(self.__class__.__name__, "attributes instances by tags {}".format(tags_filters))
        self.instance_list = self.ec2_client.describe_instances(Filters=tags_filters)
        machines = Presenter.machines_list(self.instance_list)
        logs.info(self.__class__.__name__, "attributes found {} instances".format(len(machines)))
        return machines

    def list_images(self):
        logs.info(self.__class__.__name__, "attributes images by tags {}".format(self.image_filters))
        self.images_list = self.ec2_client.describe_images(Filters=self.image_filters)
        images = Presenter.images_list(self.images_list)
        logs.info(self.__class__.__name__, "attributes found {} images".format(len(images)))
        return images

    def list_security_groups(self):
        logs.info(self.__class__.__name__, "attributes security_groups by tags {}".format(self.security_groups_filters))
        self.security_groups_list = self.ec2_client.describe_security_groups(Filters=self.security_groups_filters)
        security_groups = Presenter.security_groups_list(self.security_groups_list)
        logs.info(self.__class__.__name__, "attributes found {} security_groups".format(len(security_groups)))
        return security_groups

    def start(self):
        logs.info(self.__class__.__name__, "start {}".format(self.instance))
        self.instance.start()
        self.instance.create_tags(
            Tags=[
                {
                    'Key': Presenter.INSTANCE_TAGS_MAPPINGS.get('last_start_at'),
                    'Value': self.now.strftime("%d/%m/%Y %H:%M:%S")
                }
            ]
        )
        # todo: fix
        self.instance = self.wait_for_public_ip(self.instance, 1)
        return Presenter.machine(self.instance)

    def stop(self):
        logs.info(self.__class__.__name__, "stop {}".format(self.instance))
        self.instance.stop()
        self.instance.create_tags(
            Tags=[
                {
                    'Key': Presenter.INSTANCE_TAGS_MAPPINGS.get('last_stop_at'),
                    'Value': self.now.strftime("%d/%m/%Y %H:%M:%S")
                }
            ]
        )

    def terminate(self):
        logs.info(self.__class__.__name__, "terminate {}".format(self.instance))
        self.instance.create_tags(
            Tags=[
                {
                    'Key': Presenter.INSTANCE_TAGS_MAPPINGS.get('terminate_date'),
                    'Value': self.now.strftime("%d/%m/%Y %H:%M:%S")
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
            Monitoring={
                'Enabled': False
            },
            Placement={
                'AvailabilityZone': entity.availability_zone,
            },
            UserData=entity.cloud_init,
            IamInstanceProfile={
                'Arn': entity.profile
            },
            DryRun=False,
            NetworkInterfaces=[
                {
                    'AssociatePublicIpAddress': True,
                    'DeleteOnTermination': True,
                    'DeviceIndex': 0,
                    'Groups': entity.security_groups,
                    'SubnetId': entity.subnet_id
                },
            ],
            InstanceInitiatedShutdownBehavior='stop',
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': Presenter.get_resource_tags(entity)
                }
            ]
        )
        logs.info(self.__class__.__name__, "instance created {}".format(created_instance[0]))
        self.instance = self.wait_for_public_ip(created_instance[0], 1)
        return Presenter.machine(self.instance)

    def create_image(self, name, machine):
        image = self.instance.create_image(
            Name=name,
            Description='Created with EC2Manager'
        )

        image.create_tags(
            Tags=[
                {
                    'Key': 'Role',
                    'Value': 'ec2manager'
                },
                {
                    'Key': 'Name',
                    'Value': name
                },
                {
                    'Key': 'Owner',
                    'Value': machine.get('owner')
                }
            ]
        )

        return

    def update(self, machine, entity):
        # if machine.get('type') != entity.type:
        #     self.modify_attribute('instanceType', entity.type)

        # if machine.get('protected') != entity.protected:
        #     self.modify_attribute('disableApiTermination', entity.protected)

        logs.info(self.__class__.__name__, "update {}".format(entity.attributes))
        self.instance.create_tags(
            Tags=Presenter.get_resource_tags(entity)
        )

    # @staticmethod
    # def is_protected(instance):
    #     return instance.describe_attribute('disableApiTermination')

    def stop_instances(self, instances_ids):
        self.ec2_client.stop_instances(
            InstanceIds=instances_ids,
            DryRun=False,
        )

        self.ec2_client.create_tags(
            DryRun=False,
            Resources=instances_ids,
            Tags=[
                {
                    'Key': Presenter.INSTANCE_TAGS_MAPPINGS.get('last_stop_at'),
                    'Value': "{} - scheduled".format(self.now.strftime("%d/%m/%Y %H:%M:%S"))
                }
            ]
        )

    def terminate_instances(self, instances_ids):
        self.ec2_client.terminate_instances(
            InstanceIds=instances_ids,
            DryRun=False,
        )

        self.ec2_client.create_tags(
            DryRun=False,
            Resources=instances_ids,
            Tags=[
                {
                    'Key': Presenter.INSTANCE_TAGS_MAPPINGS.get('terminate_date'),
                    'Value': "{} - scheduled".format(self.now.strftime("%d/%m/%Y %H:%M:%S"))
                }
            ]
        )

    def modify_attribute(self, attribute, value):
        if attribute not in self.instance_attributes.values():
            raise Exception("attribiute {} not allowed to modify".format(attribute))

        logs.info(self.__class__.__name__, "instance modify_attribute {} value {}".format(attribute, value))
        return self.instance.modify_attribute(attribute, value)

    def create_dns_records(self, machine):
        self.create_private_dns_record(machine)
        self.create_public_dns_record(machine)
        self.instance.create_tags(
            Tags=[
                {
                    'Key': Presenter.INSTANCE_TAGS_MAPPINGS.get('public_dns'),
                    'Value': machine.get('public_dns')
                },
                {
                    'Key': Presenter.INSTANCE_TAGS_MAPPINGS.get('private_dns'),
                    'Value': machine.get('private_dns')
                }
            ]
        )

    def create_public_dns_record(self, machine):
        logs.info(self.__class__.__name__, "create_dns_record {}".format(machine))
        self.dns_record('UPSERT', machine.get('public_dns'), machine.get('public_ip'), self.hosted_zone_ids.get('public'))

    def create_private_dns_record(self, machine):
        logs.info(self.__class__.__name__, "create_private_dns_record {}".format(machine))
        self.dns_record('UPSERT', machine.get('private_dns'), machine.get('private_ip'), self.hosted_zone_ids.get('private'))

    def remove_dns_records(self, machine):
        self.remove_private_dns_record(machine)
        self.remove_public_dns_record(machine)

    def remove_public_dns_record(self, machine):
        logs.info(self.__class__.__name__, "remove_public_dns_record {}".format(machine))
        self.remove_dns_record(machine.get('public_dns'), self.hosted_zone_ids.get('public'))

    def remove_private_dns_record(self, machine):
        logs.info(self.__class__.__name__, "remove_private_dns_record {}".format(machine))
        self.remove_dns_record(machine.get('private_dns'), self.hosted_zone_ids.get('private'))

    def remove_dns_record(self, name, hosted_zone_id):
        logs.info(self.__class__.__name__, "remove_dns_record {}".format(name))

        record_set = self.route53.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=name,
            StartRecordType='A',
            MaxItems='1'
        )
        record_sets = record_set.get('ResourceRecordSets')
        if not bool(record_sets):
            logs.info(self.__class__.__name__, "No record set found to delete".format(self.__class__.__name__))
            return

        if record_sets[0]['Name'] != "{0}.".format(name):
            logs.info(
                self.__class__.__name__,
                "Record names don't match, skipping deletion {} != {}".format(
                    record_sets[0]['Name'],
                    "{0}.".format(name)))
            return

        value = record_sets[0]['ResourceRecords'][0]['Value']
        self.dns_record('DELETE', name, value, hosted_zone_id)

    def dns_record(self, action, name, value, hosted_zone_id):
        logs.info(self.__class__.__name__, "{} change_resource_record_sets {} with value {}".format(action, name, value))
        self.route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Comment': "{} record set".format(action),
                'Changes': [
                    {
                        'Action': action,
                        'ResourceRecordSet': {
                            'Name': name,
                            'Type': 'A',
                            'TTL': 0,
                            'ResourceRecords': [
                                {
                                    'Value': value
                                },
                            ],
                        }
                    }
                ]
            }
        )

    def fetch_owners(self):
        logs.info(self.__class__.__name__, "Download owners file from s3:{}/{} into {}".format(self.bucket_name, self.owners_file, self.save_path))
        try:
            master_settings = self.settings.accounts.get("master")
            session = self.get_new_session(master_settings.get('id'), master_settings.get('sts_role'), master_settings.get('region'))

            s3_resource = session.resource('s3')  # bucket is on main account
            s3_resource.Bucket(self.bucket_name).download_file(self.owners_file, self.save_path)
        except ClientError as error:
            raise Exception("Unable to download users.attributes from S3: {0}".format(error.response['Error']['Message']))

        try:
            with open(self.save_path, 'r') as file:
                owners_list = file.read().split('\n')
        except Exception as error:
            raise Exception("Unable read user attributes file: {0}, {1}".format(self.save_path, error.args[0]))

        return owners_list

    def userdata_cloud_init(self):
        return self.settings.cloud_config

    def userdata_cloud_init_platform(self, platform_input_data):
        return self.settings.cloud_config_platform

    def notify(self, level, payload):
        sns_settings = self.settings.config.get('sns')

        session = self.get_new_session(
            sns_settings.get('account_name'),
            sns_settings.get('role'),
            sns_settings.get('region')
        )

        sns = session.client('sns')

        message = {
            "level": level,
            "payload": payload,
        }

        sns.publish(
            TargetArn=sns_settings.get('sns_topic_arn'),
            Message=json.dumps({'default': json.dumps(message)}),
            MessageStructure='json'
        )
        return

    def key_pair_exist(self, target_key):
        resp = self.ec2_client.describe_key_pairs()
        print('Checking if AWS key pair', target_key, 'exists')
        for kn in resp['KeyPairs']:
            key_name = kn['KeyName']
            if key_name == target_key:
                print('Found AWS Key Pair:', key_name)
                return True

        print('WARNING:', target_key, 'AWS Key Pair Not Found')
        return False

    def wait_for_public_ip(self, instance, iteration, required=False):
        logs.info(self.__class__.__name__, "wait_for_public_ip {} iteration {}".format(instance, iteration))
        limit = 10

        if iteration > limit:
            logs.info(self.__class__.__name__, "Failed to get public IP address".format(self.__class__.__name__))
            if required:
                raise Exception("{} Failed to get public IP address".format(self.__class__.__name__))
            return instance

        if not instance.public_ip_address and iteration <= limit:
            logs.info(self.__class__.__name__, "Cannot to get public IP address, retrying in 5 sec...".format(self.__class__.__name__))
            time.sleep(5)
            instance.reload()
            return self.wait_for_public_ip(instance, iteration + 1)

        logs.info(self.__class__.__name__, "Found instance.public_ip_address {}".format(instance.public_ip_address))
        return instance

    def get_new_session(self, account_name, role, region):
        client = boto3.client('sts')
        logs.info(self.__class__.__name__, "client.assume_role(RoleArn={}, RoleSessionName={})".format(role, account_name))
        try:
            response = client.assume_role(RoleArn=role, RoleSessionName=account_name)
        except ClientError as error:
            raise Exception(
                "An error occurred when calling the AssumeRole operation: Access denied to role {}".format(role))

        session = Session(aws_access_key_id=response['Credentials']['AccessKeyId'],
                          aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                          aws_session_token=response['Credentials']['SessionToken'],
                          region_name=region)

        return session
