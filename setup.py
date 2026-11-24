"""Include the repository's default configuration in installed wheels."""

from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

_CONFIG_SOURCE = Path(__file__).resolve().parent / "configs" / "default.yaml"


class BuildPy(build_py):
    @property
    def _config_target(self) -> Path:
        return Path(self.build_lib) / "canopy" / "default.yaml"

    def run(self) -> None:
        super().run()
        if not self.editable_mode:
            self.copy_file(str(_CONFIG_SOURCE), str(self._config_target))

    def get_outputs(self, include_bytecode: bool = True) -> list[str]:
        outputs = super().get_outputs(include_bytecode)
        if not self.editable_mode:
            outputs.append(str(self._config_target))
        return outputs

    def get_output_mapping(self) -> dict[str, str]:
        return super().get_output_mapping() | {str(self._config_target): str(_CONFIG_SOURCE)}


setup(cmdclass={"build_py": BuildPy})
