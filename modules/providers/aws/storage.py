import json
import modules.logs as logs
import boto3
from botocore.exceptions import ClientError


class Storage(object):
    def __init__(self, config):
        """

        :type account: Account object
        :type settings: Settings.config map
        """
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(config.get("dynamodb").get("table"))
        logs.info("Storage", "Table {}".format(config.get("dynamodb").get("table")))
        self.s3 = boto3.resource("s3")
        self.bucket = self.s3.Bucket(config.get("s3").get("bucket"))
        logs.info("Storage", "s3 {}".format(config.get("s3").get("bucket")))

    def list_all_owners(self):
        response = self.table.get_item(Key={"ID": "owners"})
        print(response)

        if "Item" in response:
            item = response["Item"]
            print("GetItem succeeded:")
            print(json.dumps(item, indent=4))
            owners = item.get("attributes")
            print(owners)

            return owners

    def store_owners_lists(self, owners_list):
        try:
            response = self.table.get_item(Key={"ID": "owners"})
            print(response)
        except ClientError as e:
            print(e.response["Error"]["Message"])
        else:
            if "Item" in response:
                item = response["Item"]
                print("GetItem succeeded:")
                print(json.dumps(item, indent=4))
                owners = item.get("attributes")
                print(owners)

                response = self.table.update_item(
                    Key={"ID": "owners"},
                    UpdateExpression="set attributes = :o",
                    ExpressionAttributeValues={":o": owners_list},
                    ReturnValues="UPDATED_NEW",
                )
            else:
                print("GetItem did not succeeded")
                response = self.table.put_item(
                    Item={"ID": "owners", "attributes": owners_list}
                )
                print(response)
                return

    def store_ssh_keys(self, all_users):
        with open("/tmp/init.sh_template", "w") as output:
            output.write('DEVUSER="dev"\n')
            for owner in all_users:
                output.write(
                    'echo "{}" >> /home/$DEVUSER/.ssh/authorized_keys\n'.format(
                        all_users[owner]
                    )
                )

        self.bucket.upload_file(
            "/tmp/init.sh_template", "init.sh", ExtraArgs={"ACL": "public-read"},
        )

    def store_raw_keys(self, ssh_keys):
        try:
            response = self.table.get_item(Key={"ID": "ssh_keys"})
            print(response)
        except ClientError as e:
            print(e.response["Error"]["Message"])
        else:
            if "Item" in response:
                item = response["Item"]
                print("GetItem succeeded:")
                print(json.dumps(item, indent=4))
                cache_keys = item.get("attributes")
                print(cache_keys)

                if cache_keys == ssh_keys:
                    print("No need for update")
                    return

                response = self.table.update_item(
                    Key={"ID": "ssh_keys"},
                    UpdateExpression="set attributes = :o",
                    ExpressionAttributeValues={":o": ssh_keys},
                    ReturnValues="UPDATED_NEW",
                )
            else:
                response = self.table.put_item(
                    Item={"ID": "ssh_keys", "attributes": ssh_keys}
                )
                print(response)
                return

    # IAM users sync
    # def sync_pub_ssh_keys(self, all_keys):
    #     response = self._list_users()
    #
    #     for user in response.get('Users'):
    #         username = user.get('UserName')
    #         display_name = self._get_display_name(username)
    #         if not display_name or display_name not in all_keys:
    #             print("No found a matching key for {} named {} data: {}".format(username, display_name,
    #                                                                             all_keys.get(display_name)))
    #             return
    #
    #         print("found a matching key for {} named {} data: {}".format(username, display_name, all_keys.get(display_name)))
    #
    #         user_ssh_key_id = self._get_user_ssh_key_id(username=username)
    #
    #         if user_ssh_key_id:
    #             iam_key = self._get_ssh_public_key(username, user_ssh_key_id)
    #             git_key = all_keys.get(display_name)
    #             p = git_key.find(' ', 18)  # just for security
    #             clean_git_key = (git_key[:p])
    #             if iam_key == clean_git_key:
    #                 print("{} IAM ssh key is identical as GIT, nothing to do... ")
    #                 return
    #
    #             if iam_key != clean_git_key:
    #                 print("IAM ssh key is different than GIT... ")
    #                 print("Remove IAM ssh key... ")
    #                 self._delete_ssh_public_key(username, user_ssh_key_id)
    #
    #         print("{} does not have ssh key on AWS... ".format(username))
    #         print("Upload GIT key to IAM ssh key... ")
    #         try:
    #             upload_response = self._upload_public_ssh_key(
    #                 username=username,
    #                 ssh_pub_key=all_keys.get(display_name)
    #             )
    #         except Exception as error:
    #             print("Error Importing ssh key: ".format(error.args[0]))
    #             pass
    #
    #         print(upload_response)

    # def needs_update(self, ssh_keys_list):
    #     pass

    # def _list_users_in_group(self, param):
    #     return self.provider.
