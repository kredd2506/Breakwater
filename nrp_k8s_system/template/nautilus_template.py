# nautilus_templates.py
#
# 🧩 PURPOSE:
# This module provides Kubernetes Pod YAML *templates* and *helpers* 
# for scheduling workloads on the Nautilus (NRP) cluster.
#
# ✨ FEATURES:
# 1. Ready-made templates for common scheduling cases:
#    - Basic pod (tiny resources, easy to run anywhere)
#    - GPU pod (request GPU count)
#    - GPU product REQUIRED (strict affinity to a GPU type)
#    - GPU product PREFERRED (soft affinity, fallback if unavailable)
#    - Geo zone scheduling (pin workload to a region/zone like Korea)
#    - Science-DMZ pods with toleration (run on tainted nodes)
# 2. Templates are available in two forms:
#    - Comment-preserving YAML (ruamel.yaml) for *human readability*
#    - Plain Python dicts for *LLM/tool editing*
# 3. Editing helpers:
#    - JSON Patch (RFC6902) for precise edits
#    - Merge patch (deep merge) for easy overrides
#    - Focused setters (like set GPU product, add toleration, etc.)
#
# 🤖 WHY:
# Makes it easy for LLM agents, tools, or humans to safely construct
# and edit Kubernetes Pod manifests without writing raw YAML.

from __future__ import annotations
from typing import Any, Dict, List, Optional
from copy import deepcopy
import jsonpatch
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap as CMap, CommentedSeq as CSeq

yaml = YAML()
yaml.indent(mapping=2, sequence=2, offset=2)  # nice readable YAML output

# -----------------------------------------------------------------------------
# 🧱 INTERNAL: Helper to wrap dicts/lists into ruamel's CommentedMap
# -----------------------------------------------------------------------------

def _cm(d: Dict[str, Any]) -> CMap:
    """
    Recursively convert Python dict/list → ruamel.yaml's CommentedMap/Seq.
    This preserves ordering and allows comments, so when you dump to a file
    you don’t lose human annotations.
    """
    def convert(x):
        if isinstance(x, dict):
            out = CMap()
            for k, v in x.items():
                out[k] = convert(v)
            return out
        if isinstance(x, list):
            out = CSeq()
            for v in x:
                out.append(convert(v))
            return out
        return x
    return convert(d)

# -----------------------------------------------------------------------------
# 🏗️ TEMPLATE FUNCTIONS (comment-preserving ruamel.yaml versions)
# -----------------------------------------------------------------------------

def base_pod_yaml(
    name: str = "test-pod",
    image: str = "rocker/cuda",
    cpu_m: int = 100,
    mem_mi: int = 100,
) -> CMap:
    """
    Base Pod template:
    - Runs with tiny CPU/memory so it's guaranteed to schedule.
    - Default image = rocker/cuda.
    - Command = sleep infinity (keeps pod alive until deleted).
    Good starting point before adding GPU/affinity rules.
    """
    doc = _cm({
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": name},  # Pod name is unique in namespace
        "spec": {
            "containers": [{
                "name": "mypod",
                "image": image,  # Can be replaced with your own image
                "resources": {
                    "limits": {"cpu": f"{cpu_m}m", "memory": f"{mem_mi}Mi"},
                    "requests": {"cpu": f"{cpu_m}m", "memory": f"{mem_mi}Mi"},
                },
                "command": ["sh", "-c", "sleep infinity"],  # Pod stays alive
            }]
        }
    })
    return doc

def gpu_required_yaml(
    name: str = "test-gpupod",
    gpu_count: int = 1,
    gpu_product: str = "NVIDIA-GeForce-RTX-3090",
    image: str = "rocker/cuda",
    cpu_m: int = 100,
    mem_mi: int = 100,
) -> CMap:
    """
    Pod requiring a *specific GPU product*.
    - Uses nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution
    - Example: must run on RTX-3090 nodes
    - Requests exactly `gpu_count` GPUs.
    """
    doc = _cm({
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": name},
        "spec": {
            "affinity": {  # scheduling constraints
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [{
                            "matchExpressions": [{
                                "key": "nvidia.com/gpu.product",
                                "operator": "In",
                                "values": [gpu_product]  # Hard requirement
                            }]
                        }]
                    }
                }
            },
            "containers": [{
                "name": "mypod",
                "image": image,
                "resources": {
                    "limits": {
                        "cpu": f"{cpu_m}m", "memory": f"{mem_mi}Mi",
                        "nvidia.com/gpu": gpu_count
                    },
                    "requests": {
                        "cpu": f"{cpu_m}m", "memory": f"{mem_mi}Mi",
                        "nvidia.com/gpu": gpu_count
                    },
                },
                "command": ["sh", "-c", "sleep infinity"],
            }]
        }
    })
    return doc

