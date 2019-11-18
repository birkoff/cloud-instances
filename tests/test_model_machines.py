import json
import time
import unittest

from modules.providers.aws.provider import Aws as Provider
from modules.models.machines import Machines as Model
from modules.entities.machine import Machine as Entity
from modules.entities.account import Account as Account
from settings import Settings

import modules.logs as logs


class TestModelMachines(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(TestModelMachines, self).__init__(methodName)
        self.settings = Settings()
        data = self.settings.accounts.get('engineering')
        self.account = Account(data, 'frankfurt')
        self.model = Model(Provider(self.account, self.settings))

    def test_create_instances(self):
        post_data = self._get_post_data()
        self.create(post_data)

    def test_machine_model_flow_1(self):
        machine = self.create(self._get_post_data())
        machine_id = machine.get('id')
        self.stop(machine_id)
        self.update(
            {
                'id': machine_id,
                'name': "CloudMachines-unittest-updated-stopped",
                'owner': 'hector',
                'image_id': "ami-07f1fbbff759e24dd",
                'environment': 'test',  # env = CloudMachines-api-test sets special tags
                'type': 't2.micro',
                'terminate_date': '10-10-2020',
                'terminate_time': '20',
                'stop_time': '20',
                'start_time': '8',
                "account": 'engineering',
                "region": 'frankfurt'
            }
        )
        machine1 = self.model.get(machine_id)
        print("Machine1: {}".format(machine1))
        self.start(machine_id)
        self.update(
            {
                'id': machine_id,
                'name': "CloudMachines-unittest-updated-running",
                'image_id': "ami-07f1fbbff759e24dd",
                'owner': 'hector',
                'environment': 'prod',  # env = CloudMachines-api-test sets special tags
                'type': 't2.micro',
                'terminate_date': '11-11-2020',
                'terminate_time': '21',
                'stop_time': '22',
                'start_time': '12',
                "account": 'engineering',
                "region": 'frankfurt'
            }
        )
        machine2 = self.model.get(machine_id)
        print("Machine2: {}".format(machine2))
        self.terminate(machine_id)

        self.assertEqual(machine1.get('name'), 'cloudmachines-unittest-updated-stopped.eng.')
        self.assertEqual(machine1.get('environment'), 'test')
        self.assertEqual(machine1.get('terminate_date'), '10-10-2020')
        self.assertEqual(machine1.get('terminate_time'), '20')
        self.assertEqual(machine1.get('stop_time'), '20')
        self.assertEqual(machine1.get('start_time'), '8')

        self.assertEqual(machine2.get('name'), 'cloudmachines-unittest-updated-running.eng.')
        self.assertEqual(machine2.get('environment'), 'prod')
        self.assertEqual(machine2.get('terminate_date'), '11-11-2020')
        self.assertEqual(machine2.get('terminate_time'), '21')
        self.assertEqual(machine2.get('stop_time'), '22')
        self.assertEqual(machine2.get('start_time'), '12')

    def test_list(self):
        return
        self.list()
        self.list(filters={'owner': 'hector'})

    @staticmethod
    def _get_post_data():
        return {
            'name': "CloudMachines-unittest-{}".format(time.time_ns()),
            'image_id': "ami-0151d8654227898e7",
            'owner': 'hector',
            'environment': 'test',  # env = CloudMachines-api-test sets special tags
            'type': 'm4.2xlarge',
            'termination_date': '',
            "account": 'engineering',
            "region": 'frankfurt'
        }

    @staticmethod
    def _get_aws_response():
        with open('describe-images.json', 'r') as f:
            data = json.load(f)

        return data

    @staticmethod
    def images_ids():
        return {
            'frankfurt': 'ami-07f1fbbff759e24dd',
            'ireland': 'ami-07683a44e80cd32c5',
            'virginia': 'ami-02da3a138888ced85'
        }

    def create(self, post_data):
        print("\n\n########## CREATE ###########\n\n")
        entity = Entity(post_data, self.account)
        machine = self.model.create(entity, {'some': 'data'})

        instance = self.model.provider.get_provider_resource(machine.get('id'))

        logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        logs.info(self.__class__.__name__, "wait_until_running")

        instance.wait_until_exists({
            'Name': 'instance-id',
            'Values': [
                instance.id,
            ]
        })

        while instance.state.get('Name') != 'running':
            go_sleep(5, "state {}".format(instance.state))
            instance.reload()

        self.assertRegex(machine.get('id'), 'i-')
        print(machine)
        return machine

    def update(self, post_data):
        print("\n\n########## UPDATE ###########\n\n")
        entity = Entity(post_data, self.account)
        self.model.update(entity)

        instance = self.model.provider.get_provider_resource(entity.id)

        logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        instance.reload()
        logs.info(self.__class__.__name__, "instance reload state {}".format(instance.state))

        return instance

    def stop(self, machine_id):
        print("\n\n########## STOP ###########\n\n")
        self.model.stop(machine_id)

        instance = self.model.provider.get_provider_resource(machine_id)

        logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        logs.info(self.__class__.__name__, "wait_until_stopped")

        instance.wait_until_stopped({
            'Name': 'instance-id',
            'Values': [
                instance.id,
            ]
        })

        while instance.state.get('Name') != 'stopped':
            go_sleep(5, "state {}".format(instance.state))
            instance.reload()

        self.assertIn(instance.state.get('Name'), ['stopping', 'stopped'])

    def start(self, machine_id):
        print("\n\n########## START ###########\n\n")
        self.model.start(machine_id)

        instance = self.model.provider.get_provider_resource(machine_id)

        logs.info(self.__class__.__name__, "instance state {}".format(instance.state))
        logs.info(self.__class__.__name__, "wait_until_running")

        instance.wait_until_running({
            'Name': 'instance-id',
            'Values': [
                instance.id,
            ]
        })

        while instance.state.get('Name') != 'running':
            go_sleep(5, "state {}".format(instance.state))
            instance.reload()

        self.assertIn(instance.state.get('Name'), ['running', 'pending'])

    def terminate(self, machine_id):
        print("\n\n########## TERMINATE ###########\n\n")
        self.model.terminate(machine_id)
        reloaded_machine = self.model.get(machine_id)
        state = reloaded_machine.get('state')
        self.assertIn(state, ['shutting-down', 'terminated'])

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


if __name__ == '__main__':
    unittest.main()
