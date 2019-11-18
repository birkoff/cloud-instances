import json
import os

'''
Settings
name :string
region : string
'''


class Settings:

    def __init__(self):
        attributes = self._load_settings()
        self.config = attributes.get('config')
        self.accounts = attributes.get('accounts')
        self.cloud_config = self._load_cloud_config("cloud-config.conf")
        self.cloud_config_platform = self._load_cloud_config("cloud-config-platform.conf")
        print("Config: {} Accounts: {}, Cloud-Config: {}".format(self.config, self.accounts, self.cloud_config))

    @staticmethod
    def _load_settings():
        environment = os.environ.get('ENVIRONMENT', 'dev')
        try:
            with open("./config/settings.{}.json".format(environment), 'r') as f:
                data = json.load(f)
        except Exception as error:
            raise Exception("Cannot read ./config/settings.{}.json, {}".format(environment, error.__str__()))

        return data

    @staticmethod
    def _load_cloud_config(conf):
        try:
            with open("./config/%s" % conf, 'r') as f:
                cloud_init_file = f.read().split('\n')
        except Exception as error:
            raise Exception("Cannot read ./config/{}, {}".format(conf, error.__str__()))

        return '\n'.join(cloud_init_file)


if __name__ == '__main__':
    pass

