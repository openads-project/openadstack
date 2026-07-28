#!/usr/bin/env python3

# Copyright Institute for Automotive Engineering (ika), RWTH Aachen University
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from rosgraph_msgs.msg import Clock
from std_srvs.srv import Empty

RESET_SERVICE = os.environ.get("RVIZ_RESET_SERVICE", "/rviz/reset_time")
MIN_BACKWARD_JUMP_SEC = 1.0
RESET_COOLDOWN_SEC = 2.0
RESET_TIMEOUT_SEC = 1.0


class RvizClockResetWatchdog(Node):
    """Reset RViz when simulated time jumps backwards."""

    def __init__(self, rviz_command):
        """Start RViz and subscribe to the clock topic."""
        super().__init__("rviz_clock_reset_watchdog")
        self._last_clock_ns = None
        self._last_reset_monotonic = 0.0
        self._reset_future = None
        self._rviz_process = subprocess.Popen(rviz_command)
        self._reset_client = self.create_client(Empty, RESET_SERVICE)

        qos = QoSProfile(
            depth=10,
            durability=QoSDurabilityPolicy.VOLATILE,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
        )
        self.create_subscription(Clock, "/clock", self._on_clock, qos)

    def _on_clock(self, msg):
        current_ns = msg.clock.sec * 1_000_000_000 + msg.clock.nanosec
        jump_ns = int(MIN_BACKWARD_JUMP_SEC * 1e9)

        if self._last_clock_ns is not None and self._last_clock_ns - current_ns >= jump_ns:
            self._reset_rviz()

        self._last_clock_ns = current_ns

    def _reset_rviz(self):
        now = time.monotonic()
        if now - self._last_reset_monotonic < RESET_COOLDOWN_SEC:
            return

        self._last_reset_monotonic = now
        self.get_logger().info(f"Calling {RESET_SERVICE}")

        if not self._reset_client.wait_for_service(timeout_sec=RESET_TIMEOUT_SEC):
            self.get_logger().warn(f"{RESET_SERVICE} is not available; skipping RViz reset")
            return

        if self._reset_future is not None and not self._reset_future.done():
            self.get_logger().warn("Previous RViz reset_time call is still pending")
            return

        self._reset_future = self._reset_client.call_async(Empty.Request())
        self._reset_future.add_done_callback(self._on_reset_complete)

    def _on_reset_complete(self, future):
        """Log the asynchronous reset result without recursively spinning the executor."""
        self._reset_future = None
        if future.cancelled():
            self.get_logger().warn("RViz reset_time call was cancelled")
            return

        try:
            future.result()
        except Exception as exception:  # noqa: BLE001 - rclpy futures may expose service exceptions
            self.get_logger().warn(f"RViz reset_time call failed: {exception}")

    def destroy_node(self):
        """Stop the RViz subprocess before destroying the watchdog node."""
        if self._rviz_process.poll() is None:
            self._rviz_process.terminate()
            self._rviz_process.wait(timeout=5.0)
        super().destroy_node()


def main():
    """Run RViz with automatic reset handling for backward clock jumps."""
    rviz_command = sys.argv[1:]
    if rviz_command and rviz_command[0] == "--":
        rviz_command = rviz_command[1:]
    if not rviz_command:
        raise SystemExit("Usage: reset_rviz_on_clock_jump.py -- rviz2 [args...]")

    rclpy.init(args=[])
    node = RvizClockResetWatchdog(rviz_command)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
