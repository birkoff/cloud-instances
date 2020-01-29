import unittest.mock
from unittest import mock
from modules.providers.aws.presenters import AWSPresenter as Presenter
from datetime import datetime


class TestPresentersAws(unittest.TestCase):
    def test_get_instance_ready_status(self):
        presenter = Presenter()
        response = presenter.get_instance_ready_status(
            "10/12/2019 17:24:00", datetime(2019, 12, 10, 17, 28)
        )
        print(response)
        self.assertEqual(response, "Bootstrapping Instance")

        presenter = Presenter()
        response2 = presenter.get_instance_ready_status(
            "10/12/2019 17:58:00", datetime(2019, 12, 10, 18, 5)
        )
        print(response2)
        self.assertEqual(response2, "Bootstrapping Instance")

        presenter = Presenter()
        response3 = presenter.get_instance_ready_status(
            "10/12/2019 18:05:00", datetime(2019, 12, 10, 18, 13)
        )
        print(response3)
        self.assertEqual(response3, "Ready")

        presenter = Presenter()
        response4 = presenter.get_instance_ready_status(
            "10/12/2019 17:58:00", datetime(2019, 12, 10, 18, 6)
        )
        print(response4)
        self.assertEqual(response3, "Ready")


if __name__ == "__main__":
    unittest.main()
