from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union

from dagster_shared.record import record
from typing_extensions import TypeAlias

from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_DAGSTER_TYPE,
    SYSTEM_METADATA_KEY_IO_MANAGER_KEY,
    AssetExecutionType,
    AssetSpec,
)
from dagster._core.definitions.output import Out
from dagster._core.types.dagster_type import Nothing

T_Spec = TypeVar("T_Spec", AssetSpec, AssetCheckSpec)

CoercibleToEffect: TypeAlias = Union[AssetSpec, AssetCheckSpec, "EntityEffect"]


class EntityEffect(ABC, Generic[T_Spec]):
    """An EntityEffect is something that happens as a result of a computation. An effect is targeted
    at a specific spec (AssetSpec or AssetCheckSpec), and is associated with a particular action
    that happens as a result of the computation. For checks, the only available action is
    executing the check. For assets, the computation can result in a materialization or an
    observation.

    EntityEffects are mapped to the underlying outputs of a compute node (OpDefinition or GraphDefinition).
    When the given output is produced, the system produces the requisite events to record the associated
    effect.
    """

    spec: T_Spec

    @property
    def key(self) -> EntityKey:
        return self.spec.key

    @staticmethod
    def from_coercible(coercible: CoercibleToEffect) -> "EntityEffect":
        """Coerces an AssetSpec or AssetCheckSpec into an Effect. The default
        execution type for an AssetSpec is AssetExecutionType.MATERIALIZATION.
        """
        if isinstance(coercible, EntityEffect):
            return coercible
        if isinstance(coercible, AssetCheckSpec):
            return AssetCheckEffect(spec=coercible)
        elif isinstance(coercible, AssetSpec):
            # default to materialization for asset specs
            return AssetMaterializationEffect(spec=coercible)
        else:
            raise ValueError(f"Invalid effect type: {type(coercible)}")

    @abstractmethod
    def to_out(self, can_subset: bool) -> Out: ...


@record
class AssetCheckEffect(EntityEffect[AssetCheckSpec]):
    spec: AssetCheckSpec

    def to_out(self, can_subset: bool) -> Out:
        return Out(
            dagster_type=Nothing,
            io_manager_key=None,
            # do not redundantly copy over description
            description=None,
            is_required=not can_subset,
            metadata=self.spec.metadata,
            code_version=None,
        )


class AssetEffect(EntityEffect[AssetSpec]):
    @property
    @abstractmethod
    def execution_type(self) -> AssetExecutionType: ...

    def to_out(self, can_subset: bool) -> Out:
        return Out(
            dagster_type=self.spec.metadata.get(SYSTEM_METADATA_KEY_DAGSTER_TYPE),
            io_manager_key=self.spec.metadata.get(SYSTEM_METADATA_KEY_IO_MANAGER_KEY),
            # do not redundantly copy over description
            description=None,
            is_required=not (can_subset or self.spec.skippable),
            metadata=self.spec.metadata,
            code_version=self.spec.code_version,
        )


@record
class AssetMaterializationEffect(AssetEffect):
    spec: AssetSpec

    @property
    def execution_type(self) -> AssetExecutionType:
        return AssetExecutionType.MATERIALIZATION


@record
class AssetObservationEffect(AssetEffect):
    spec: AssetSpec

    @property
    def execution_type(self) -> AssetExecutionType:
        return AssetExecutionType.OBSERVATION
