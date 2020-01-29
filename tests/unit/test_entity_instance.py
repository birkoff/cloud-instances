from datetime import datetime
from datetime import timedelta

import unittest.mock
from unittest import mock
import modules.entities.instance as Entity


class TestInstanceEntity(unittest.TestCase):
    @mock.patch("modules.entities.account.Account")
    def test_instance_entity(self, account_entity):

        account_entity.id = "foo-bar-id"
        account_entity.name = "foo-bar-name"
        account_entity.sts_role = "foo-bar-role"

        account_entity.hosted_zone_names = {
            "public": "eng.eiq.sh",
            "private": "eng.eiq",
        }

        account_entity.hosted_zones_ids = (
            {"public": "XXXXXXXXXXXXXX", "private": "YYYYYYYYYYYYYY"},
        )

        account_entity.key_name = "foo-bar-key"

        account_entity.instance_profile = (
            "arn:aws:iam::303555438846:instance-profile/ec2manager/"
            "ec2manager-instance-profile-dev"
        )

        account_entity.subnets = {
            "eu-central-1a": "subnet-05ce5d59125be4c79",
            "eu-central-1b": "subnet-016c7e809551124d0",
            "eu-central-1c": "subnet-0659f26f419c24b88",
        }
        account_entity.region = "frankfurt"
        account_entity.tag_role = "ec2manager-test"
        account_entity.environments = ["test"]
        account_entity.availability_zones = ["a", "b", "c"]

        days_in_the_future = (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y")
        post_data = {
            "name": "CloudInstances-unittest",
            "image_id": "ami-0000000001",
            "owner": "unittest",
            "environment": "test",
            # env = CloudInstances-api-test sets special tags
            "type": "t2.micro",
            "termination_date": days_in_the_future,
            "security_groups": [],
            "account": "engineering",
            "region": "frankfurt",
        }

        e = Entity.Instance(post_data, account_entity)
        self.assertEqual("test", e.environment)
        self.assertEqual("cloudinstances-unittest", e.name)
        self.assertEqual("cloudinstances-unittest.eng.eiq.sh", e.public_dns)
        self.assertEqual("cloudinstances-unittest.eng.eiq", e.private_dns)
        self.assertEqual("unittest", e.owner)
        self.assertEqual("t2.micro", e.type)
        self.assertEqual("", e.stop_time)
        self.assertEqual("", e.start_time)
        self.assertEqual("", e.last_stop_at)
        self.assertEqual("", e.last_start_at)
        self.assertEqual(days_in_the_future, e.terminate_date)
        self.assertEqual("ami-0000000001", e.image_id)

        post_data.update({"name": "invalid name"})
        print(post_data)
        with self.assertRaises(Exception) as cm:
            i_e = Entity.Instance(post_data, account_entity)
        self.assertRegex(cm.exception.args[0], "Instance Invalid name")


if __name__ == "__main__":
    unittest.main()
