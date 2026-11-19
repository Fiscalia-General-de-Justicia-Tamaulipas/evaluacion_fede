import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import main


class SaveAnswerSecurityTests(unittest.TestCase):
    def setUp(self):
        self.evaluation = SimpleNamespace(
            id=24,
            user_id=7,
            module_id=1,
            completed_at=None,
            video_completed=True,
        )
        self.question = SimpleNamespace(id=11, module_id=1)
        self.option = SimpleNamespace(id=5, question_id=11, is_correct=True)
        self.database = Mock()
        self.database.get.side_effect = lambda model, _: {
            main.Evaluation: self.evaluation,
            main.Question: self.question,
            main.Option: self.option,
        }[model]
        self.user = SimpleNamespace(id=7)
        self.data = main.SaveAnswerIn(question_id=11, option_id=5)

    def save_answer(self, existing_answer=None):
        self.database.scalar.return_value = existing_answer
        with (
            patch.object(main, "_require_available_module"),
            patch.object(main, "get_evaluation_question_order", return_value=[11]),
            patch.object(main, "get_next_unanswered_index", return_value=0),
        ):
            return main.save_answer(24, self.data, self.database, self.user)

    def test_new_answer_does_not_disclose_correctness(self):
        response = self.save_answer()

        self.assertNotIn("is_correct", response)

    def test_updated_answer_does_not_disclose_correctness(self):
        existing_answer = SimpleNamespace(option_id=4, is_correct=False)

        response = self.save_answer(existing_answer)

        self.assertNotIn("is_correct", response)


class JwtSecretStartupTests(unittest.TestCase):
    def test_startup_rejects_missing_or_short_secret(self):
        with (
            patch.object(main, "SECRET_KEY", ""),
            patch.object(main, "initialize_database") as initialize_database,
            self.assertRaisesRegex(RuntimeError, "SECRET_KEY"),
        ):
            main.startup_event()

        initialize_database.assert_not_called()

    def test_startup_accepts_long_secret(self):
        with (
            patch.object(main, "SECRET_KEY", "s" * 48),
            patch.object(main, "initialize_database") as initialize_database,
        ):
            main.startup_event()

        initialize_database.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
