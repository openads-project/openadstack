import tempfile
import textwrap
import unittest
from pathlib import Path

import generate


class GenerateComposeTests(unittest.TestCase):
    def test_image_tag_for_branch(self):
        self.assertEqual(generate.image_tag_from_ref_for_test("feature/demo", "branch", "1.2.3"), "latest_feature-demo_ci")

    def test_image_tag_for_tag(self):
        self.assertEqual(generate.image_tag_from_ref_for_test("v1.2.3", "tag", "1.2.3"), "v1.2.3")

    def test_image_tag_for_commit(self):
        self.assertEqual(generate.image_tag_from_ref_for_test("abc1234", "commit", "1.2.3"), "v1.2.3")

    def test_launch_argument_extraction(self):
        source = textwrap.dedent(
            """
            from launch.actions import DeclareLaunchArgument

            remappable_topics = [
                DeclareLaunchArgument("input_topic", default_value="~/input"),
            ]

            def generate_launch_description():
                return [
                    DeclareLaunchArgument("use_sim_time", default_value="false"),
                    *remappable_topics,
                ]
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "module.launch.py"
            path.write_text(source)
            self.assertEqual(
                generate.launch_arguments(path),
                {"input_topic": "~/input", "use_sim_time": "false"},
            )

    def test_override_preservation_from_comment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose = Path(temp_dir) / "docker-compose.yml"
            compose.write_text(
                textwrap.dedent(
                    """
                    services:
                      demo:
                        environment:
                          EGO_DATA_TOPIC: /stack/ego_data # ~/ego_data
                          STALE_TOPIC: ~/stale
                    """
                )
            )
            launch_args = {"ego_data_topic": "~/ego_data"}
            env, stale = generate.generated_environment(
                launch_args,
                {"repository_url": "https://github.com/openads-project/demo", "namespace": "/planning"},
                generate.parse_existing_environment(compose),
            )
            self.assertEqual(env["ego_data_topic"]["value"], "/stack/ego_data")
            self.assertEqual(env["ego_data_topic"]["comment"], "~/ego_data")
            self.assertEqual(stale, ["STALE_TOPIC"])


if __name__ == "__main__":
    unittest.main()
