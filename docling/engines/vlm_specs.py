"""VLM presets for the Amir Engine.

Docling ships picture-description presets for ``smolvlm``, ``granite_vision``
and ``pixtral``. We add ``qwen25_vl_3b`` here so a future swap to Qwen3-VL is
a one-line edit (change the ``default_repo_id``).

Use :func:`build_picture_description_options` from
:class:`docling.engines.PdfEngine` via the ``picture_description=`` flag.
"""

from __future__ import annotations

from typing import Literal

from docling.datamodel.pipeline_options import (
    PictureDescriptionVlmEngineOptions,
    PictureDescriptionVlmOptions,
)
from docling.datamodel.pipeline_options_vlm_model import ResponseFormat
from docling.datamodel.stage_model_specs import VlmModelSpec
from docling.datamodel.vlm_engine_options import (
    BaseVlmEngineOptions,
    TransformersVlmEngineOptions,
    VllmVlmEngineOptions,
    VlmEngineType,
)

PictureDescriptionPreset = Literal[
    "smolvlm",
    "granite_vision",
    "pixtral",
    "qwen25_vl_3b",
]
PictureDescriptionEngine = Literal["vllm", "transformers", "default"]

# Custom Qwen2.5-VL-3B model spec — Docling's bundled Qwen preset is for the
# full-page VlmConvert stage, not picture description, so we declare our own.
QWEN25_VL_3B_PICTURE_DESC_SPEC = VlmModelSpec(
    name="Qwen2.5-VL-3B-Instruct",
    default_repo_id="Qwen/Qwen2.5-VL-3B-Instruct",
    prompt="Describe this image in one or two concise sentences. Be specific and factual.",
    response_format=ResponseFormat.MARKDOWN,
    max_new_tokens=200,
)


def build_picture_description_options(
    preset: PictureDescriptionPreset,
    *,
    engine: PictureDescriptionEngine = "vllm",
) -> PictureDescriptionVlmEngineOptions | PictureDescriptionVlmOptions:
    """Construct picture-description options for the chosen preset.

    For ``qwen25_vl_3b`` we build a fresh :class:`PictureDescriptionVlmEngineOptions`
    with the Qwen model spec; for everything else we use Docling's registered
    preset via ``from_preset``. The ``engine`` argument selects the runtime
    (``vllm`` for high-throughput serving, ``transformers`` for direct HF
    inference, ``default`` to let Docling decide).
    """
    engine_opts = _engine_options(engine)

    if preset == "qwen25_vl_3b":
        kwargs: dict = {"model_spec": QWEN25_VL_3B_PICTURE_DESC_SPEC}
        if engine_opts is not None:
            kwargs["engine_options"] = engine_opts
        return PictureDescriptionVlmEngineOptions(**kwargs)

    if engine_opts is not None:
        return PictureDescriptionVlmEngineOptions.from_preset(
            preset, engine_options=engine_opts
        )
    return PictureDescriptionVlmEngineOptions.from_preset(preset)


def _engine_options(engine: PictureDescriptionEngine) -> BaseVlmEngineOptions | None:
    if engine == "vllm":
        return VllmVlmEngineOptions(engine_type=VlmEngineType.VLLM)
    if engine == "transformers":
        return TransformersVlmEngineOptions(engine_type=VlmEngineType.TRANSFORMERS)
    return None
