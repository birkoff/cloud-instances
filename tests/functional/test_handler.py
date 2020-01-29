import unittest
import handler as Handler
import modules.logs as logs


class TestHandler(unittest.TestCase):
    #
    # def test_list_accounts(self):
    #     response = Handler.list_accounts(self.__get_event(), None)
    #     logs.info('test_list_accounts', "{}".format(response.__str__()))
    #     self.assertEqual(200, response.get('statusCode'))
    #     self.assertIn('body', response)
    #
    # def test_list_instances(self):
    #     response = Handler.list_instances(self.__get_event(), None)
    #     logs.info('test_list_instances', "{}".format(response.__str__()))
    #     self.assertEqual(200, response.get('statusCode'))
    #     self.assertIn('body', response)
    #
    # def test_list_images(self):
    #     response = Handler.list_images(self.__get_event(), None)
    #     logs.info('test_list_images', "{}".format(response.__str__()))
    #     self.assertEqual(200, response.get('statusCode'))
    #     self.assertIn('body', response)
    #
    # def test_list_security_groups(self):
    #     response = Handler.list_securitygroups(self.__get_event(), None)
    #     logs.info('test_list_security_groups', "{}".format(response.__str__()))
    #     self.assertEqual(200, response.get('statusCode'))
    #     self.assertIn('body', response)

    def test_info(self):
        response = Handler.info(self.__get_event(), None)
        logs.info("test_list_security_groups", "{}".format(response.__str__()))
        self.assertEqual(200, response.get("statusCode"))
        self.assertIn("body", response)

    def test_sync_users_owners(self):
        response = Handler.sync_users_owners(self.__get_event(), None)
        logs.info("test_sync_users_owners", "{}".format(response.__str__()))
        self.assertEqual(200, response.get("statusCode"))
        self.assertIn("body", response)

    @staticmethod
    def __get_event():
        return {
            "queryStringParameters": {"account": "engineering", "region": "frankfurt",}
        }

    # def test_stop_tagged_instances(self):
    #     Handler.stop_tagged_instances(None, None)
    #     return

    # def test_terminate_tagged_instances(self):
    #     Handler.terminate_tagged_instances(None, None)
    #     return
    # def test_info(self):
    #     event = {
    #         'queryStringParameters': {
    #             'account': 'engineering',
    #             'region': 'frankfurt',
    #         }
    #     }
    #
    #     response = Handler.info(event, None)
    #     print(response)
    #
    # def test_list_images(self):
    #     event = {
    #         'queryStringParameters': {
    #             'account': 'engineering',
    #             'region': 'frankfurt',
    #         }
    #     }
    #
    #     response = Handler.list_images(event, None)
    #     print(response)

    # def test_create(self):
    #     event_dic = json.loads(event['body'])
    #     account = event_dic.get('account', None)
    #     region = event_dic.get('region', None)
    #     account_settings = settings(account, region)
    #     instance_entity = InstanceEntity(event_dic, account_settings)
    #     instance_model = InstanceModel(Service(account_settings))
    #
    #     instance_entity.id = instance_model.create(instance_entity)
    #     return response.success(instance_entity)

    # def test_create_ami(self):
    #     event = {
    #         'body': {
    #             'name': "CloudInstances-AMI",
    #             'id': "ami-07f1fbbff759e24dd",
    #             'owner': 'hector',
    #             'environment': 'test',  # env = CloudInstances-api-test sets special tags
    #             'type': 't2.micro',
    #             'termination_date': '',
    #             "account": 'engineering',
    #             "region": 'frankfurt'
    #         }
    #     }
    #     event_dic = json.loads(event['body'])
    #     account = event_dic.get('account', None)
    #     region = event_dic.get('region', None)
    #     account_settings = settings(account, region)
    #     instance_entity = InstanceEntity(event_dic, account_settings)
    #     instance_model = InstanceModel(Service(account_settings))
    #
    #     instance_entity.id = instance_model.create(instance_entity)
    #     return response.success(instance_entity)

    # def test_update(self):
    #     event_dic = json.loads(event['body'])
    #     account = event_dic.get('account', None)
    #     region = event_dic.get('region', None)
    #     account_settings = settings(account, region)
    #     instance_entity = InstanceEntity(event_dic, account_settings)
    #     instance_model = InstanceModel(Service(account_settings))
    #     instance_model.update(instance_entity)
    #     return response.success(instance_entity)
    #
    # def test_start(self):
    #     event_dic = json.loads(event['body'])
    #     account = event_dic.get('account', None)
    #     region = event_dic.get('region', None)
    #     id = event_dic.get('id', None)
    #     instance_model = InstanceModel(Service(settings(account, region)))
    #     instance_model.start(id)
    #     return response.success(instance_entity)
    #
    # def test_stop(self):
    #     event_dic = json.loads(event['body'])
    #     account = event_dic.get('account', None)
    #     region = event_dic.get('region', None)
    #     id = event_dic.get('id', None)
    #     instance_model = InstanceModel(Service(settings(account, region)))
    #     instance_model.stop(id)
    #     return response.success(instance_entity)
    #
    # def test_terminate(self):
    #     event_dic = json.loads(event['body'])
    #     account = event_dic.get('account', None)
    #     region = event_dic.get('region', None)
    #     id = event_dic.get('id', None)
    #     instance_model = InstanceModel(Service(settings(account, region)))
    #     instance_model.terminate(id)
    #     return response.success(instance_entity)


if __name__ == "__main__":
    unittest.main()
