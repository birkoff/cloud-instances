import json

from settings import Settings
from modules.entities.account import Account
from modules.entities.machine import Machine as Instance
from modules.models.machines import Machines as Instances
from modules.providers.aws.provider import Aws as Provider

import datetime as dt
from datetime import datetime

import modules.logs as logs
import modules.response as Response


def _build_instance_model(account_name, region, settings=None):
    if settings is None:
        try:
            settings = Settings()
        except Exception as error:
            logs.info('Handler', "Error getting settings {}".format(error.args[0]))
            raise Exception("Error getting settings, {}".format(error.args[0]))

    account_map = settings.accounts.get(account_name)

    if not account_map.get('enabled', False):
        raise Exception("Error {} is set enabled: false".format(account_name))

    account = Account(account_map, region)
    instances = Instances(Provider(account, settings))
    return (account, instances)


def list_instances(event, context):
    if 'queryStringParameters' not in event or event.get('queryStringParameters') is None:
        return Response.error("Missing required parameters: account, region")

    account_name = event.get('queryStringParameters').get('account', None)
    region = event.get('queryStringParameters').get('region', None)

    owner = event.get('queryStringParameters').get('owner', None)

    logs.info('Handler', "list_instances: {}, {}, {}".format(account_name, region, owner))

    filters = []
    if owner:
        filters.append({'Name': 'tag:Owner','Values': [owner]})

    try:
        _, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: list_instances setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        instances_list = instances.list(filters)
    except Exception as error:
        logs.info('Handler', "Error: list_instances {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success(instances_list)


def create(event, context):
    if 'body' not in event or event.get('body') is None:
        return Response.error("Missing required parameters: account, region, id")

    event = json.loads(event.get('body'))

    account_name = event.get('account', None)
    region = event.get('region', None)

    logs.info('Handler', "create: {}, {}".format(account_name, region))

    try:
        account, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: create setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        instances.create(Instance(event, account))
    except Exception as error:
        return Response.error(error.args[0])

    return Response.success("ok")


def create_platform(event, context):
    if 'body' not in event or event.get('body') is None:
        return Response.error("Missing required parameters: account, region, id")

    event = json.loads(event.get('body'))

    account_name = event.get('account', None)
    region = event.get('region', None)

    logs.info('Handler', "create: {}, {}".format(account_name, region))

    try:
        account, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: create setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        instances.create(Instance(event, account), event.get('platform'))
    except Exception as error:
        return Response.error(error.args[0])

    return Response.success("ok")


def update(event, context):
    if 'body' not in event or event.get('body') is None:
        return Response.error("Missing required parameters: account, region, id")

    event = json.loads(event.get('body'))

    account_name = event.get('account', None)
    region = event.get('region', None)

    logs.info('Handler', "update: {}, {}".format(account_name, region))

    try:
        account, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: update setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        entity = Instance(event, account)
        instances.update(entity)
    except Exception as error:
        logs.info('Handler', "Error: update {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success("ok")


def start(event, context):
    if 'body' not in event or event.get('body') is None:
        return Response.error("Missing required parameters: account, region, id")

    event = json.loads(event.get('body'))

    account_name = event.get('account', None)
    region = event.get('region', None)
    instance_id = event.get('id', None)

    logs.info('Handler', "start: {}, {}, {}".format(account_name, region, instance_id))

    try:
        _, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: start setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        instances.start(instance_id)
    except Exception as error:
        logs.info('Handler', "Error: Start Machine {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success("ok")


def stop(event, context):
    if 'body' not in event or event.get('body') is None:
        return Response.error("Missing required parameters: account, region, id")

    event = json.loads(event.get('body'))

    account_name = event.get('account', None)
    region = event.get('region', None)
    instance_id = event.get('id', None)

    logs.info('Handler', "stop: {}, {}, {}".format(account_name, region, instance_id))

    try:
        _, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: stop setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        instances.stop(instance_id)
    except Exception as error:
        logs.info('Handler', "Error: stop {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success("ok")


def terminate(event, context):
    if 'body' not in event or event.get('body') is None:
        return Response.error("Missing required parameters: account, region, id")

    event = json.loads(event.get('body'))

    account_name = event.get('account', None)
    region = event.get('region', None)
    instance_id = event.get('id', None)

    logs.info('Handler', "terminate: {}, {}, {}".format(account_name, region, instance_id))

    try:
        _, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: list_images setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        instances.terminate(instance_id)
    except Exception as error:
        logs.info('Handler', "Error: list_images {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success("ok")


def info(event, context):
    if 'queryStringParameters' not in event or event.get('queryStringParameters') is None:
        return Response.error("Missing required parameters: account, region")

    account_name = event.get('queryStringParameters').get('account', None)
    region = event.get('queryStringParameters').get('region', None)

    logs.info('Handler', "info: {}, {}".format(account_name, region))

    try:
        account, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: info setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        owners = instances.list_owners()
    except Exception as error:
        logs.info('Handler', "Error: info {}".format(error.args[0]))
        return Response.error(error.args[0])

    response = {'users': owners, 'environments': account.environments}
    return Response.success(response)


def list_images(event, context):
    if 'queryStringParameters' not in event or event.get('queryStringParameters') is None:
        return Response.error("Missing required parameters: account, region")

    account_name = event.get('queryStringParameters').get('account', None)
    region = event.get('queryStringParameters').get('region', None)

    logs.info('Handler', "list_images: {}, {}".format(account_name, region))

    try:
        _, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: list_images setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:

        images = instances.list_images()
    except Exception as error:
        logs.info('Handler', "Error: list_images {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success(images)


def list_securitygroups(event, context):
    if 'queryStringParameters' not in event or event.get('queryStringParameters') is None:
        return Response.error("Missing required parameters: account, region")

    account_name = event.get('queryStringParameters', {}).get('account', None)
    region = event.get('queryStringParameters', {}).get('region', None)

    logs.info('Handler', "list_securitygroups: {}, {}".format(account_name, region))

    try:
        _, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: list_securitygroups setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        securitygroups = instances.list_security_groups()
    except Exception as error:
        logs.info('Handler', "Error: list_securitygroups {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success(securitygroups)


def list_accounts(event, context):
    settings = Settings()
    astngs = []
    for k, v in settings.accounts.items():
        if v.get('enabled', False):
            astngs.append(v)

    return Response.success(astngs)


def stop_tagged_instances(event, context):
    current_hour = dt.datetime.today().hour
    try:
        settings = Settings()
    except Exception as error:
        logs.info('Handler', "Error getting settings {}".format(error.args[0]))
        return Response.error(error.args[0])

    for account_name in settings.accounts:
        account_config = settings.accounts.get(account_name)
        for region in account_config.get('regions'):

            try:
                _, instances = _build_instance_model(account_name, region, settings)
            except Exception as error:
                logs.info('Handler', "Error: stop_tagged_instances setup {}".format(error.args[0]))
                continue
                pass

            try:
                instances.stop_tagged_instances(
                    [
                        {"Name": "tag:StopTime", "Values": [str(current_hour)]}
                    ]
                )
            except Exception as error:
                logs.info('Handler', "Error: stop_tagged_instances {}".format(error.args[0]))
                continue
                pass

    return Response.success("ok")


def terminate_tagged_instances(event, context):
    current_date = datetime.now().strftime("%d/%m/%Y")
    try:
        settings = Settings()
    except Exception as error:
        logs.info('Handler', "Error getting settings {}".format(error.args[0]))
        return Response.error(error.args[0])

    for account_name in settings.accounts:
        account_config = settings.accounts.get(account_name)
        for region in account_config.get('regions'):

            try:
                _, instances = _build_instance_model(account_name, region, settings)
            except Exception as error:
                logs.info('Handler', "Error: terminate_tagged_instances setup {}".format(error.args[0]))
                continue
                pass

            try:
                instances.terminate_tagged_instances(
                    [
                        {"Name": "tag:TerminateDate", "Values": [str(current_date)]},
                    ]
                )
            except Exception as error:
                logs.info('Handler', "Error: terminate_tagged_instances {}".format(error.args[0]))
                continue
                pass

    return Response.success("ok")


def start_tagged_instances(event, context):
    current_hour = dt.datetime.today().hour
    try:
        settings = Settings()
    except Exception as error:
        logs.info('Handler', "Error getting settings {}".format(error.args[0]))
        return Response.error(error.args[0])

    for account_name in settings.accounts:
        account_config = settings.accounts.get(account_name)
        for region in account_config.get('regions'):

            try:
                _, instances = _build_instance_model(account_name, region, settings)
            except Exception as error:
                logs.info('Handler', "Error: stop_tagged_instances setup {}".format(error.args[0]))
                continue
                pass

            try:
                instances.start_tagged_instances(
                    [
                        {"Name": "tag:StartTime", "Values": [str(current_hour)]}
                    ]
                )
            except Exception as error:
                logs.info('Handler', "Error: stop_tagged_instances {}".format(error.args[0]))
                continue
                pass

    return Response.success("ok")


def create_image(event, context):
    if 'body' not in event or event.get('body') is None:
        return Response.error("Missing required parameters: account, region, id")

    event = json.loads(event.get('body'))

    account_name = event.get('account', None)
    region = event.get('region', None)
    instance_id = event.get('id', None)
    image_name = event.get('image_name', None)

    logs.info('Handler', "start: {}, {}, {}".format(account_name, region, instance_id))

    try:
        _, instances = _build_instance_model(account_name, region)
    except Exception as error:
        logs.info('Handler', "Error: start setup {}".format(error.args[0]))
        return Response.error(error.args[0])

    try:
        instances.create_image(instance_id, image_name)
    except Exception as error:
        logs.info('Handler', "Error: Start Machine {}".format(error.args[0]))
        return Response.error(error.args[0])

    return Response.success("ok")
