from django.test.testcases import TestCase

from common.date_util import parse_search_to_date, parse_date_to_search


class DateUtilTestDrive(TestCase):

    def test_search_q_to_date(self):
        # given
        search_q = '2023.06.03'

        # when
        result = parse_search_to_date(search_q)

        self.assertEqual(str(result), "2023-06-03")

    def test_date_to_search_q(self):
        # given
        date = '2023-06-03'

        # when
        result = parse_date_to_search(date)

        self.assertEqual(str(result), "2023.06.03")
