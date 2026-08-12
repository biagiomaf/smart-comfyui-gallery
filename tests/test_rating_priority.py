import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMARTGALLERY_PATH = PROJECT_ROOT / "smartgallery.py"
FUNCTION_NAMES = {
    "prioritize_personal_unrated",
    "resolve_rating_client_uuid",
}


def load_rating_priority_functions():
    """Load pure helpers without importing the application's runtime dependencies."""
    tree = ast.parse(SMARTGALLERY_PATH.read_text(encoding="utf-8"))
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_NAMES
    ]
    namespace = {}
    exec(
        compile(
            ast.Module(body=functions, type_ignores=[]),
            str(SMARTGALLERY_PATH),
            "exec",
        ),
        namespace,
    )
    return namespace


HELPERS = load_rating_priority_functions()
prioritize_personal_unrated = HELPERS["prioritize_personal_unrated"]
resolve_rating_client_uuid = HELPERS["resolve_rating_client_uuid"]


class RatingPriorityTests(unittest.TestCase):
    def test_unrated_files_come_first_without_changing_group_order(self):
        files = [
            {"id": "rated-a", "my_rating": 4},
            {"id": "unrated-a", "my_rating": None},
            {"id": "rated-b", "my_rating": 2},
            {"id": "unrated-b", "my_rating": 0},
        ]

        result = prioritize_personal_unrated(files)

        self.assertEqual(
            [item["id"] for item in result],
            ["unrated-a", "unrated-b", "rated-a", "rated-b"],
        )

    def test_cleared_rating_returns_to_unrated_group(self):
        files = [
            {"id": "still-rated", "my_rating": 5},
            {"id": "cleared", "my_rating": 0},
        ]

        result = prioritize_personal_unrated(files)

        self.assertEqual([item["id"] for item in result], ["cleared", "still-rated"])

    def test_original_sort_index_supports_consistent_client_reordering(self):
        files = [
            {"id": "rated-a", "my_rating": 4},
            {"id": "unrated-a", "my_rating": None},
            {"id": "rated-b", "my_rating": 2},
            {"id": "unrated-b", "my_rating": None},
        ]

        result = prioritize_personal_unrated(files)

        self.assertEqual(
            {item["id"]: item["review_sort_index"] for item in result},
            {"rated-a": 0, "unrated-a": 1, "rated-b": 2, "unrated-b": 3},
        )

    def test_local_admin_uses_same_identity_as_browser_rating_requests(self):
        self.assertEqual(resolve_rating_client_uuid(None, False, False), "admin")
        self.assertEqual(resolve_rating_client_uuid("42", True, False), "42")
        self.assertEqual(resolve_rating_client_uuid(None, True, False), "")


if __name__ == "__main__":
    unittest.main()