def gpu_preferred_yaml():
    """
    Pod preferring some GPU products but not requiring them.
    - Uses nodeAffinity.preferredDuringSchedulingIgnoredDuringExecution
    - If fast GPUs available → scheduler picks them
    - Otherwise → falls back to anything available.
    """
    ...

def geo_zone_yaml():
    """
    Pod pinned to a specific *geographical zone* (e.g. Korea).
    - Uses node label topology.kubernetes.io/zone
    - Optional: installs curl and calls ipinfo.io to confirm location.
    """
    ...

def scidmz_toleration_yaml():
    """
    Pod targeting a *tainted science-DMZ node*.
    - Requires a toleration (nautilus.io/noceph=NoSchedule).
    - Example: igrok-la.cenic.net node.
    """
    ...

# -----------------------------------------------------------------------------
# 🔄 DICT VERSIONS
# -----------------------------------------------------------------------------
# These functions return plain Python dicts (no comments), ready for:
# - LLM tool-calling
# - Kubernetes API submission (e.g. CoreV1Api.create_namespaced_pod)
# -----------------------------------------------------------------------------

def dict_basic_pod(**kwargs) -> Dict[str, Any]:
    return yaml_to_dict(base_pod_yaml(**kwargs))

# (other dict_* variants wrap the ruamel templates above)

def yaml_to_dict(doc: CMap) -> Dict[str, Any]:
    """
    Convert ruamel.yaml CommentedMap → plain dict.
    Useful when sending manifests programmatically to K8s API.
    """
    import io
    buf = io.StringIO()
    yaml.dump(doc, buf)
    buf.seek(0)
    return YAML().load(buf.getvalue())

# -----------------------------------------------------------------------------
# ✏️ PATCHING HELPERS
# -----------------------------------------------------------------------------
# These functions let you *modify templates safely* instead of rewriting them.
# -----------------------------------------------------------------------------

def apply_json_patch(doc: Dict[str, Any], operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply RFC6902 JSON Patch.
    Example op:
    {"op":"add","path":"/spec/containers/0/resources/limits/nvidia.com~1gpu","value":2}
    """
    return jsonpatch.JsonPatch(operations).apply(deepcopy(doc), in_place=False)

def merge_patch(doc: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge strategy (similar to Kubernetes strategic merge).
    Later values override earlier ones.
    Example: merge_patch(doc, {"spec":{"containers":[{"image":"pytorch/pytorch:latest"}]}})
    """
    def _merge(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            out = deepcopy(a)
            for k, v in b.items():
                out[k] = _merge(a.get(k), v)
            return out
        return deepcopy(b)
    return _merge(doc, patch)

# -----------------------------------------------------------------------------
# 🎛️ FOCUSED SETTERS
# -----------------------------------------------------------------------------
# These are small, opinionated mutators. Easier for LLMs than writing patches.
# -----------------------------------------------------------------------------

def set_gpu_product_required(doc: Dict[str, Any], product: str) -> Dict[str, Any]:
    """Force pod to schedule on nodes with a specific GPU product label."""
    ...

def set_gpu_count(doc: Dict[str, Any], count: int) -> Dict[str, Any]:
    """Update container resource requests/limits for nvidia.com/gpu."""
    ...

def set_zone_required(doc: Dict[str, Any], zone: str) -> Dict[str, Any]:
    """Pin pod to a specific geographical zone via nodeAffinity."""
    ...

def add_toleration_exists(doc: Dict[str, Any], key: str, effect: str = "NoSchedule") -> Dict[str, Any]:
    """Add a toleration that allows scheduling onto tainted nodes."""
    ...

# -----------------------------------------------------------------------------
# 📚 TEMPLATE CATALOG
# -----------------------------------------------------------------------------
# Simple dictionary so LLMs/agents can say `get_template("gpu_required", **kwargs)`
# -----------------------------------------------------------------------------

TEMPLATES = {
    "basic": dict_basic_pod,
    "gpu_required": dict_gpu_required,
    "gpu_preferred": dict_gpu_preferred,
    "geo_zone": dict_geo_zone,
    "scidmz_toleration": dict_scidmz_toleration,
}

def get_template(name: str, **kwargs) -> Dict[str, Any]:
    """
    Retrieve a manifest dict by template name.
    Example:
        pod = get_template("gpu_required", name="mypod", gpu_product="Tesla-V100-SXM2-32GB")
    """
    if name not in TEMPLATES:
        raise KeyError(f"Unknown template: {name}. Options: {list(TEMPLATES)}")
    return TEMPLATES[name](**kwargs)
