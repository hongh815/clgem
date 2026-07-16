import unittest

from cogem.task_policy import is_under


class TaskPolicyTests(unittest.TestCase):
    def test_path_traversal_is_not_classified_under_skill_root(self):
        self.assertFalse(is_under("skills/../docs/readme.md", "skills"))

    def test_similar_prefix_is_not_classified_under_skill_root(self):
        self.assertFalse(is_under("skills-old/demo/SKILL.md", "skills"))

    def test_windows_separator_is_normalized(self):
        self.assertTrue(is_under(r"skills\demo\SKILL.md", "skills"))


if __name__ == "__main__":
    unittest.main()
