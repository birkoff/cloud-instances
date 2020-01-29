from modules.providers.aws.sts import AssumeRoleSession


class Users(object):
    def __init__(self, settings):
        """

        :type account: Account object
        :type settings: Settings object
        """
        self.settings = settings
        session = self._get_new_session(
            settings.get("account_name"), settings.get("role"), settings.get("region"),
        )
        self.iam = session.resource("iam")
        self.group = self.iam.Group("ec2manager")

    @staticmethod
    def _get_new_session(account_name, role, region):
        role_session = AssumeRoleSession(account_name, role, region)
        return role_session.session

    def _delete_ssh_public_key(self, username, user_ssh_key_id):
        return self.provider.delete_ssh_public_key(
            UserName=username, SSHPublicKeyId=user_ssh_key_id,
        )

    def _get_ssh_public_key(self, username, user_ssh_key_id):
        response = self.provider.get_ssh_public_key(
            UserName=username, SSHPublicKeyId=user_ssh_key_id, Encoding="SSH"
        )
        return response.get("SSHPublicKey").get("SSHPublicKeyBody")

    def _list_users(self):
        return self.provider.list_users(PathPrefix="/engineering/",)

    def _list_user_tags(self, username):
        return self.provider.list_user_tags(UserName=username)

    def _get_user_ssh_key_id(self, username):
        response = self.provider.list_ssh_public_keys(UserName=username)

        if "SSHPublicKeys" not in response or len(response["SSHPublicKeys"]) < 1:
            return None

        return response["SSHPublicKeys"][0]["SSHPublicKeyId"]

    def _upload_public_ssh_key(self, username, ssh_pub_key):
        return self.provider.upload_ssh_public_key(
            UserName=username, SSHPublicKeyBody=ssh_pub_key
        )

    def _get_display_name(self, username):
        tags_response = self._list_user_tags(username)

        display_name = None
        for tags in tags_response.get("Tags"):
            if tags.get("Key") == "DisplayName":
                display_name = tags.get("Value")
                break
        return display_name

    def fetch_owners(self):
        logs.info(
            self.__class__.__name__,
            "Download owners file from s3:{}/{} into {}".format(
                self.bucket_name, self.owners_file, self.save_path
            ),
        )
        try:
            master_settings = self.settings.accounts.get("master")
            session = self.get_new_session(
                master_settings.get("id"),
                master_settings.get("sts_role"),
                master_settings.get("region"),
            )

            s3_resource = session.resource("s3")  # bucket is on main account
            s3_resource.Bucket(self.bucket_name).download_file(
                self.owners_file, self.save_path
            )
        except ClientError as error:
            raise Exception(
                "Unable to download users.attributes from S3: {0}".format(
                    error.response["Error"]["Message"]
                )
            )

        try:
            with open(self.save_path, "r") as file:
                owners_list = file.read().split("\n")
        except Exception as error:
            raise Exception(
                "Unable read user attributes file: {0}, {1}".format(
                    self.save_path, error.args[0]
                )
            )

        return owners_list
