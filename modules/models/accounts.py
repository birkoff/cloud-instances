
class Accounts:

    def __init__(self, settings):
        self.settings = settings

    def get(self, account_name):
        return self.provider.get_machine(account_name)

    def list(self, filters=None):
        if filters is None:
            filters = []
        machines = self.provider.list_machines(filters)
        return machines


if __name__ == '__main__':
    pass
