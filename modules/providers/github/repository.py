from json import loads

import urllib3


class Users:
    def __init__(self, config):
        self.repo_url = config.get("repo_url").rstrip("/") + "/"
        self.contents_url = config.get("contents_url").rstrip("/") + "/"
        self.headers = {
            "Authorization": "token " + config.get("github_token"),
            "Accept": "application/vnd.github.v3.raw",
            "User-Agent": "ec2manager",
        }
        self.http = urllib3.PoolManager()

    def github_auth_handler(self, req_id):
        expected_id = str()

        if expected_id == req_id:
            return True
        else:
            return False

    def get_repo_contents(self, path):
        resp = self.http.request("GET", path, headers=self.headers)

        if (100 <= resp.status < 600) and (resp.status != 200):
            raise ConnectionError("Error: Bad response", resp.status)

        contents = loads(resp.data.decode("utf-8"))

        return contents

    def fetch_users(self):
        contents = self.get_repo_contents(self.contents_url)

        dirs = []

        user_keys = {}
        admin_keys = {}  # these users will be added to every instance

        for each in contents:
            if each["type"] == "dir" and each["name"].find("public_keys") != -1:
                dir_path = self.contents_url + each["name"]
                dirs.append(self.get_repo_contents(dir_path))

        for dir in dirs:
            for file in dir:
                if file["type"] == "dir":  # ignore subfolders
                    continue

                file_path = self.repo_url + file["path"]
                username = file["name"].split(".")[0]

                key = self.http.request(
                    "GET", file_path, headers=self.headers
                ).data.decode("utf-8")

                # remove blank lines for consistency
                ssh_key = "".join(
                    [s for s in key.strip().splitlines(True) if s.strip("\r\n").strip()]
                )

                if file["path"].find("common") != -1:
                    print("Fetched Common User:", username)
                    # print(ssh_key)
                    admin_keys[username] = ssh_key
                else:
                    # print('Fetched User:', username)
                    # print(ssh_key)
                    user_keys[username] = ssh_key

        total_users = int(len(user_keys)) + int(len(admin_keys))

        # print('\nTotal:  ', total_users, 'users (', len(user_keys), 'users', '+', len(admin_keys), 'admins )')

        return {**user_keys, **admin_keys}
