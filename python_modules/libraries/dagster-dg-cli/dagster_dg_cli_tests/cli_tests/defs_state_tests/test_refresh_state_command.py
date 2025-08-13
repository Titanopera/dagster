import shutil
from pathlib import Path

import dagster as dg
import yaml
from dagster_dg_core.utils import activate_venv
from dagster_dg_core_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)


def test_refresh_state_command():
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner, in_workspace=False, use_editable_dagster=True, uv_sync=True
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
        dg.instance_for_test() as instance,
    ):
        # no components, nothing to refresh
        result = runner.invoke("utils", "refresh-component-state")
        assert_runner_result(result)
        latest_state_info = instance.defs_state_storage.get_latest_defs_state_info()
        assert latest_state_info is None

        # write a local component defs.yaml
        component_dir = project_dir / "src/foo_bar/defs/the_component"
        component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component_dir / "local.py",
        )
        with (component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {"type": ".local.SampleStateBackedComponent"},
                f,
            )

        # now we have a state-backed component, command should succeed
        # and we should have a new state version
        result = runner.invoke("utils", "refresh-component-state")
        assert_runner_result(result)

        latest_state_info = instance.defs_state_storage.get_latest_defs_state_info()
        assert latest_state_info is not None
        assert latest_state_info.info_mapping.keys() == {"the_component"}

        # write another local component defs.yaml, this one will fail to write state
        component_dir = project_dir / "src/foo_bar/defs/the_component_fails"
        component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(
            Path(__file__).parent / "sample_state_backed_component.py",
            component_dir / "local.py",
        )
        with (component_dir / "defs.yaml").open("w") as f:
            yaml.dump(
                {
                    "type": ".local.SampleStateBackedComponent",
                    "attributes": {"fail_write": True},
                },
                f,
            )

        # command should fail, but state should be updated for the non-failing component
        result = runner.invoke("utils", "refresh-component-state")
        assert result.exit_code == 1

        new_latest_state_info = instance.defs_state_storage.get_latest_defs_state_info()
        assert new_latest_state_info is not None
        assert new_latest_state_info.info_mapping.keys() == {"the_component"}
        assert (
            new_latest_state_info.info_mapping["the_component"].version
            != latest_state_info.info_mapping["the_component"].version
        )
