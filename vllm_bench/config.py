from dataclasses import dataclass, field
from pathlib import Path
import itertools, yaml

@dataclass(frozen=True)
class dockerCfg:
    host: str
    user: str
    docker_path: str
    docker_name: str
    exe_path: str
    gpu: str
    tensor_parallel: int

@dataclass(frozen=True)
class Modelcfg:
    name: str
    dtype: str
    block_size: list[int]
    nccl_p2p_disable: list[int]
    max_num_seqs: list[int]
    max_num_batched_tokens: list[int]
    gpu_memory_util: list[float]
    max_model_len: list[int]

@dataclass(frozen=True)
class BenchCfg:
    dataset_name: str
    dataset_path: str
    request_rate: list[int]
    num_prompts: int
    num_runs: int

@dataclass(frozen=True)
class GlobalCfg:
    docker: dockerCfg
    model: Modelcfg
    benchmark: BenchCfg
    output_dir: Path = Path("./result")

    @staticmethod
    def read_yaml(path: str | Path) -> "GlobalCfg":
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return GlobalCfg(
            docker=dockerCfg(**raw["docker"]),
            model=Modelcfg(**raw["model"]),
            benchmark=BenchCfg(**raw["benchmark"]),
            output_dir=Path(raw["output_dir"])
        )

    def param_grid(self):
        m = self.model
        b = self.benchmark
        for (
            block_size,
            nccl,
            max_seqs,
            max_tokens,
            util,
            max_len,
            req_rate,
            run_id
        ) in itertools.product(
            m.block_size,
            m.nccl_p2p_disable,
            m.max_num_seqs,
            m.max_num_batched_tokens,
            m.gpu_memory_util,
            m.max_model_len,
            b.request_rate,
            range(1, b.num_runs + 1)
        ):
            yield{
                "block_size": block_size,
                "nccl": nccl,
                "max_seqs": max_seqs,
                "max_tokens": max_tokens,
                "util": util,
                "max_len": max_len,
                "req_rate": req_rate,
                "run_id": run_id
            }