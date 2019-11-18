from datetime import datetime
from datetime import timedelta

import unittest
import modules.entities.machine as Entity
from modules.settings import Settings
from modules.entities.account import Account


class TestMachineEntity(unittest.TestCase):

    def test_instance_entity_missing_name(self):
        account_settings, post_data = self.prepare()
        post_data.update({'name': ''})
        with self.assertRaises(Exception) as cm:
            Entity.Machine(post_data, account_settings)

        self.assertRegex(cm.exception.args[0], "Machine Error: Invalid name")

    def test_instance_entity_invalid_name(self):
        account_settings, post_data = self.prepare()

        post_data.update({'name': 'foo&baar'})
        with self.assertRaises(Exception) as cm:
            Entity.Machine(post_data, account_settings)
        self.assertRegex(cm.exception.args[0], "Machine Error: Invalid name")

        post_data.update({'name': 'fo'})
        with self.assertRaises(Exception) as cm:
            Entity.Machine(post_data, account_settings)
        self.assertRegex(cm.exception.args[0], "Machine Error: Invalid name")

    def test_instance_entity_error_owner(self):
        account_settings, post_data = self.prepare()
        post_data.update({'owner': ''})

        with self.assertRaises(Exception) as cm:
            Entity.Machine(post_data, account_settings)

        self.assertRegex(cm.exception.args[0], "Machine Error: missing argument owner")

    def test_instance_entity_error_image_id(self):
        account_settings, post_data = self.prepare()
        post_data.update({'image_id': ''})

        with self.assertRaises(Exception) as cm:
            Entity.Machine(post_data, account_settings)

        self.assertRegex(cm.exception.args[0], "Machine Error: missing argument image_id")

    def test_instance_entity_start_stop_time(self):
        account_settings, post_data = self.prepare()
        post_data.update({'stop_time': '20'})
        post_data.update({'start_time': '09'})
        instance = Entity.Machine(post_data, account_settings)
        self.assertEqual("20", instance.stop_time)
        self.assertEqual('09', instance.start_time)


    def test_instance_entity_success(self):
        account_settings, post_data = self.prepare()
        instance = Entity.Machine(self._get_post_data(), account_settings)
        self.assertIsNone(instance.id)
        self.assertEqual('cloudmachines-unittest.eng.', instance.name)
        self.assertEqual('eu-central-1', instance.region)
        self.assertListEqual(['sg-0730e485923f7f478'], instance.security_groups)
        self.assertEqual('arn:aws:iam::303555438846:instance-profile/admin/tip-services-profile',
                         instance.profile)
        self.assertEqual("test", instance.environment)
        self.assertEqual("unittest", instance.owner)
        self.assertEqual("t2.micro", instance.type)
        self.assertEqual("", instance.stop_time)
        self.assertEqual("", instance.start_time)
        self.assertEqual((datetime.now() + timedelta(days=2)).strftime('%d/%m/%Y'), instance.terminate_date)

        self.assertTrue(instance)

    def prepare(self):
        settings = Settings()
        account = Account(settings.accounts.get('engineering'), 'frankfurt')
        post_data = self._get_post_data()
        return account, post_data

    @staticmethod
    def _get_post_data():
        return {
            'name': "CloudMachines-unittest",
            'image_id': "ami-0000000001",
            'owner': 'unittest',
            'environment': 'test',  # env = CloudMachines-api-test sets special tags
            'type': 't2.micro',
            'termination_date': (datetime.now() + timedelta(days=2)).strftime('%d/%m/%Y'),
            'security_groups': [],
            "account": 'engineering',
            "region": 'frankfurt'
        }

if __name__ == '__main__':
    unittest.main()
