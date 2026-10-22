import unittest
from policy import POINT_RULES, FORBIDDEN_REWARD_ACTIONS, validate_youtube_url

class PointsPolicyTests(unittest.TestCase):
    def test_only_in_app_tasks_are_rewardable(self):
        self.assertEqual(POINT_RULES, {"profile_completed": 10, "tutorial_completed": 5})
        for action in ("youtube_subscribe", "youtube_view", "youtube_like", "youtube_comment", "youtube_share", "sub4sub"):
            self.assertIn(action, FORBIDDEN_REWARD_ACTIONS)
            self.assertNotIn(action, POINT_RULES)

    def test_youtube_url_validation(self):
        self.assertTrue(validate_youtube_url("https://www.youtube.com/@example"))
        self.assertTrue(validate_youtube_url("https://youtu.be/abc123"))
        self.assertFalse(validate_youtube_url("http://www.youtube.com/@example"))
        self.assertFalse(validate_youtube_url("https://youtube.com.evil.example/@fake"))

if __name__ == "__main__":
    unittest.main()
