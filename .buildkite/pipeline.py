#!/usr/bin/env python3
"""Buildkite dynamic pipeline generator for qdb-cloudwatch-exporter.

Step templates in steps/*.yml define nearly-complete Buildkite steps with
{placeholder} variables.  This script loads them, substitutes variables, and
overlays environment variables and the Docker plugin per platform.

Usage:
    python3 pipeline.py           # emit pipeline YAML to stdout
    python3 pipeline.py check     # validate without emitting
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

from buildkite_sdk import CommandStep, Pipeline, GroupStep

sys.path.insert(0, str(Path(__file__).parent / "tools"))
from qdb_pipeline import (
    Platform,
    apply_docker_compose,
    load_template,
    merge_env,
    select_platforms,
    validate_pipeline,
    get_git_ref,
    set_artifact_plugin_options,
)  # noqa: E402

STEPS_DIR = Path(__file__).parent / "steps"

# Quasardb-specific toolchain overlays on top of shared infrastructure platforms.
_LINUX = dict()

_OS_OVERLAY = {"linux": _LINUX}
PLATFORMS: list[Platform] = [
    dataclasses.replace(p, **_OS_OVERLAY.get(p.os, {}))
    for p in select_platforms(
        "linux-amd64-core2",
    )
]

BUILD_TYPES = ["Release"]

# We only test latest Python and the minimum supported version
PYTHON_VERSIONS = [
    "3.9",
    "3.14",
]

# Environment variable layering: global → step → os → os+step → platform compilers.
GLOBAL_ENV: dict[str, str] = {
    "JUNIT_XML_FILE": "tests/pytest.xml",
    "QDB_ENCRYPT_TRAFFIC": "1",
}

STEP_ENV: dict[str, dict[str, str]] = {}

OS_ENV: dict[str, dict[str, str]] = {}

OS_STEP_ENV: dict[str, dict[str, str]] = {}

CPU_ENV: dict[str, dict[str, str]] = {}


def _env(p: Platform, step_name: str, build_type: str) -> dict[str, str]:
    """Compose the full environment dict for one step."""
    return merge_env(
        GLOBAL_ENV,
        STEP_ENV.get(step_name, {}),
        OS_ENV.get(p.os, {}),
        OS_STEP_ENV.get(f"{p.os}/{step_name}", {}),
        CPU_ENV.get(p.cpu, {}),
        {"CMAKE_BUILD_TYPE": build_type},
        platform=p,
    )


def generate_pipeline() -> Pipeline:
    """Load templates, expand across platforms × build_types, overlay env and docker."""
    pipeline = Pipeline()
    git_ref = get_git_ref()
    group_steps = {}
    jobs = []

    for p in PLATFORMS:
        for bt in BUILD_TYPES:
            for py in PYTHON_VERSIONS:
                slug = p.slug(bt.lower(), f"py{py.replace('.', '')}")
                jobs.append(f"build-{slug}")

                # We want to use Release QuasarDB binaries when building Python API (debug and release)
                py_dependency_slug = p.slug("release", f"py{py.replace('.', '')}")
                qdb_dependency_slug = p.slug("release")

                tvars = {
                    "slug": slug,
                    "queue": f"{p.queue_os}-{p.arch}",
                    "name": slug.replace("-", " ").title(),
                }

                artifact_vars_per_step = {
                    "upload": {"variant": slug, "git-ref": git_ref},
                    "promote": {"variant": slug, "git-ref": git_ref},
                    "download": {
                        "by_project": {
                            "qdb-api-python": {
                                "variant": py_dependency_slug,
                                "git-ref": git_ref,
                            },
                            "quasardb-build": {
                                "variant": qdb_dependency_slug,
                                "git-ref": git_ref,
                            },
                        }
                    },
                }

                compose_config = {
                    "run": "python-build",
                    "config": "docker/docker-compose.yml",
                    "propagate-uid-gid": True,
                }

                step = load_template(STEPS_DIR / "_build.yml", **tvars)
                env = _env(p, "build", bt)
                env.update(step.get("env") or {})
                env.update({"PYTHON_VERSION": py})
                step["env"] = env
                if p.os == "linux":
                    apply_docker_compose(step, config=compose_config)
                set_artifact_plugin_options(step, artifact_vars_per_step)

                # add step to group
                group_name = p.slug(bt.lower()).replace("-", " ").title()
                if group_name not in group_steps:
                    group_steps[group_name] = []
                group_steps[group_name].append(step)

    # create groups and add to pipeline
    for group, steps in group_steps.items():
        group_step = GroupStep(group=group, steps=steps)
        pipeline.add_step(group_step)
    
    step = load_template(STEPS_DIR / "_test_report.yml")
    step["depends_on"] = jobs
    pipeline.add_step(CommandStep.from_dict(step))

    return pipeline


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "generate"

    try:
        pipeline = generate_pipeline()
    except Exception as e:
        print(f"[FAIL] Pipeline generation failed: {e}", file=sys.stderr)
        sys.exit(1)

    if command == "generate":
        print(pipeline.to_yaml())
    elif command == "check":
        errors = validate_pipeline(pipeline)
        if errors:
            for e in errors:
                print(f"[FAIL] {e}", file=sys.stderr)
            sys.exit(1)
        print(f"[OK] Pipeline valid: {len(pipeline.steps)} steps")
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Usage: pipeline.py [generate|check]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
