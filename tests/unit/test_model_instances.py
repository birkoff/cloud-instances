from modules.models.instances import Instances as InstancesModel

import unittest.mock
from unittest import mock


class TestModelInstances(unittest.TestCase):
    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    def test_get_instance(self, account_provider):
        model = InstancesModel(account_provider, None)
        model.get(123)
        assert account_provider.get_instance.called is True

    # @mock.patch('modules.providers.aws.account.AwsAccountProvider.list_instances', return_value='foo')
    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    def test_list_instances(self, account_provider):
        account_provider.list_instances.return_value = "foo-instances"
        model = InstancesModel(account_provider, None)
        assert model.list() == "foo-instances"

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    def test_list_images(self, account_provider):
        account_provider.list_images.return_value = "foo-images"
        model = InstancesModel(account_provider, None)
        assert model.list_images() == "foo-images"

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    def test_list_security_groups(self, account_provider):
        account_provider.list_security_groups.return_value = "foo-security-groups"
        model = InstancesModel(account_provider, None)
        assert model.list_security_groups() == "foo-security-groups"

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    def test_list_owners(self, account_provider):
        account_provider.fetch_owners.return_value = "foo-owners"
        model = InstancesModel(account_provider, None)
        assert model.list_owners() == "foo-owners"

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    def test_start(self, account_provider, dispatcher_function):
        account_provider.get_instance.return_value = {"state": "terminated"}
        invalid_model = InstancesModel(account_provider, dispatcher_function)

        with self.assertRaises(Exception) as cm:
            invalid_model.start(123)

        account_provider.get_instance.return_value = {"state": "stopped"}
        model = InstancesModel(account_provider, dispatcher_function)
        model.start(123)

        assert account_provider.get_instance.called is True
        assert account_provider.start.called is True
        assert account_provider.create_instance_dns_records.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    @mock.patch("modules.entities.instance.Instance")
    # @mock.patch('modules.models.instances.find_by_name')
    def test_create(self, account_provider, dispatcher_function, instance_entity):
        account_provider.find_by_name.return_value = []
        account_provider.userdata_cloud_init_platform.return_value = ""
        model = InstancesModel(account_provider, dispatcher_function)

        model.create(instance_entity)

        assert account_provider.find_by_name.called is True
        assert account_provider.userdata_cloud_init.called is True
        assert account_provider.create.called is True
        assert account_provider.create_private_dns_record.called is True
        assert account_provider.create_public_dns_record.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    @mock.patch("modules.entities.instance.Instance")
    def test_update(self, account_provider, dispatcher_function, instance_entity):
        model = InstancesModel(account_provider, dispatcher_function)
        instance_entity.id.return_value = "123"
        instance_entity.name.return_value = ""
        instance_entity.attributes.return_value = {}
        model.update(instance_entity)
        assert account_provider.get_instance.called is True
        assert account_provider.find_by_name.called is True
        assert account_provider.remove_instance_dns_records.called is True
        assert account_provider.update.called is True
        assert account_provider.create_instance_dns_records.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    def test_stop(self, account_provider, dispatcher_function):
        account_provider.get_instance.return_value = {"state": "terminated"}
        invalid_model = InstancesModel(account_provider, dispatcher_function)
        with self.assertRaises(Exception) as cm:
            invalid_model.stop(123)

        account_provider.get_instance.return_value = {
            "id": "i-123456789",
            "state": "running",
        }

        model = InstancesModel(account_provider, dispatcher_function)
        model.stop(123)

        assert account_provider.stop.called is True
        assert account_provider.get_instance.called is True
        assert account_provider.remove_instance_dns_records.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    def test_terminate(self, account_provider, dispatcher_function):
        account_provider.get_instance.return_value = {
            "id": "i-123456789",
            "state": "running",
        }

        model = InstancesModel(account_provider, dispatcher_function)
        model.terminate(123)

        assert account_provider.get_instance.called is True
        assert account_provider.remove_instance_dns_records.called is True
        assert account_provider.terminate.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    def test_stop_tagged_instances(self, account_provider, dispatcher_function):
        model = InstancesModel(account_provider, dispatcher_function)

        account_provider.list_instances.return_value = [
            {"id": "i-123456789", "name": "foo-bar", "public_ip": None}
        ]
        model.stop_tagged_instances(["i-123456"])
        assert (
            account_provider.remove_public_dns_record.called is False
        )  # No pub IP no need to remove record
        assert account_provider.remove_private_dns_record.called is True
        assert account_provider.stop_instances.called is True
        assert dispatcher_function.send.called is True

        account_provider.list_instances.return_value = [
            {"id": "i-123456789", "name": "foo-bar", "public_ip": "127.0.0.1"}
        ]
        model.stop_tagged_instances(["i-123456"])
        assert account_provider.remove_public_dns_record.called is True
        assert account_provider.remove_private_dns_record.called is True
        assert account_provider.stop_instances.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    def test_terminate_tagged_instances(self, account_provider, dispatcher_function):
        model = InstancesModel(account_provider, dispatcher_function)

        account_provider.list_instances.return_value = [
            {"id": "i-123456789", "name": "foo-bar", "public_ip": None}
        ]
        model.terminate_tagged_instances(["i-123456"])
        assert (
            account_provider.remove_public_dns_record.called is False
        )  # No pub IP no need to remove record
        assert account_provider.remove_private_dns_record.called is True
        assert account_provider.terminate_instances.called is True
        assert dispatcher_function.send.called is True

        account_provider.list_instances.return_value = [
            {"id": "i-123456789", "name": "foo-bar", "public_ip": "127.0.0.1"}
        ]

        model.terminate_tagged_instances(["i-123456"])

        assert account_provider.list_instances.called is True
        assert account_provider.remove_public_dns_record.called is True
        assert account_provider.remove_private_dns_record.called is True
        assert account_provider.terminate_instances.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    @mock.patch("time.sleep")
    def test_start_tagged_instances(
        self, account_provider, dispatcher_function, time_sleep_function
    ):
        model = InstancesModel(account_provider, dispatcher_function)

        account_provider.list_instances.return_value = [
            {"id": "i-123456789", "name": "foo-bar", "public_ip": "127.0.0.1"}
        ]
        time_sleep_function.return_value = 1

        model.start_tagged_instances(["i-123456"])

        assert account_provider.list_instances.called is True
        assert account_provider.start_instances.called is True
        assert account_provider.create_instance_dns_records.called is True
        assert dispatcher_function.send.called is True

    @mock.patch("modules.providers.aws.account.AwsAccountProvider")
    @mock.patch("modules.providers.aws.notify.Dispatcher")
    def test_create_image(self, account_provider, dispatcher_function):
        model = InstancesModel(account_provider, dispatcher_function)

        account_provider.get_instance.return_value = {
            "id": "i-123456789",
            "name": "foo-bar",
            "public_ip": "127.0.0.1",
        }
        model.create_image("foo-bar-image", ["i-123456"])

        assert account_provider.get_instance.called is True
        assert account_provider.create_image.called is True
        assert dispatcher_function.send.called is True
