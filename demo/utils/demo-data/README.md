# OpenADStack demo bag images

Each OpenADStack demo requires a recorded ROS 2 bag as its input. All bag
variants cover the same time range and therefore have the same playback
duration. They differ only in the topics they contain. This keeps the basic
demo small, while the extended demo includes the additional sensor data
required by its perception pipeline. An optional full bag contains the remaining
recorded sensor topics for further experiments.

## Bag overview

| Topic | Bag for Basic Demo (2.3 GB) | Bag for Extended Demo (15.1 GB) | Full Bag for Extended Demo (30.3 GB) |
| --- | --- | --- | --- |
| `/tf` | x | x | x |
| `/localization/ego_state_estimation/ego_data` | x | x | x |
| `/localization/ego_state_estimation/nav_sat_fix` | x | x | x |
| `/perception/point_cloud_object_detection_ouster/object_list` | x | | |
| `/drivers/ouster_lidar_fl/points/cloudini` | | x | x |
| `/drivers/ouster_lidar_fr/points/cloudini` | | | x |
| `/drivers/ouster_lidar_rl/points/cloudini` | | | x |
| `/drivers/ouster_lidar_rr/points/cloudini` | | x | x |
| `/drivers/zed_camera/front_center/left/color/rect/image/compressed` | x | x | x |
| `/drivers/zed_camera/front_center/left/color/rect/camera_info` | x | x | x |
| `/drivers/zed_camera/front_left/left/color/rect/image/compressed` | | | x |
| `/drivers/zed_camera/front_left/left/color/rect/camera_info` | | | x |
| `/drivers/zed_camera/front_right/right/color/rect/image/compressed` | | | x |
| `/drivers/zed_camera/front_right/right/color/rect/camera_info` | | | x |

## Create the bag variants

Place the original bag in an `openadstack_demo` directory next to
`convert.yml`:

```text
demo-data/
├── convert.yml
└── openadstack_demo/
    ├── metadata.yaml
    └── rosbag2.mcap
```

Run the conversion from the `demo-data` directory:

```bash
docker-run --mwd rwthika/ros2:jazzy \
  ros2 bag convert \
  --input openadstack_demo \
  --output-options convert.yml
```

The configuration extracts the common time range and applies the topic filters
shown above. It creates three new ROS 2 bag directories:

- `openadstack_demo_basic`
- `openadstack_demo_extended`
- `openadstack_demo_full`

These output directories must not exist before running the command. Each
generated directory can then be used as the Docker build context described
below.

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
| Basic demo | `ghcr.io/openads-project/openadstack/demo-data:basic_v1.0.0` |
| Extended demo | `ghcr.io/openads-project/openadstack/demo-data:extended_v1.0.0` |
| Full bag | `ghcr.io/openads-project/openadstack/demo-data:full_v1.0.0` |

```bash
docker build \
  --file Dockerfile \
  --tag ghcr.io/openads-project/openadstack/demo-data:basic_v1.0.0 \
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

> [!NOTE]
> These are data-only images and do not contain ROS 2. A service that executes
> `ros2 bag play` must provide the ROS runtime separately and consume the files
> from `/data`.
