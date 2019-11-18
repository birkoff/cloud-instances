import time
import modules.logs as logs

class Machines:

    def __init__(self, provider):
        self.provider = provider

    def get(self, machine_id):
        return self.provider.get_machine(machine_id)

    def list(self, filters=None):
        if filters is None:
            filters = {}
        machines = self.provider.list_machines(filters)
        return machines

    def list_images(self):
        return self.provider.list_images()

    def list_security_groups(self):
        return self.provider.list_security_groups()

    def list_owners(self):
        return self.provider.fetch_owners()

    def start(self, machine_id):
        logs.info(self.__class__.__name__, "start machine {}".format(machine_id))
        if not machine_id:
            raise Exception("Missing id")
        machine = self.provider.get_machine(machine_id)
        if machine.get('state') not in ('stopped'):
            raise Exception("Wrong state, Machine must be state stoped")
        self.provider.start()

        machine = self.provider.get_machine()

        try:
            self.provider.create_dns_records(machine)
        except Exception as error:
            logs.warning('Model', "create_dns_record failed")
            pass

        try:
            self.provider.notify('info', {"event": "start", "resource": machine})
        except Exception as error:
            logs.warning('Model', "notify failed")
            pass

    def stop(self, machine_id):
        logs.info(self.__class__.__name__, "stop machine {}".format(machine_id))
        if not machine_id:
            raise Exception("Missing id")
        machine = self.provider.get_machine(machine_id)
        if machine.get('state') != 'running':
            raise Exception("Machine is not running")

        self.provider.stop()
        machine = self.provider.get_machine()

        try:
            self.provider.remove_dns_records(machine)
        except Exception as error:
            logs.warning('Model', "remove_dns_record failed")
            pass

        try:
            self.provider.notify('info', {"event": "stop", "resource": machine})
        except Exception as error:
            logs.warning('Model', "notify failed")
            pass

    def terminate(self, machine_id):
        logs.info(self.__class__.__name__, "terminate machine {}".format(machine_id))
        if not machine_id:
            raise Exception("Missing id")

        machine = self.provider.get_machine(machine_id)

        try:
            self.provider.remove_dns_records(machine)
        except Exception as error:
            logs.warning('Model', "remove_dns_records failed")
            pass

        self.provider.terminate()

        try:
            self.provider.notify('info', {"event": "terminate", "resource": machine})
        except Exception as error:
            logs.warning('Model', "notify failed")
            pass

    def create(self, entity, platform_input_data=None):
        logs.info(self.__class__.__name__, "create machine {}".format(entity))
        logs.info(self.__class__.__name__, "create platform {}".format(platform_input_data))

        m = self.find_by_name(entity.name)
        if len(m) > 0:
            raise Exception("Machine Name alreay exist: {}, choose a different name".format(entity.name))

        entity.cloud_init = self.provider.userdata_cloud_init_platform(platform_input_data) if platform_input_data else self.provider.userdata_cloud_init()

        machine = self.provider.create(entity)
        self.provider.create_private_dns_record(machine)

        if machine.get('public_ip'):
            self.provider.create_public_dns_record(machine)

        self.provider.notify('info', {"event": "create", "resource": machine})

        return machine

    def update(self, entity):
        logs.info(self.__class__.__name__, "update machine {}".format(entity.attributes))
        if entity.id is None:
            raise Exception("Instance does not exist on AWS")

        machine = self.provider.get_machine(entity.id)
        dns_update_required = self._dns_update_required(machine, entity)

        m = self.find_by_name(entity.name)

        if len(m) > 1 or (len(m) == 1 and m[0].get('id') != entity.id):
            raise Exception("Machine Name alreay exist: {}, choose a different name".format(entity.name))

        if dns_update_required:
            self.provider.remove_private_dns_record(machine)
            self.provider.remove_public_dns_record(machine)

        self.provider.update(machine, entity)

        if dns_update_required:
            self.provider.create_private_dns_record(machine)
            self.provider.create_public_dns_record(machine)

        self.provider.notify('info', {"event": "update", "resource": machine})

    @staticmethod
    def _dns_update_required(machine, entity):
        return machine.get('state') == 'running' and entity.name != machine.get('name')

    def find_by_name(self, name):
        return self.provider.list_machines(
            [
                {
                    'Name': 'tag:Name',
                    'Values': [name]
                }
            ]
        )

    def stop_tagged_instances(self, filters):
        filters.append(
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        )

        tagged_instances = self.provider.list_machines(filters)

        ids = []
        for instance in tagged_instances:
            ids.append(instance.get('id'))

            if instance.get('public_ip'):
                try:
                    self.provider.remove_public_dns_record(instance)
                except Exception as error:
                    logs.warning('Model', "remove_public_dns_record failed, {}".format(error.args[0]))
                    pass

            try:
                self.provider.remove_private_dns_record(instance)
            except Exception as error:
                logs.warning('Model', "remove_private_dns_record failed, {}".format(error.args[0]))
                pass

            print('{0} ({1}) has public ip {2}, private_ip {3}'.format(instance.get('name'), instance.get('id'), instance.get('public_ip'), instance.get('private_ip')))

        print('Total tagged matches:', len(ids))
        if ids:
            self.provider.stop_instances(ids)
        return

    def terminate_tagged_instances(self, filters):
        tagged_instances = self.provider.list_machines(filters)

        ids = []
        for instance in tagged_instances:
            ids.append(instance.get('id'))

            if instance.get('public_ip'):
                try:
                    self.provider.remove_public_dns_record(instance)
                except Exception as error:
                    logs.warning('Model', "remove_public_dns_record failed, {}".format(error.args[0]))
                    pass

            try:
                self.provider.remove_private_dns_record(instance)
            except Exception as error:
                logs.warning('Model', "remove_private_dns_record failed, {}".format(error.args[0]))
                pass

            print('{0} ({1}) has public ip {2}, private_ip {3}'.format(instance.get('name'), instance.get('id'),
                                                                       instance.get('public_ip'),
                                                                       instance.get('private_ip')))
        print('Total tagged matches:', len(ids))
        if ids:
            self.provider.terminate_instances(ids)
        return

    def start_tagged_instances(self, filters):

        filters.append(
            {
                'Name': 'instance-state-name',
                'Values': ['stopped']
            }
        )

        tagged_instances = self.provider.list_machines(filters)

        ids = []
        for instance in tagged_instances:
            ids.append(instance.get('id'))

        if ids:
            self.provider.start_instances(ids)

        time.sleep(60)

        for instance_id in ids:
            machine = self.provider.get_machine(instance_id)

            try:
                self.provider.create_dns_records(machine)
            except Exception as error:
                logs.warning('Model', "create_dns_record failed")
                pass

    def create_image(self, machine_id, image_name):
        logs.info(self.__class__.__name__, "stop machine {}".format(machine_id))
        if not machine_id:
            raise Exception("Missing id")

        machine = self.provider.get_machine(machine_id)
        self.provider.create_image(image_name, machine)
        return


if __name__ == '__main__':
    pass
