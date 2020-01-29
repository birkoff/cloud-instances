class Owners:
    def __init__(self, github, cloud_storage):
        self.github = github
        self.cloud_storage = cloud_storage

    def list_all(self):
        return self.cloud_storage.list_all_owners()

    def sync(self):
        all_users = self.github.fetch_users()
        self.cloud_storage.store_owners_lists(list(all_users.keys()))
        self.cloud_storage.store_ssh_keys(all_users)
