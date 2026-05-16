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

    def test_service_name_inference(self):
        self.assertEqual(generate.service_namespace("planning.trajectory-optimization"), "/planning")
        self.assertEqual(generate.service_node_name("planning.trajectory-optimization"), "trajectory_optimization")
        self.assertEqual(
            generate.service_output_path(Path("/repo"), "planning.trajectory-optimization"),
            Path("/repo/planning/trajectory_optimization/docker-compose.yml"),
        )

    def test_normalize_central_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "compose-generation"
            config_dir.mkdir()
            path = config_dir / "config.yml"
            path.write_text(
                textwrap.dedent(
                    """
                    services:
                    - planning.trajectory-optimization:
                        repository:
                          url: https://github.com/openads-project/trajectory_optimization
                          ref: v1.2.0
                        compose:
                          extends: ros2-service
                    """
                )
            )
            configs = generate.normalize_services(path)
            self.assertEqual(len(configs), 1)
            self.assertEqual(configs[0]["service_name"], "planning.trajectory-optimization")
            self.assertEqual(configs[0]["namespace"], "/planning")
            self.assertEqual(configs[0]["name"], "trajectory_optimization")
            self.assertEqual(configs[0]["extends"]["file"], "../../docker-compose-essentials/docker-compose.template.yml")

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
                          # --- inputs ----
                          EGO_DATA_TOPIC: /stack/ego_data # ~/ego_data
                          STALE_TOPIC: ~/stale
                    """
                )
            )
            launch_args = {"ego_data_topic": "~/ego_data"}
            env, stale = generate.generated_environment(
                launch_args,
                {"repository_url": "https://github.com/openads-project/demo", "namespace": "/planning", "name": "demo"},
                generate.parse_existing_environment(compose),
            )
            self.assertEqual(env["ego_data_topic"]["value"], "/stack/ego_data")
            self.assertEqual(env["ego_data_topic"]["comment"], "~/ego_data")
            self.assertEqual(stale, ["STALE_TOPIC"])


if __name__ == "__main__":
    unittest.main()
