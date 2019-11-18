import json
import unittest
from unittest.mock import patch

import modules.providers.aws.presenters as presenter


class TestPresentersAws(unittest.TestCase):

    def test_security_groups_list(self):
        response = presenter.security_groups_list(self.describe_security_groups())
        self.assertEqual(13, len(response))
        self.log_response(response, 'test_security_groups_list')

    def test_machines_list(self):
        response = presenter.machines_list(self.describe_instances())
        self.assertEqual(140, len(response))
        self.log_response(response, 'test_machines_list')

    def test_images_list(self):
        response = presenter.images_list(self.describe_images())
        self.assertEqual(13, len(response))
        self.log_response(response, 'test_images_list')

    def test_machine(self,):
        instance = type(
            'ec2.Instance',
            (object,),
            dict(
                id = '999',
                name = 'foo',
                owner = 'unittest',
                state = dict(Name='running'),
                instance_type = 'micro',
                launch_time = 'datetime',
                environment = 'test',
                stop_time = '18',
                start_time = '08',
                termination_date = '10-10-10',
                private_ip = '10.20.30.40',
                public_ip = '50.60.70.80',
                image_id = 'ami-0000000000001',
                key_name = 'KeyName',
                role = 'tags.role',
                actions = ['stop', 'terminate']
            )
        )
        response = presenter.machine(instance)
        # self.assertEqual(1, response)
        self.log_response(response, 'test_machine')

    def log_response(self, response, test):
        print("Class: {} \nTest: {}\nResponse Len: {}\nResponse Data: {}\n\n".format(
            self.__class__.__name__,
            test,
            len(response),
            response
        ))

    @staticmethod
    def describe_security_groups():
        with open('files/describe-security-groups.json', 'r') as f:
            data = json.load(f)

        return data

    @staticmethod
    def describe_images():
        with open('files/describe-images.json', 'r') as f:
            data = json.load(f)

        return data

    @staticmethod
    def describe_instances():
        with open('files/describe-instances.json', 'r') as f:
            data = json.load(f)

        return data

if __name__ == '__main__':
    unittest.main()
