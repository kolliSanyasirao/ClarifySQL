import os
import time
import random
from typing import List

from dotenv import load_dotenv
from loguru import logger

import litellm
from litellm.router import RetryPolicy, AllowedFailsPolicy
from litellm import Router
from litellm.caching import Cache


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------
load_dotenv(".vscode/.env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    error_msg = (
        "ERROR: GEMINI_API_KEY is not set!\n"
        "Please check .vscode/.env and make sure it contains:\n"
        "GEMINI_API_KEY=your-api-key"
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)

logger.info("✓ Gemini API key loaded successfully")


# ---------------------------------------------------------
# LiteLLM cache
# ---------------------------------------------------------
litellm.cache = Cache(
    type="disk",
    disk_cache_dir="../.vscode/.litellm_cache"
)

litellm.enable_cache()
litellm.set_verbose = False
litellm.suppress_debug_info = True


# ---------------------------------------------------------
# Retry configuration
# ---------------------------------------------------------
NUM_RETRIES = 5
RETRY_AFTER = 10

DEFAULT_RETRY_POLICY = RetryPolicy(
    ContentPolicyViolationErrorRetries=3,
    AuthenticationErrorRetries=0,
    BadRequestErrorRetries=1,
    TimeoutErrorRetries=2,
    RateLimitErrorRetries=30,
)

DEFAULT_ALLOWED_FAILS_POLICY = AllowedFailsPolicy(
    ContentPolicyViolationErrorAllowedFails=100,
    RateLimitErrorAllowedFails=100,
)


# ---------------------------------------------------------
# Gemini model
# ---------------------------------------------------------
GEMINI_MODEL = "gemini/gemini-3.5-flash-lite"


# Keep the original model names used by the repository.
# Internally they all use Gemini for now.
MODEL_LIST = [
    {
        "model_name": "llama3-1-70b",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
    {
        "model_name": "llama3-1-8b",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
    {
        "model_name": "claude-3-sonnet",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
    {
        "model_name": "claude-3-haiku",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
    {
        "model_name": "claude-3-5-sonnet",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
    {
        "model_name": "mixtral-8x7b",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
    {
        "model_name": "mixtral-large-2",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
    {
        "model_name": "llama3-1-405b",
        "litellm_params": {
            "model": GEMINI_MODEL,
            "api_key": GEMINI_API_KEY,
        },
    },
]


# ---------------------------------------------------------
# Create LiteLLM router
# ---------------------------------------------------------
def get_litellm_router(cache_responses=True):
    router = Router(
        model_list=MODEL_LIST,
        cache_responses=cache_responses,
    )

    logger.info(
        f"✓ Initialized LiteLLM router with {len(MODEL_LIST)} model aliases"
    )

    return router


DEFAULT_ROUTER = get_litellm_router()


# ---------------------------------------------------------
# Completion helper
# ---------------------------------------------------------
def router_completion_with_ratelimit_retry(
    model: str = "claude-3-5-sonnet",
    messages: List = [],
    router=DEFAULT_ROUTER,
    temperature=0.0,
    top_p=1,
    max_tokens=2048,
    num_retries=NUM_RETRIES,
    retry_after=RETRY_AFTER,
    system: str = None,
):
    start_time = time.time()
    ex = None

    if system:
        messages = [{"role": "system", "content": system}] + messages

    for ith_retry in range(num_retries):
        response_obj = None

        try:
            response_obj = router.completion(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )

            return response_obj.choices[0].message.content

        except Exception as ex:
            if (
                isinstance(ex, litellm.RateLimitError)
                or isinstance(ex, IndexError)
                or isinstance(ex, litellm.ServiceUnavailableError)
                or isinstance(ex, litellm.APIConnectionError)
            ):
                sleep_time = retry_after + (
                    ith_retry * (0.01 + random.random()) * retry_after
                )

                logger.warning(
                    f"Retry {ith_retry + 1}/{num_retries}: "
                    f"{type(ex).__name__}"
                )

                time.sleep(sleep_time)

                if (1 + ith_retry) % 6 == 0:
                    logger.info(
                        f"Sleep for {sleep_time:.2f}s. "
                        f"Time elapsed: {time.time() - start_time:.2f}s"
                    )

            else:
                logger.error(
                    f"Unexpected exception during Gemini completion: {ex}"
                )

                time.sleep(5)

                if ith_retry > num_retries / 3:
                    raise Exception(
                        f"Completion failed: "
                        f"{type(ex).__name__}: {str(ex)}"
                    ) from None

    raise Exception(
        f"Completion failed after {num_retries} retries: "
        f"{type(ex).__name__}: {str(ex)}"
    ) from None


# ---------------------------------------------------------
# Message conversion helper
# ---------------------------------------------------------
def convert_claude_msg_list_to_litellm_msg_list(claude_msg_list):
    litellm_msg_list = []

    for msg in claude_msg_list:
        if (
            isinstance(msg["content"], list)
            and len(msg["content"]) > 0
            and isinstance(msg["content"][0], dict)
        ):
            litellm_msg_list.append(
                {
                    "role": msg["role"],
                    "content": msg["content"][0]["text"],
                }
            )

        elif isinstance(msg["content"], str):
            litellm_msg_list.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
            )

    return litellm_msg_list