from __future__ import annotations

from xampler.experimental.dynamic_workers import (
    DynamicModule,
    DynamicWorkerCode,
    DynamicWorkerLimits,
    python_fetch_worker,
    stable_worker_id,
)


def test_dynamic_worker_code_shape() -> None:
    code = DynamicWorkerCode(
        compatibility_date="2026-05-01",
        main_module="worker.py",
        modules={"worker.py": DynamicModule("py", "print('hi')")},
        env={"MESSAGE": "hello"},
        global_outbound=None,
        limits=DynamicWorkerLimits(cpu_ms=10, subrequests=0),
    )

    assert code.to_raw() == {
        "compatibilityDate": "2026-05-01",
        "mainModule": "worker.py",
        "modules": {"worker.py": {"py": "print('hi')"}},
        "env": {"MESSAGE": "hello"},
        "globalOutbound": None,
        "limits": {"cpuMs": 10, "subRequests": 0},
    }


def test_python_fetch_worker_and_stable_id() -> None:
    code = python_fetch_worker("print('hello')", compatibility_date="2026-05-01")

    assert code.main_module == "worker.py"
    assert code.to_raw()["modules"] == {"worker.py": "print('hello')"}
    assert code.to_raw()["compatibilityFlags"] == [
        "python_workers",
        "disable_python_external_sdk",
    ]


def test_stable_worker_id_follows_code_content() -> None:
    def worker(source: str) -> DynamicWorkerCode:
        return python_fetch_worker(source, compatibility_date="2026-05-01")

    worker_id = stable_worker_id("demo", worker("print('hello')"))

    assert worker_id.startswith("demo:")
    assert stable_worker_id("demo", worker("print('hello')")) == worker_id
    assert stable_worker_id("demo", worker("print('bye')")) != worker_id
    assert stable_worker_id("other", worker("print('hello')")).startswith("other:")
    assert stable_worker_id("demo", "a") != stable_worker_id("demo", "b")
