import time
import modules.logs as logs
import modules.exceptions.exception as exception


class Instances:
    def __init__(self, account_provider, dispatcher):
        """
        :type account_provider: Aws
        """
        self.account_provider = account_provider
        self.dispatcher = dispatcher

    def get(self, instance_id):
        return self.account_provider.get_instance(instance_id)

    def list(self, filters=None):
        if filters is None:
            filters = {}
        instances = self.account_provider.list_instances(filters)
        return instances

    def list_images(self):
        return self.account_provider.list_images()

    def list_security_groups(self):
        return self.account_provider.list_security_groups()

    def list_owners(self):
        return self.account_provider.fetch_owners()

    def start(self, instance_id):
        logs.info(self.__class__.__name__, "start instance {}".format(instance_id))

        if not instance_id:
            raise Exception("Missing id")

        instance = self.account_provider.get_instance(instance_id)

        if instance.get("state") not in ("stopped"):
            raise Exception("Wrong state, Instance must be state stopped")

        self.account_provider.start()

        instance = self.account_provider.get_instance()

        try:
            self.account_provider.create_instance_dns_records(instance)
        except Exception as error:
            logs.warning(
                "Model", "create_dns_record failed because {}".format(error.args[0]),
            )
            raise exception.DnsRecordsTagsMissing(
                "create_dns_record failed because {}".format(error.args[0])
            )
        finally:
            try:
                self.dispatcher.send("info", {"event": "start", "resource": instance})
            except Exception as error:
                logs.warning("Model", "notify failed")
                pass

    def stop(self, instance_id):
        logs.info(self.__class__.__name__, "stop instance {}".format(instance_id))
        if not instance_id:
            raise Exception("Missing id")
        instance = self.account_provider.get_instance(instance_id)
        if instance.get("state") != "running":
            raise Exception("Instance is not running")

        self.account_provider.stop()
        instance = self.account_provider.get_instance()

        try:
            self.account_provider.remove_instance_dns_records(instance)
        except Exception as error:
            logs.warning("Model", "remove_dns_record failed")
            pass
        finally:
            try:
                self.dispatcher.send("info", {"event": "stop", "resource": instance})
            except Exception as error:
                logs.warning("Model", "notify failed")
                pass

    def terminate(self, instance_id):
        logs.info(
            self.__class__.__name__, "terminate instance {}".format(instance_id),
        )
        if not instance_id:
            raise Exception("Missing id")

        instance = self.account_provider.get_instance(instance_id)

        try:
            self.account_provider.remove_instance_dns_records(instance)
        except Exception as error:
            logs.warning("Model", "remove_dns_records failed")
            pass

        self.account_provider.terminate()

        try:
            self.dispatcher.send("info", {"event": "terminate", "resource": instance})
        except Exception as error:
            logs.warning("Model", "notify failed")
            pass

    def create(self, entity, platform_input_data=None):
        if platform_input_data:
            logs.info(
                self.__class__.__name__,
                "create platform {}".format(platform_input_data),
            )
        else:
            logs.info(
                self.__class__.__name__, "create instance {}".format(entity.attributes),
            )

        m = self.account_provider.find_by_name(entity.name)
        if len(m) > 0:
            raise Exception(
                "Instance Name alreay exist: {}, choose a different name".format(
                    entity.name
                )
            )

        entity.cloud_init = (
            self.account_provider.userdata_cloud_init_platform(platform_input_data)
            if platform_input_data
            else self.account_provider.userdata_cloud_init()
        )

        instance = self.account_provider.create(entity)
        self.account_provider.create_private_dns_record(instance)

        if instance.get("public_ip"):
            self.account_provider.create_public_dns_record(instance)

        self.dispatcher.send("info", {"event": "create", "resource": instance})

        return instance

    def update(self, entity):
        logs.info(
            self.__class__.__name__, "update instance {}".format(entity.attributes),
        )
        if entity.id is None:
            raise Exception("Instance does not exist on AWS")

        instance = self.account_provider.get_instance(entity.id)
        # dns_update_required = self._dns_update_required(instance, entity)

        m = self.account_provider.find_by_name(entity.name)

        if len(m) > 1 or (len(m) == 1 and m[0].get("id") != entity.id):
            logs.error(
                self.__class__.__name__,
                "Instance id {} cannot be updated with name: {}".format(
                    entity.id, entity.name
                ),
            )
            logs.error(
                self.__class__.__name__,
                "Instance Name {} already taken by id {}".format(
                    entity.name, m[0].get("id")
                ),
            )
            raise Exception(
                "Instance Name already exist, {} already taken by id {}, choose a different name".format(
                    entity.name, m[0].get("id")
                )
            )

        # if dns_update_required:
        self.account_provider.remove_instance_dns_records(instance)

        self.account_provider.update(entity)
        instance = self.account_provider.get_instance()

        # if dns_update_required:
        self.account_provider.create_instance_dns_records(instance)

        self.dispatcher.send("info", {"event": "update", "resource": instance})

    # @staticmethod
    # def _dns_update_required(instance, entity):
    #     return instance.get('state') == 'running' and entity.name != instance.get('name')

    def stop_tagged_instances(self, filters):
        filters.append({"Name": "instance-state-name", "Values": ["running"]})

        tagged_instances = self.account_provider.list_instances(filters)

        if not len(tagged_instances):
            return

        ids = []
        for instance in tagged_instances:
            ids.append(instance.get("id"))

            if instance.get("public_ip"):
                try:
                    self.account_provider.remove_public_dns_record(instance)
                except Exception as error:
                    logs.warning(
                        "Model",
                        "remove_public_dns_record failed, {}".format(error.args[0]),
                    )
                    pass

            try:
                self.account_provider.remove_private_dns_record(instance)
            except Exception as error:
                logs.warning(
                    "Model",
                    "remove_private_dns_record failed, {}".format(error.args[0]),
                )
                pass

            print(
                "{0} ({1}) has public ip {2}, private_ip {3}".format(
                    instance.get("name"),
                    instance.get("id"),
                    instance.get("public_ip"),
                    instance.get("private_ip"),
                )
            )

        print("Total tagged matches:", len(ids))
        self.account_provider.stop_instances(ids)
        self.dispatcher.send(
            "info", {"event": "stop_tagged_instances", "resources": ids}
        )

    def terminate_tagged_instances(self, filters):
        tagged_instances = self.account_provider.list_instances(filters)

        if not len(tagged_instances):
            return

        ids = []
        for instance in tagged_instances:
            ids.append(instance.get("id"))

            if instance.get("public_ip"):
                try:
                    self.account_provider.remove_public_dns_record(instance)
                except Exception as error:
                    logs.warning(
                        "Model",
                        "remove_public_dns_record failed, {}".format(error.args[0]),
                    )
                    pass

            try:
                self.account_provider.remove_private_dns_record(instance)
            except Exception as error:
                logs.warning(
                    "Model",
                    "remove_private_dns_record failed, {}".format(error.args[0]),
                )
                pass

            print(
                "{0} ({1}) has public ip {2}, private_ip {3}".format(
                    instance.get("name"),
                    instance.get("id"),
                    instance.get("public_ip"),
                    instance.get("private_ip"),
                )
            )
        print("Total tagged matches:", len(ids))
        self.account_provider.terminate_instances(ids)
        self.dispatcher.send(
            "info", {"event": "terminate_tagged_instances", "resources": ids}
        )

    def start_tagged_instances(self, filters):
        filters.append({"Name": "instance-state-name", "Values": ["stopped"]})

        tagged_instances = self.account_provider.list_instances(filters)
        logs.info(
            self.__class__.__name__,
            "Info: start_tagged_instances tagged_instances: {}".format(
                tagged_instances
            ),
        )

        if not len(tagged_instances):
            return

        ids = []
        for instance in tagged_instances:
            ids.append(instance.get("id"))

        self.account_provider.start_instances(ids)

        logs.info(
            self.__class__.__name__,
            "Info: start_tagged_instances sleeping 60 sec to get public ips",
        )
        time.sleep(60)
        logs.info(
            self.__class__.__name__, "Info: start_tagged_instances wake up from sleep",
        )

        for instance_id in ids:
            instance = self.account_provider.get_instance(instance_id)
            logs.info(
                self.__class__.__name__,
                "Info: start_tagged_instances instance: {}".format(instance),
            )

            try:
                self.account_provider.create_instance_dns_records(instance)
            except Exception as error:
                logs.warning("Model", "create_dns_record failed")
                pass

        self.dispatcher.send(
            "info", {"event": "start_tagged_instances", "resources": ids}
        )

    def create_image(self, instance_id, image_name):
        logs.info(self.__class__.__name__, "stop instance {}".format(instance_id))
        if not instance_id:
            raise Exception("Missing id")

        instance = self.account_provider.get_instance(instance_id)
        self.account_provider.create_image(image_name, instance)
        self.dispatcher.send(
            "info",
            {"event": "create_image", "name": image_name, "instance_id": instance_id,},
        )

    def set_ready_state(self, instance_id):
        logs.info(self.__class__.__name__, "set_ready_state {}".format(instance_id))
        if not instance_id:
            raise Exception("Missing id")

        self.account_provider.set_ready_state_tags(instance_id)
        self.dispatcher.send(
            "info", {"event": "set_ready_state", "instance_id": instance_id}
        )


if __name__ == "__main__":
    pass
