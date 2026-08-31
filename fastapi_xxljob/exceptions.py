"""
FastAPI-XXLJob 异常类型。

FastAPI-XXLJob exception types.

所有异常都继承统一基类 :class:`FastAPIXXLJobError`。为了兼容通用 XXL-JOB 命名，
``XXLJobError`` 与部分异常名保留为别名或子类。异常信息中绝不包含 Access Token。

All exceptions inherit from the single base :class:`FastAPIXXLJobError`. For
compatibility with common XXL-JOB naming, ``XXLJobError`` and several related
names are retained as aliases or subclasses. Exception messages never contain
the access token.
"""

from __future__ import annotations


class FastAPIXXLJobError(Exception):
    """
    所有 FastAPI-XXLJob 异常的统一基类。

    The single base class for all FastAPI-XXLJob exceptions.
    """


# 通用命名兼容别名 / Compatibility alias for the generic name.
XXLJobError = FastAPIXXLJobError


class XXLJobConfigurationError(FastAPIXXLJobError):
    """
    配置缺失或类型不正确时抛出。

    Raised when configuration is missing or has an incorrect type.
    """


# 通用命名兼容别名 / Compatibility alias for the concise name.
XXLJobConfigError = XXLJobConfigurationError


class XXLJobInitializationError(FastAPIXXLJobError):
    """
    扩展初始化相关错误的基类。

    Base class for extension-initialization errors.
    """


class XXLJobAlreadyInitializedError(XXLJobInitializationError):
    """
    在同一个 FastAPI 应用上重复初始化扩展时抛出。

    Raised when the extension is initialized more than once for the same
    FastAPI application.
    """


class XXLJobCallbackRegistrationError(FastAPIXXLJobError):
    """
    请求处理函数注册失败时抛出（例如重复注册且未指定 ``replace=True``）。

    Raised when request-callback registration fails (for example a duplicate
    registration without ``replace=True``).
    """


class XXLJobValidationError(FastAPIXXLJobError):
    """
    公共 API 参数无效时抛出（例如类型错误的整数参数）。

    Raised when public API arguments are invalid (for example an integer
    argument with the wrong type).
    """


# 通用命名兼容别名 / Compatibility alias for request validation errors.
XXLJobRequestError = XXLJobValidationError


class XXLJobProtocolError(FastAPIXXLJobError):
    """
    Admin 返回的响应无法按官方协议解析时抛出。

    Raised when an admin response cannot be parsed according to the official
    protocol.
    """


class XXLJobAdminCallError(FastAPIXXLJobError):
    """
    调用 XXL-JOB Admin 接口失败相关错误的基类。

    Base class for failures when calling XXL-JOB admin APIs.
    """


class XXLJobCallbackError(XXLJobAdminCallError):
    """
    调用 XXL-JOB Admin 回调接口失败时抛出。

    Raised when a callback request to the XXL-JOB admin fails.
    """


class XXLJobRegistryError(XXLJobAdminCallError):
    """
    执行器注册或注销失败时抛出。

    Raised when executor registration or deregistration fails.
    """
