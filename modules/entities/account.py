import json
import os

'''
Account
name :string
region : string
'''


class Account:

    def __init__(self, account_map, region):
        """
        :type account_map: dict
        :type region: string
        """
        self.id = account_map.get('id')
        self.name = account_map.get('name')  # todo: add name attribute to the account node to settings json files
        self.regions = account_map.get('regions')
        self.region = region
        self.security_groups = account_map.get('security_groups').get(region, [])
        self.instance_profile = account_map.get('instance_profile', '')
        self.sts_role = account_map.get('sts_role', '')
        self.environments = account_map.get('environments')
        self.availability_zones = ['a','b','c']
        self.subnets = account_map.get('subnets', {})
        self.key_name = account_map.get('ssh_key', '')
        self.tag_filters = account_map.get('tag_filters', {})
        self.tag_role = account_map.get('tag_role')
        self.hosted_zones_ids = account_map.get('hosted_zone_ids')
        self.hosted_zone_names = account_map.get('hosted_zone_names')

    @property
    def name(self):
        return self.__name

    @property
    def region(self):
        return self.__region

    @property
    def availability_zones(self):
        return self.__availability_zones

    @property
    def subnets(self):
        return self.__subnets

    @property
    def environments(self):
        return self.__environments

    @property
    def security_groups(self):
        return self.__security_groups

    @name.setter
    def name(self, name):
        if not name:
            raise Exception("{}: Settings for account {} not found".format(self.__class__.__name__, name))
        self.__name = name

    @region.setter
    def region(self, region):
        if not region:
            raise Exception("{}: Region {} not enabled for this account".format(self.__class__.__name__, region))
        self.__region = self.regions.get(region)

    @environments.setter
    def environments(self, environments):
        if not environments:
            raise Exception("{}: Missing environments from settings".format(self.__class__.__name__))
        self.__environments = environments

    @availability_zones.setter
    def availability_zones(self, azs):
        self.__availability_zones = ["{}{}".format(self.__region, az) for az in azs]

    @subnets.setter
    def subnets(self, subnets):
        self.__subnets = {}
        if not subnets:
            raise Exception("{} Error: Missing subnets in config".format(self.__class__.__name__))

        for az in self.__availability_zones:
            if az in subnets and subnets.get(az):
                self.__subnets[az] = subnets.get(az)

        if not self.__subnets:
            raise Exception("{} Error: mapping subnets with availability_zones in region has failed".format(self.__class__.__name__))

    @security_groups.setter
    def security_groups(self, security_groups):
        if not security_groups or not isinstance(security_groups, list):
            raise Exception("{} Error: Missing security_groups in config".format(self.__class__.__name__))
        self.__security_groups = security_groups


if __name__ == '__main__':
    pass

