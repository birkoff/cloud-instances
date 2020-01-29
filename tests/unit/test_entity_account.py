from datetime import datetime
from datetime import timedelta

import unittest.mock
from unittest import mock
import modules.entities.account as Entity

account_map = {
            "id": "foo-bar-id",
            "name": "foo-bar",
            "enabled": True,
            "ssh_key": "foo-bar-key",
            "regions": {"frankfurt": "eu-central-1"},
            "subnets": {
                "eu-central-1a": "subnet-0000000001",
                "eu-central-1b": "subnet-0000000002",
                "eu-central-1c": "subnet-0000000003",
            },
            "security_groups": {"frankfurt": ["sg-0000000001"]},
            "tag_filters": {
                "instances": [{"Name": "tag:Role", "Values": ["foo-bar-instance-role"]}],
                "images": [{"Name": "tag:Role", "Values": ["foo-bar-image-tag"]}],
                "security_groups": [{"Name": "tag:Role", "Values": ["foo-bar-sg"]}],
            },
            "environments": ["dev", "test", "prod"],
            "tag_role": "foo-bar-tag",
            "hosted_zone_ids": {
                "public": "0000000001",
                "private": "0000000002",
            },
            "hosted_zone_names": {"public": "eng.eiq.sh", "private": "eng.eiq"},
            "instance_profile": "ec2manager-instance-profile-dev",
            "sts_role": "ec2manager-instance-sts-role-dev",
        }


class TestAccountEntity(unittest.TestCase):

    def test_instance_entity(self):
        region = "frankfurt"
        a = Entity.Account(account_map, region)
        self.assertEqual("foo-bar-id", a.id)
        self.assertEqual("foo-bar", a.name)
        self.assertEqual({"frankfurt": "eu-central-1"}, a.regions)
        self.assertEqual("eu-central-1", a.region)
        self.assertEqual(["sg-0000000001"], a.security_groups)
        self.assertEqual("ec2manager-instance-profile-dev", a.instance_profile)
        self.assertEqual("ec2manager-instance-sts-role-dev", a.sts_role)
        self.assertEqual(["dev", "test", "prod"], a.environments)
        # self.assertEqual("", a.availability_zones)
        # self.assertEqual("", a.subnets)
        # self.assertEqual(days_in_the_future, a.key_name)
        # self.assertEqual(days_in_the_future, a.tag_filters)
        # self.assertEqual(days_in_the_future, a.tag_role)
        # self.assertEqual(days_in_the_future, a.hosted_zones_ids)
        # self.assertEqual(days_in_the_future, a.hosted_zone_names)

        # post_data.update({"name": "invalid name"})
        # print(post_data)
        # with self.assertRaises(Exception) as cm:
        #     i_e = Entity.Instance(post_data, account_entity)
        # self.assertRegex(cm.exception.args[0], "Instance Invalid name")

    def test_create_entity_fails(self):
        region = "mexico"
        a = Entity.Account(account_map, region)


if __name__ == "__main__":
    unittest.main()
