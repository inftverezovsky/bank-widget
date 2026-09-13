"""Tests for operation-processing helpers."""

import unittest

from src.processing import filter_by_state, sort_by_date


class TestProcessing(unittest.TestCase):
    """Check filtering and sorting of banking operations."""

    def setUp(self) -> None:
        """Prepare the operation list from the homework examples."""
        self.operations = [
            {
                "id": 41428829,
                "state": "EXECUTED",
                "date": "2019-07-03T18:35:29.512364",
            },
            {
                "id": 939719570,
                "state": "EXECUTED",
                "date": "2018-06-30T02:08:58.425572",
            },
            {
                "id": 594226727,
                "state": "CANCELED",
                "date": "2018-09-12T21:27:25.241689",
            },
            {
                "id": 615064591,
                "state": "CANCELED",
                "date": "2018-10-14T08:21:33.419441",
            },
        ]

    def test_filter_by_state_uses_executed_by_default(self) -> None:
        """The default filter keeps only EXECUTED operations."""
        result = filter_by_state(self.operations)

        self.assertEqual([operation["id"] for operation in result], [41428829, 939719570])

    def test_filter_by_state_accepts_custom_state(self) -> None:
        """A custom state can be passed as the second argument."""
        result = filter_by_state(self.operations, "CANCELED")

        self.assertEqual([operation["id"] for operation in result], [594226727, 615064591])

    def test_filter_by_state_returns_new_list(self) -> None:
        """Filtering must not return the original list object."""
        result = filter_by_state(self.operations)

        self.assertIsNot(result, self.operations)

    def test_sort_by_date_descending_by_default(self) -> None:
        """By default operations are sorted from newest to oldest."""
        result = sort_by_date(self.operations)

        self.assertEqual(
            [operation["id"] for operation in result],
            [41428829, 615064591, 594226727, 939719570],
        )

    def test_sort_by_date_can_sort_ascending(self) -> None:
        """Passing False sorts operations from oldest to newest."""
        result = sort_by_date(self.operations, False)

        self.assertEqual(
            [operation["id"] for operation in result],
            [939719570, 594226727, 615064591, 41428829],
        )

    def test_sort_by_date_does_not_modify_source_list(self) -> None:
        """Sorting must leave the source list order unchanged."""
        original_ids = [operation["id"] for operation in self.operations]

        result = sort_by_date(self.operations)

        self.assertIsNot(result, self.operations)
        self.assertEqual([operation["id"] for operation in self.operations], original_ids)


if __name__ == "__main__":
    unittest.main()
