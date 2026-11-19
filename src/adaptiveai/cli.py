from __future__ import annotations

import argparse
import json
from pathlib import Path

from adaptiveai import __version__
from adaptiveai.config import Settings, configure_logging, load_product_config
from adaptiveai.hardware import discover_hardware


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="adaptiveai")
    root.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    root.add_argument("--config", type=Path, help="TOML runtime configuration")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    hardware = sub.add_parser("hardware")
    hardware_sub = hardware.add_subparsers(dest="hardware_command", required=True)
    hardware_sub.add_parser("inspect")
    models = sub.add_parser("models")
    models_sub = models.add_subparsers(dest="models_command", required=True)
    models_list = models_sub.add_parser("list")
    models_list.add_argument("--verify-hashes", action="store_true")
    command = sub.add_parser("serve")
    command.add_argument("--host")
    command.add_argument("--port", type=int)
    command = sub.add_parser("chat")
    command.add_argument("prompt")
    command.add_argument(
        "--mode",
        choices=["fastest", "quality", "balanced", "hardware-aware", "auto", "economy", "manual"],
    )
    command.add_argument("--model")
    command.add_argument("--max-tokens", type=int, default=64)
    command.add_argument("--stream", action="store_true")
    command.add_argument("--scope", choices=["local", "cloud", "hybrid"], default="local")
    command.add_argument("--provider")
    command.add_argument("--max-estimated-cost", type=float)
    command.add_argument("--cost-currency", choices=["USD", "RUB"])
    command.add_argument("--allow-paid-cloud", action="store_true")
    providers = sub.add_parser("providers")
    providers_sub = providers.add_subparsers(dest="providers_command", required=True)
    providers_sub.add_parser("list")
    estimate = providers_sub.add_parser("estimate")
    estimate.add_argument("--provider", required=True)
    estimate.add_argument("--model", required=True)
    estimate.add_argument("--input-tokens", type=int, required=True)
    estimate.add_argument("--max-output-tokens", type=int, required=True)
    smoke_plan = providers_sub.add_parser("smoke-plan")
    smoke_plan.add_argument("--provider", required=True)
    smoke_plan.add_argument("--model", required=True)
    smoke_plan.add_argument("--input-tokens", type=int, default=16)
    smoke_plan.add_argument("--max-output-tokens", type=int, default=8)
    route = sub.add_parser("route")
    route_sub = route.add_subparsers(dest="route_command", required=True)
    explain = route_sub.add_parser("explain")
    explain.add_argument("prompt")
    explain.add_argument("--mode", choices=["auto", "economy", "manual"], default="auto")
    explain.add_argument("--scope", choices=["local", "cloud", "hybrid"], default="hybrid")
    explain.add_argument("--provider")
    explain.add_argument("--model")
    explain.add_argument("--local-only", action="store_true")
    explain.add_argument("--max-tokens", type=int, default=64)
    explain.add_argument("--max-estimated-cost", type=float)
    explain.add_argument("--cost-currency", choices=["USD", "RUB"])
    command = sub.add_parser("import-archive")
    command.add_argument("archive", type=Path)
    command.add_argument("--raw-dir", type=Path)
    command.add_argument("--source-uri", default="local-file")
    command = sub.add_parser("download-archive")
    command.add_argument("--raw-dir", type=Path)
    command.add_argument("--max-gib", type=float, default=3.0)
    command = sub.add_parser("normalize")
    command.add_argument("archive", type=Path)
    command.add_argument("--output-dir", type=Path)
    command.add_argument("--seed", type=int, default=3407)
    command.add_argument("--holdout-task", action="append", default=[])
    command = sub.add_parser("catalog")
    command.add_argument("--output-dir", type=Path, default=Path("data/catalog"))
    command = sub.add_parser("validate")
    command.add_argument("directory", type=Path, nargs="?", default=Path("data/processed"))
    command = sub.add_parser("eda")
    command.add_argument("directory", type=Path, nargs="?", default=Path("data/processed"))
    command.add_argument("report_dir", type=Path, nargs="?", default=Path("reports/eda"))
    command = sub.add_parser("audit-archive")
    command.add_argument("archive", type=Path)
    command.add_argument("--output", type=Path, default=Path("reports/real_data/schema_audit.json"))
    command = sub.add_parser("coverage")
    command.add_argument("directory", type=Path, nargs="?", default=Path("data/processed"))
    command.add_argument("output_dir", type=Path, nargs="?", default=Path("reports/real_data"))
    command = sub.add_parser("benchmark")
    command.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    command.add_argument("--output-dir", type=Path, default=Path("reports/phase2/runs"))
    command.add_argument(
        "--pool", choices=["lightweight20", "proprietary8"], default="lightweight20"
    )
    command.add_argument("--split", choices=["validation", "test", "ood_test"], default="test")
    command.add_argument(
        "--resolution-policy", choices=["mean", "representative", "exclude"], default="mean"
    )
    command.add_argument("--seed", type=int, default=3407)
    command.add_argument("--random-repeats", type=int, default=5)
    command.add_argument("--bootstrap-samples", type=int, default=1000)
    command = sub.add_parser("neural-suite")
    command.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    command.add_argument("--output-dir", type=Path, required=True)
    command.add_argument(
        "--pool", choices=["lightweight20", "proprietary8"], default="proprietary8"
    )
    command = sub.add_parser("neural-ablation")
    command.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    command.add_argument("--output-dir", type=Path, required=True)
    sub.add_parser("hardware-inspect")
    command = sub.add_parser("models-list")
    command.add_argument("--registry", type=Path, default=Path("data/local_model_registry.json"))
    command = sub.add_parser("local-infer")
    command.add_argument("model_id")
    command.add_argument("prompt")
    command.add_argument("--registry", type=Path, default=Path("data/local_model_registry.json"))
    command.add_argument("--max-tokens", type=int, default=64)
    command.add_argument("--timeout", type=float, default=120)
    intelligence = sub.add_parser("intelligence")
    intelligence_sub = intelligence.add_subparsers(dest="intelligence_command", required=True)
    intelligence_sub.add_parser("sources")
    intelligence_sub.add_parser("permissions")
    command = intelligence_sub.add_parser("import")
    command.add_argument("--live", action="store_true")
    command.add_argument("--snapshot", type=Path)
    command.add_argument("--store", type=Path, default=Path("data/evidence/evidence.sqlite3"))
    command.add_argument("--cache-dir", type=Path, default=Path("data/external_cache/phase6b"))
    command.add_argument("--max-results", type=int, default=20)
    command.add_argument("--dry-run", action="store_true")
    command = intelligence_sub.add_parser("evidence")
    command.add_argument("--store", type=Path, default=Path("data/evidence/evidence.sqlite3"))
    command.add_argument("--source-model-id")
    command.add_argument("--benchmark")
    command = intelligence_sub.add_parser("compare")
    command.add_argument("left_source_model_id")
    command.add_argument("right_source_model_id")
    command.add_argument("--store", type=Path, default=Path("data/evidence/evidence.sqlite3"))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = Settings()
    product_config = load_product_config(args.config)
    configure_logging(product_config.log_level)
    if args.command == "route":
        from adaptiveai.auto_routing import AutoRoutingPolicy
        from adaptiveai.public import ChatMessage, InferenceRequest, ProviderScope, RoutingMode

        router = AutoRoutingPolicy(
            product_config.auto_candidates,
            default_candidate=product_config.auto_default_candidate,
            uncertainty_policy=product_config.auto_uncertainty_policy,
        )
        request = InferenceRequest(
            messages=(ChatMessage("user", args.prompt),),
            model=args.model,
            routing_mode=RoutingMode(args.mode),
            provider_scope=ProviderScope(args.scope),
            provider=args.provider,
            local_only=args.local_only,
            max_tokens=args.max_tokens,
            max_estimated_cost=args.max_estimated_cost,
            cost_currency=args.cost_currency,
        )
        decision = router.explain(request)
        print(decision.model_dump_json(indent=2))
        return 0 if decision.status == "SELECTED" else 2
    if args.command == "providers":
        import os

        if args.providers_command == "smoke-plan":
            from adaptiveai.cloud import external_smoke_plan

            if args.input_tokens < 0 or args.max_output_tokens < 0:
                raise ValueError("token estimates must be non-negative")
            matches = [
                item for item in product_config.cloud_providers if item.provider_id == args.provider
            ]
            if len(matches) != 1:
                raise ValueError("smoke-plan requires one configured provider")
            result = external_smoke_plan(
                matches[0],
                args.model,
                input_tokens=args.input_tokens,
                max_output_tokens=args.max_output_tokens,
            )
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "READY_FOR_OWNER_AUTHORIZATION" else 2
        if args.providers_command == "estimate":
            if args.input_tokens < 0 or args.max_output_tokens < 0:
                raise ValueError("token estimates must be non-negative")
            matches = [
                item for item in product_config.cloud_providers if item.provider_id == args.provider
            ]
            if len(matches) != 1:
                raise ValueError("estimate requires one configured provider")
            config = matches[0]
            model = config.aliases.get(args.model, args.model)
            prices = [item for item in config.pricing if item.model == model]
            if not prices:
                raise ValueError("pricing is unknown for this provider deployment and model")
            price = prices[0]
            amount = (
                args.input_tokens * price.input_per_million
                + args.max_output_tokens * price.output_per_million
            ) / 1_000_000
            print(
                json.dumps(
                    {
                        "provider": config.provider_id,
                        "deployment": config.deployment_id or config.base_url,
                        "model": model,
                        "currency": price.currency,
                        "worst_case_estimate": str(amount),
                        "pricing_source": price.source,
                        "pricing_retrieved_at": price.retrieved_at,
                        "guaranteed_bill": False,
                    },
                    indent=2,
                )
            )
            return 0
        payload = [
            {
                "provider": item.provider_id,
                "deployment": item.deployment_id or item.base_url,
                "base_url": item.base_url,
                "credential_env": item.api_key_env,
                "credential_available": bool(os.getenv(item.api_key_env)),
                "configured_models": item.permitted_models,
                "pricing_models": tuple(price.model for price in item.pricing),
            }
            for item in product_config.cloud_providers
        ]
        print(json.dumps(payload, indent=2))
    elif args.command == "intelligence":
        from adaptiveai.evidence_comparison import compare_models
        from adaptiveai.evidence_store import EvidenceStore
        from adaptiveai.external_intelligence import write_private_snapshot
        from adaptiveai.hf_benchmark import (
            SOURCE_ID,
            SOURCE_URL,
            HuggingFaceLimits,
            HuggingFaceSWEVerifiedAdapter,
            swe_bench_permissions,
        )

        if args.intelligence_command == "sources":
            print(json.dumps([{"source_id": SOURCE_ID, "url": SOURCE_URL}], indent=2))
        elif args.intelligence_command == "permissions":
            print(swe_bench_permissions().model_dump_json(indent=2))
        elif args.intelligence_command == "import":
            if args.live == bool(args.snapshot):
                raise ValueError("choose exactly one of --live or --snapshot")
            adapter = HuggingFaceSWEVerifiedAdapter(
                HuggingFaceLimits(
                    max_results=args.max_results,
                    total_request_limit=1,
                    retry_limit=0,
                    offline=not args.live,
                )
            )
            raw = adapter.fetch() if args.live else args.snapshot.read_bytes()
            retrieved_at = None
            if args.snapshot:
                manifest_path = args.snapshot.with_suffix(".manifest.json")
                if manifest_path.exists():
                    from adaptiveai.hf_benchmark import SnapshotManifest

                    manifest = SnapshotManifest.model_validate_json(manifest_path.read_text())
                    retrieved_at = manifest.retrieved_at
            result = adapter.import_bytes(raw, retrieved_at=retrieved_at)
            with EvidenceStore(args.store) as store:
                update = store.ingest(result.records, dry_run=args.dry_run)
            paths = (None, None)
            if not args.dry_run:
                paths = write_private_snapshot(result, args.cache_dir)
            print(
                json.dumps(
                    {
                        "manifest": result.manifest.model_dump(mode="json"),
                        "update": update.__dict__,
                        "diagnostics": [item.model_dump() for item in result.diagnostics],
                        "snapshot": [str(path) if path else None for path in paths],
                    },
                    indent=2,
                    default=str,
                )
            )
        elif args.intelligence_command == "evidence":
            with EvidenceStore(args.store) as store:
                records = store.query(
                    source_model_id=args.source_model_id, benchmark=args.benchmark
                )
            print(json.dumps([record.model_dump(mode="json") for record in records], indent=2))
        elif args.intelligence_command == "compare":
            with EvidenceStore(args.store) as store:
                left = store.query(source_model_id=args.left_source_model_id)
                right = store.query(source_model_id=args.right_source_model_id)
            print(compare_models(left, right).model_dump_json(indent=2))
    elif args.command == "import-archive":
        from adaptiveai.io import import_archive

        path, manifest = import_archive(
            args.archive, args.raw_dir or settings.raw_dir, source_uri=args.source_uri
        )
        print(
            json.dumps(
                {"archive": str(path), "manifest": manifest.model_dump(mode="json")}, indent=2
            )
        )
    elif args.command == "download-archive":
        from adaptiveai.io import download_official_archive

        path, manifest = download_official_archive(
            args.raw_dir or settings.raw_dir,
            max_bytes=int(args.max_gib * 1024**3),
        )
        print(
            json.dumps(
                {"archive": str(path), "manifest": manifest.model_dump(mode="json")},
                indent=2,
            )
        )
    elif args.command == "normalize":
        import pandas as pd

        from adaptiveai.normalize import normalize_archive, write_empty_future_tables
        from adaptiveai.splits import create_splits

        output = args.output_dir or settings.processed_dir
        counts = normalize_archive(args.archive, output)
        queries = pd.read_parquet(output / "queries.parquet")
        create_splits(
            queries, seed=args.seed, holdout_task_types=set(args.holdout_task)
        ).to_parquet(output / "data_splits.parquet", index=False)
        write_empty_future_tables(output)
        print(json.dumps(counts, indent=2))
    elif args.command == "catalog":
        import os

        from adaptiveai.registry import fetch_catalog

        raw, table = fetch_catalog(args.output_dir, os.getenv("OPENROUTER_API_KEY"))
        print(json.dumps({"raw": str(raw), "parquet": str(table)}, indent=2))
    elif args.command == "validate":
        from adaptiveai.validation import validate_dataset

        errors = validate_dataset(args.directory)
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 1 if errors else 0
    elif args.command == "eda":
        from adaptiveai.eda import run_eda

        print(json.dumps(run_eda(args.directory, args.report_dir), indent=2))
    elif args.command == "audit-archive":
        from adaptiveai.audit import audit_archive

        print(json.dumps(audit_archive(args.archive, args.output), indent=2))
    elif args.command == "coverage":
        from adaptiveai.audit import coverage_analysis

        print(json.dumps(coverage_analysis(args.directory, args.output_dir), indent=2))
    elif args.command == "benchmark":
        from adaptiveai.benchmark import BenchmarkConfig, run_benchmark

        config = BenchmarkConfig(
            pool=args.pool,
            split=args.split,
            resolution_policy=args.resolution_policy,
            seed=args.seed,
            random_repeats=args.random_repeats,
            bootstrap_samples=args.bootstrap_samples,
        )
        print(
            json.dumps(
                {"output": str(run_benchmark(args.processed_dir, args.output_dir, config))},
                indent=2,
            )
        )
    elif args.command == "neural-suite":
        from adaptiveai.neural_experiments import run_neural_suite

        print(
            json.dumps(
                {
                    "output": str(
                        run_neural_suite(args.processed_dir, args.output_dir, pool=args.pool)
                    )
                },
                indent=2,
            )
        )
    elif args.command == "neural-ablation":
        from adaptiveai.neural_experiments import run_ablation

        print(
            json.dumps({"output": str(run_ablation(args.processed_dir, args.output_dir))}, indent=2)
        )
    elif args.command == "hardware-inspect" or (
        args.command == "hardware" and args.hardware_command == "inspect"
    ):
        print(json.dumps(discover_hardware().to_dict(), indent=2))
    elif args.command == "models-list":
        from adaptiveai.local_backend import load_registry

        models = load_registry(args.registry)
        payload = [{**model.__dict__, "path": str(model.path)} for model in models]
        print(json.dumps(payload, indent=2))
    elif args.command == "local-infer":
        from adaptiveai.local_backend import InferenceParameters, LlamaCppServer, load_registry

        models = load_registry(args.registry)
        matches = [model for model in models if model.model_id == args.model_id]
        if not matches:
            raise ValueError(f"Unknown local model: {args.model_id}")
        with LlamaCppServer(
            Path("vendor/llama.cpp/build/bin/llama-server"), matches[0], port=18777
        ) as server:
            result = server.infer(
                args.prompt,
                InferenceParameters(max_tokens=args.max_tokens),
                timeout=args.timeout,
            )
        payload = result.__dict__.copy()
        payload.pop("raw_stderr")
        print(json.dumps(payload, indent=2))
    elif args.command == "doctor":
        from adaptiveai.product_registry import ModelRegistry

        checks = []
        checks.append(
            {
                "check": "backend",
                "ok": product_config.backend_path.is_file(),
                "message": (
                    str(product_config.backend_path)
                    if product_config.backend_path.is_file()
                    else (
                        "missing; build llama.cpp or set backend_path: "
                        f"{product_config.backend_path}"
                    )
                ),
            }
        )
        try:
            registry = ModelRegistry(product_config.registry_path)
            statuses = registry.inspect()
            checks.append(
                {
                    "check": "registry",
                    "ok": True,
                    "message": f"{len(statuses)} configured model(s)",
                }
            )
            checks.extend(
                {
                    "check": f"model:{status.model.model_id}",
                    "ok": status.available,
                    "message": status.message,
                }
                for status in statuses
            )
        except (FileNotFoundError, ValueError) as error:
            checks.append({"check": "registry", "ok": False, "message": str(error)})
        hardware = discover_hardware()
        checks.append(
            {
                "check": "available_ram",
                "ok": hardware.available_ram_bytes > 512 * 1024**2,
                "message": f"{hardware.available_ram_bytes / 1024**3:.2f} GiB available",
            }
        )
        print(json.dumps({"ok": all(row["ok"] for row in checks), "checks": checks}, indent=2))
        return 0 if all(row["ok"] for row in checks) else 1
    elif args.command == "models" and args.models_command == "list":
        from adaptiveai.product_registry import ModelRegistry

        registry = ModelRegistry(product_config.registry_path)
        payload = [
            {
                "id": status.model.model_id,
                "family": status.model.family,
                "quantization": status.model.quantization,
                "available": status.available,
                "hash_valid": status.hash_valid,
                "message": status.message,
            }
            for status in registry.inspect(verify_hash=args.verify_hashes)
        ]
        print(json.dumps(payload, indent=2))
    elif args.command in {"serve", "chat"}:
        from adaptiveai.api import ProductService, serve
        from adaptiveai.auto_routing import AutoRoutingPolicy
        from adaptiveai.cloud import OpenAICompatibleProvider
        from adaptiveai.cloud_gateway import CloudGateway
        from adaptiveai.lifecycle import CloudOnlyManager, ModelManager
        from adaptiveai.product_registry import ModelRegistry
        from adaptiveai.public import ChatMessage, InferenceRequest, ProviderScope, RoutingMode
        from adaptiveai.routing_engine import RoutingEngine, load_model_profiles

        gateway = (
            CloudGateway(
                tuple(OpenAICompatibleProvider(item) for item in product_config.cloud_providers)
            )
            if product_config.cloud_providers
            else None
        )
        auto_router = AutoRoutingPolicy(
            product_config.auto_candidates,
            default_candidate=product_config.auto_default_candidate,
            uncertainty_policy=product_config.auto_uncertainty_policy,
        )
        scope = ProviderScope(args.scope) if args.command == "chat" else ProviderScope.LOCAL
        auto_selection = None
        if args.command == "chat" and args.mode in {"auto", "economy", "manual"}:
            preflight = InferenceRequest(
                messages=(ChatMessage("user", args.prompt),),
                model=args.model,
                routing_mode=RoutingMode(args.mode),
                max_tokens=args.max_tokens,
                stream=args.stream,
                local_only=scope == ProviderScope.LOCAL,
                provider_scope=scope,
                provider=args.provider,
                max_estimated_cost=args.max_estimated_cost,
                cost_currency=args.cost_currency,
            )
            auto_selection = auto_router.select(preflight)
            args.model = auto_selection.request.model
            args.provider = auto_selection.request.provider
            scope = auto_selection.request.provider_scope
        cloud_chat = scope == ProviderScope.CLOUD or (
            scope == ProviderScope.HYBRID and args.provider is not None
        )
        if args.command == "chat" and cloud_chat:
            if not args.allow_paid_cloud:
                raise ValueError("cloud chat requires explicit --allow-paid-cloud acknowledgement")
            if gateway is None:
                raise ValueError("no cloud providers are configured")
            request = InferenceRequest(
                messages=(ChatMessage("user", args.prompt),),
                model=args.model,
                routing_mode=RoutingMode(args.mode or product_config.default_routing_mode),
                max_tokens=args.max_tokens,
                stream=args.stream,
                local_only=False,
                provider_scope=scope,
                provider=args.provider,
                max_estimated_cost=args.max_estimated_cost,
                cost_currency=args.cost_currency,
            )
            try:
                if args.stream:
                    for event in gateway.stream(request):
                        if event["type"] == "content":
                            print(event["content"], end="", flush=True)
                    print()
                else:
                    response = gateway.complete(request)
                    print(response.text)
                    diagnostics = response.diagnostics.__dict__
                    if auto_selection:
                        diagnostics = {
                            **diagnostics,
                            "explanation": auto_selection.decision.model_dump(mode="json"),
                        }
                    print(json.dumps(diagnostics, indent=2))
            finally:
                gateway.close()
            return 0

        if product_config.registry_path.is_file() and product_config.backend_path.is_file():
            registry = ModelRegistry(product_config.registry_path)
            profiles_path = product_config.registry_path.with_name("local_model_profiles.json")
            profiles = load_model_profiles(
                profiles_path, tuple(model.model_id for model in registry.models())
            )
            router = RoutingEngine(
                profiles, balanced_latency_weight=product_config.balanced_latency_weight
            )
            manager = ModelManager(
                registry,
                router,
                product_config.backend_path,
                keep_alive_seconds=product_config.keep_alive_seconds,
                switch_hysteresis_seconds=product_config.switch_hysteresis_seconds,
            )
        elif product_config.cloud_providers:
            registry = None
            manager = CloudOnlyManager()
        else:
            raise ValueError(
                "local backend/registry unavailable and no cloud provider is configured"
            )
        if args.command == "serve":
            updates = {}
            if args.host:
                updates["host"] = args.host
            if args.port:
                updates["port"] = args.port
            runtime_config = product_config.__class__.model_validate(
                {**product_config.model_dump(), **updates}
            )
            service = ProductService(manager, registry, runtime_config, gateway, auto_router)
            print(
                f"AdaptiveAI experimental server: http://{runtime_config.host}:{runtime_config.port}"
            )
            serve(service, runtime_config)
        else:
            mode = RoutingMode(args.mode or product_config.default_routing_mode)
            request = InferenceRequest(
                messages=(ChatMessage("user", args.prompt),),
                model=args.model,
                routing_mode=mode,
                max_tokens=args.max_tokens,
                stream=args.stream,
                local_only=product_config.local_only,
                provider_scope=scope,
                provider=args.provider,
                max_latency_seconds=product_config.max_latency_seconds,
                available_memory_bytes=product_config.available_memory_bytes,
            )
            try:
                if args.stream:
                    for event in manager.stream(request):
                        if event["type"] == "content":
                            print(event["content"], end="", flush=True)
                    print()
                else:
                    response = manager.complete(request)
                    print(response.text)
                    diagnostics = response.diagnostics.__dict__
                    if auto_selection:
                        diagnostics = {
                            **diagnostics,
                            "explanation": auto_selection.decision.model_dump(mode="json"),
                        }
                    print(json.dumps(diagnostics, indent=2))
            finally:
                manager.shutdown()
                if gateway:
                    gateway.close()
    return 0


def entrypoint() -> int:
    try:
        return main()
    except ModuleNotFoundError as error:
        research_modules = {
            "matplotlib",
            "numpy",
            "pandas",
            "pyarrow",
            "scipy",
            "sklearn",
            "sentence_transformers",
            "torch",
        }
        if error.name in research_modules:
            raise SystemExit(
                f"Optional research dependency '{error.name}' is missing. "
                "Install AdaptiveAI with: pip install -e '.[research]'"
            ) from error
        raise


if __name__ == "__main__":
    raise SystemExit(entrypoint())
