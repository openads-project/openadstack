# OpenADStack demo bag images

Each OpenADStack demo requires a recorded ROS 2 bag as its input. All bag
variants cover the same time range and therefore have the same playback
duration. They differ only in the topics they contain. This keeps the regular
demo small, while the full demo and experiment setup include the additional
sensor data required by their processing pipelines.

## Bag overview

| Topic | Bag for Basic Demo (XGB) | Bag for Full Demo (XGB) | Bag for further Experiments (XGB) |
| --- | --- | --- | --- |
| `/tf` | x | x | x |
| `/localization/ego_state_estimation/ego_data` | x | x | x |
| `/localization/ego_state_estimation/nav_sat_fix` | x | x | x |
| `/perception/point_cloud_object_detection_ouster/object_list` | x | x | x |
| `/drivers/ouster_lidar_fl/points/cloudini` | | x | x |
| `/drivers/ouster_lidar_fr/points/cloudini` | | | x |
| `/drivers/ouster_lidar_rl/points/cloudini` | | | x |
| `/drivers/ouster_lidar_rr/points/cloudini` | | x | x |
| `/drivers/zed_camera/front_center/left/color/rect/image/compressed` | x | x | x |
| `/drivers/zed_camera/front_center/left/color/rect/camera_info` | x | x | x |
| `/drivers/zed_camera/front_left/left/color/rect/image/compressed` | | | x |
| `/drivers/zed_camera/front_left/left/color/rect/camera_info` | | | x |
| `/drivers/zed_camera/front_right/left/color/rect/image/compressed` | | | x |
| `/drivers/zed_camera/front_right/left/color/rect/camera_info` | | | x |
| `/drivers/zed_camera/rear_center/left/color/rect/image/compressed` | | | x |
| `/drivers/zed_camera/rear_center/left/color/rect/camera_info` | | | x |

## Build a bag image

Each bag is packaged as a separate, Alpine-based data image. The Rosbag
directory itself must be used as the Docker build context and must contain
`metadata.yaml` at its root:

```text
<rosbag-directory>/
├── metadata.yaml
└── <storage-file>.db3  # or .mcap
```

Run the build command from this directory and select the image name matching
the bag:

| Bag variant | Image |
| --- | --- |
| Demo | `ghcr.io/openads-project/openadstack/data-demo:v1.0.0` |
| Full demo | `ghcr.io/openads-project/openadstack/data-demo-full:v1.0.0` |
| Experiments | `ghcr.io/openads-project/openadstack/data-demo-extended:v1.0.0` |

```bash
docker build \
  --file Dockerfile \
  --tag ghcr.io/openads-project/openadstack/data-demo:v1.0.0 \
  /absolute/path/to/rosbag-directory
```

For the other variants, replace both the image name and the Rosbag directory
with the corresponding values from the table.

During the build, the contents of the Rosbag directory are copied directly into
`/data`. The build fails if `metadata.yaml` is missing. The resulting image has
this structure:

```text
/data/
├── metadata.yaml
└── <storage-file>.db3  # or .mcap
```

Verify the packaged bag with:

```bash
docker run --rm \
  --entrypoint ls \
  ghcr.io/openads-project/openadstack/data-demo:v1.0.0 \
  -lah /data
```

> [!NOTE]
> These are data-only images and do not contain ROS 2. A service that executes
> `ros2 bag play` must provide the ROS runtime separately and consume the files
> from `/data`.
