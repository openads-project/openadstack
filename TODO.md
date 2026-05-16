# TODO: Publish Upstream Compose Contracts

## Render the downstream composition before OCI artifacts exist

Run this from the repository root. The two environment variables temporarily replace the future OCI artifact references with the local playground files under `upstream_repos/`.

```bash
LANELET2_ROUTE_PLANNING_COMPOSE="$PWD/upstream_repos/planning/lanelet2_route_planning/docker-compose.yml" \
TRAJECTORY_OPTIMIZATION_COMPOSE="$PWD/upstream_repos/planning/trajectory_optimization/docker-compose.yml" \
docker compose -f downstream_composition/docker-compose.yml config
```

For module-only renders, use the same variable for the module being rendered:

```bash
LANELET2_ROUTE_PLANNING_COMPOSE="$PWD/upstream_repos/planning/lanelet2_route_planning/docker-compose.yml" \
docker compose -f downstream_composition/planning/lanelet2_route_planning/docker-compose.yml config

TRAJECTORY_OPTIMIZATION_COMPOSE="$PWD/upstream_repos/planning/trajectory_optimization/docker-compose.yml" \
docker compose -f downstream_composition/planning/trajectory_optimization/docker-compose.yml config
```

## Publish the upstream Compose artifacts

Each upstream module repository should publish its module-owned compose contract as an OCI artifact with the same version as the module image. The publish target does not use the `oci://` prefix; consumers use `oci://` when referencing it.

From the `lanelet2_route_planning` upstream repository root:

```bash
docker login ghcr.io
docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml publish ghcr.io/openads-project/lanelet2_route_planning-compose:v1.0.2
```

From the `trajectory_optimization` upstream repository root:

```bash
docker login ghcr.io
docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml publish ghcr.io/openads-project/trajectory_optimization-compose:v1.2.0
```

Optional hardening before publishing:

```bash
docker compose -f docker-compose.yml publish --resolve-image-digests ghcr.io/openads-project/<module>-compose:<version>
```

Use `--with-env` only if the upstream repository intentionally wants resolved environment values embedded in the published artifact. Do not publish downstream files with bind mounts as upstream artifacts; Docker documents bind mounts and local includes as publish limitations.

## After publishing

Once both OCI artifacts exist, the local override variables are no longer needed:

```bash
docker compose -f downstream_composition/docker-compose.yml config
```

The AD-stack files already default to these remote references:

```text
oci://ghcr.io/openads-project/lanelet2_route_planning-compose:v1.0.2
oci://ghcr.io/openads-project/trajectory_optimization-compose:v1.2.0
```

Reference docs:

- https://docs.docker.com/compose/how-tos/oci-artifact/
- https://docs.docker.com/reference/cli/docker/compose/publish/
- https://docs.docker.com/reference/cli/docker/compose/
