import json
import time
import unittest

import unittest.mock

# import mock

from modules.providers.aws.account import AwsAccountProvider as Provider
from modules.models.instances import Instances as Model
from modules.entities.instance import Instance as Entity
from modules.entities.account import Account as Account
from modules.providers.aws.notify import Dispatcher

from config.settings import Settings
3
import modules.logs as logs


class TestModelMachines(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super(TestModelInstances, self).__init__(methodName)
        self.settings = Settings()
        data = self.settings.accounts.get("engineering")
        self.account = Account(data, "frankfurt")
        self.model = Model(
            Provider(self.account, self.settings),
            Dispatcher(self.settings.config.get("sns")),
        )

    def test_update_name_fails_with_duplication(self):
        print("====================================================================")
        print("=============- test_update_name_fails_with_duplication =============")
        instance1 = self.create()
        instance2 = self.create()

        with self.assertRaises(Exception) as cm:
            self.update(
                {
                    "id": instance1.get("id"),
                    "name": instance2.get("name"),
                    "image_id": "ami-0151d8654227898e7",
                    "owner": "hector",
                    "environment": "test",
                    "type": "t2.small",
                    "terminate_date": "10-10-2020",
                    "terminate_time": "20",
                    "stop_time": "20",
                    "start_time": "8",
                    "account": "engineering",
                    "region": "frankfurt",
                }
            )
        self.assertRegex(cm.exception.args[0], "Instance Name already exist")

        #
        # updated_instance = self.model.provider.get_instance()
        #
        # self.assertEquals(original_instance.get('id'), updated_instance.get('id'))
        # self.assertNotEqual(original_instance.get('name'), updated_instance.get('name'))
        # self.assertNotEqual(original_instance.get('private_dns'), updated_instance.get('private_dns'))
        # self.assertNotEqual(original_instance.get('public_dns'), updated_instance.get('public_dns'))
        # self.assertEquals(updated_instance.get('name'), new_name)
        #
        # self.terminate(updated_instance.get('id'))

    def test_update_name_successfuly_upserts_dns_records(self):
        print("====================================================================")
        print("========= test_update_name_successfuly_upserts_dns_records =========")
        new_name = "test-update-name-dns-records-looks-ok"
        original_instance = self.create()

        self.update(
            {
                "id": original_instance.get("id"),
                "name": new_name,
                "image_id": "ami-0151d8654227898e7",
                "owner": "hector",
                "environment": "test",
                "type": "t2.small",
                "terminate_date": "10-10-2020",
                "terminate_time": "20",
                "stop_time": "20",
                "start_time": "8",
                "account": "engineering",
                "region": "frankfurt",
            }
        )

        updated_instance = self.model.account_provider.get_instance()

        self.assertEquals(original_instance.get("id"), updated_instance.get("id"))
        self.assertNotEqual(original_instance.get("name"), updated_instance.get("name"))
        self.assertNotEqual(
            original_instance.get("private_dns"), updated_instance.get("private_dns"),
        )
        self.assertNotEqual(
            original_instance.get("public_dns"), updated_instance.get("public_dns"),
        )
        self.assertEquals(updated_instance.get("name"), new_name)

        self.terminate(updated_instance.get("id"))

    def test_create_instances(self):
        pass
        # post_data = self._get_post_data()
        # post_data.update({'name': 'cloudinstances-unittest-1567585891589051000'})
        # instance = self.create(post_data)
        # post_data.update({'name': 'instance-new-10', 'environment': 'test'})
        # instance = self.create(post_data)

        # post_data.update({'name': 'instance-new-2', 'environment': 'prod'})
        # instance = self.create(post_data)
        #
        # post_data.update({'name': 'instance-new-3', 'environment': 'test'})
        # instance = self.create(post_data)
        #
        # post_data.update({'name': 'instance-new-4', 'environment': 'prod'})
        # instance = self.create(post_data)
        #
        # post_data.update({'name': 'instance-new-5', 'environment': 'test'})
        # instance = self.create(post_data)
        #
        # post_data.update({'name': 'instance-new-6', 'environment': 'prod'})
        # instance = self.create(post_data)
        #
        # post_data.update({'name': 'instance-new-7', 'environment': 'test'})
        # instance = self.create(post_data)

    # def test_instance_model_flow_1(self):
    #     return
    #     #instance_id = 'i-0210bf9709f400db2'
    #     instance = self.create(self._get_post_data())
    #     instance_id = instance.get('id')
    #     self.stop(instance_id)
    #     self.update(
    #         {
    #             'id': instance_id,
    #             'name': "CloudInstances-unittest-updated-stopped",
    #             'owner': 'hector',
    #             'image_id': "ami-07f1fbbff759e24dd",
    #             'environment': 'test',  # env = CloudInstances-api-test sets special tags
    #             'type': 't2.micro',
    #             'terminate_date': '10-10-2020',
    #             'terminate_time': '20',
    #             'stop_time': '20',
    #             'start_time': '8',
    #             "account": 'engineering',
    #             "region": 'frankfurt'
    #         }
    #     )
    #     instance1 = self.model.get(instance_id)
    #     print("Instance1: {}".format(instance1))
    #     self.start(instance_id)
    #     self.update(
    #         {
    #             'id': instance_id,
    #             'name': "CloudInstances-unittest-updated-running",
    #             'image_id': "ami-07f1fbbff759e24dd",
    #             'owner': 'hector',
    #             'environment': 'prod',  # env = CloudInstances-api-test sets special tags
    #             'type': 't2.micro',
    #             'terminate_date': '11-11-2020',
    #             'terminate_time': '21',
    #             'stop_time': '22',
    #             'start_time': '12',
    #             "account": 'engineering',
    #             "region": 'frankfurt'
    #         }
    #     )
    #     instance2 = self.model.get(instance_id)
    #     print("Instance2: {}".format(instance2))
    #     self.terminate(instance_id)
    #
    #     self.assertEqual(instance1.get('name'), 'cloudinstances-unittest-updated-stopped.eng.eiq.dev')
    #     self.assertEqual(instance1.get('environment'), 'test')
    #     self.assertEqual(instance1.get('terminate_date'), '10-10-2020')
    #     self.assertEqual(instance1.get('terminate_time'), '20')
    #     self.assertEqual(instance1.get('stop_time'), '20')
    #     self.assertEqual(instance1.get('start_time'), '8')
    #
    #     self.assertEqual(instance2.get('name'), 'cloudinstances-unittest-updated-running.eng.eiq.sh')
    #     self.assertEqual(instance2.get('environment'), 'prod')
    #     self.assertEqual(instance2.get('terminate_date'), '11-11-2020')
    #     self.assertEqual(instance2.get('terminate_time'), '21')
    #     self.assertEqual(instance2.get('stop_time'), '22')
    #     self.assertEqual(instance2.get('start_time'), '12')
    #
    # def test_list(self):
    #     return
    #     self.list()
    #     self.list(filters={'owner': 'hector'})

    @staticmethod
    def _get_post_data():
        return {
            "name": "CloudInstances-unittest-{}".format(time.time_ns()),
            "image_id": "ami-0151d8654227898e7",
            "owner": "hector",
            "environment": "test",  # env = CloudInstances-api-test sets special tags
            "type": "m4.2xlarge",
            "termination_date": "",
            "account": "engineering",
            "region": "frankfurt",
        }

    @staticmethod
    def _get_aws_response():
        with open("describe-images.json", "r") as f:
            data = json.load(f)

        return data

    @staticmethod
    def images_ids():
        return {
            "frankfurt": "ami-07f1fbbff759e24dd",
            "ireland": "ami-07683a44e80cd32c5",
            "virginia": "ami-02da3a138888ced85",
        }

    def create(self, post_data=None):
        if not post_data:
            post_data = {
                "name": "cloudinstance-unittest-{}".format(time.time_ns()),
                "image_id": "ami-0151d8654227898e7",
                "owner": "hector",
                "environment": "test",  # env = CloudInstances-api-test sets special tags
                "type": "t2.small",
                "termination_date": "",
                "account": "engineering",
                "region": "frankfurt",
            }
        print("\n\n########## CREATE ###########\n\n")
        entity = Entity(post_data, self.account)

        instance = self.model.create(entity)

        instance = self.model.account_provider.get_provider_resource(instance.get("id"))

        logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        logs.info(self.__class__.__name__, "wait_until_running")

        instance.wait_until_exists({"Name": "instance-id", "Values": [instance.id,]})

        while instance.state.get("Name") != "running":
            go_sleep(5, "state {}".format(instance.state))
            instance.reload()

        self.assertRegex(instance.get("id"), "i-")
        self.assertEquals(post_data.get("name"), instance.get("name"))
        print(instance)
        return instance

    def update(self, post_data):
        print("\n\n########## UPDATE ###########\n\n")
        entity = Entity(post_data, self.account)
        self.model.update(entity)

        # instance = self.model.provider.get_provider_resource(entity.id)

        # logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        # instance.reload()
        # logs.info(self.__class__.__name__, "instance reload state {}".format(instance.state))

        # return instance

    def stop(self, instance_id):
        print("\n\n########## STOP ###########\n\n")
        self.model.stop(instance_id)

        instance = self.model.account_provider.get_provider_resource(instance_id)

        logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        logs.info(self.__class__.__name__, "wait_until_stopped")

        instance.wait_until_stopped({"Name": "instance-id", "Values": [instance.id,]})

        while instance.state.get("Name") != "stopped":
            go_sleep(5, "state {}".format(instance.state))
            instance.reload()

        self.assertIn(instance.state.get("Name"), ["stopping", "stopped"])

    def start(self, instance_id):
        print("\n\n########## START ###########\n\n")
        self.model.start(instance_id)

        instance = self.model.account_provider.get_provider_resource(instance_id)

        logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        logs.info(self.__class__.__name__, "wait_until_running")

        instance.wait_until_running({"Name": "instance-id", "Values": [instance.id,]})

        while instance.state.get("Name") != "running":
            go_sleep(5, "state {}".format(instance.state))
            instance.reload()

        self.assertIn(instance.state.get("Name"), ["running", "pending"])

    def terminate(self, instance_id):
        print("\n\n########## TERMINATE ###########\n\n")
        self.model.terminate(instance_id)
        reloaded_instance = self.model.get(instance_id)
        state = reloaded_instance.get("state")
        self.assertIn(state, ["shutting-down", "terminated"])

    def list(self, filters=None):
        if filters is None:
            filters = {}

        instances = self.model.list(filters)
        self.assertIsInstance(instances, list)
        print(instances)

        images = self.model.list_images()
        self.assertIsInstance(images, list)
        print(images)

        security_groups = self.model.list_security_groups()
        self.assertIsInstance(security_groups, list)
        print(security_groups)

        owners = self.model.list_owners()
        self.assertIsInstance(owners, list)
        print(owners)


def go_sleep(sec, message):
    print(message)
    print("Go Sleep for {} seconds...".format(sec))
    time.sleep(sec)


if __name__ == "__main__":
    unittest.main()
