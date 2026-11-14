---
name: ctx-fastapi-fastapi
description: "Package layout of fastapi in fastapi/fastapi, 23 modules"
---

- `fastapi/__init__.py`: FastAPI framework, high performance, easy to learn, fast to code, ready for production
- `fastapi/__main__.py`
- `fastapi/applications.py` Defines FastAPI.
- `fastapi/background.py` Defines BackgroundTasks.
- `fastapi/cli.py` Defines main.
- `fastapi/concurrency.py` Defines contextmanager_in_threadpool.
- `fastapi/datastructures.py` Defines UploadFile, DefaultPlaceholder, Default.
- `fastapi/encoders.py` Defines isoformat, decimal_encoder, generate_encoders_by_class_tuples, jsonable_encoder.
- `fastapi/exception_handlers.py` Defines http_exception_handler, request_validation_exception_handler, websocket_request_validation_exception_handler.
- `fastapi/exceptions.py` Defines EndpointContext, HTTPException, WebSocketException, FastAPIError, DependencyScopeError, ValidationException, RequestValidationError, WebSocketRequestValidationError, and 3 more.
- `fastapi/logger.py`
- `fastapi/param_functions.py` Defines Path, Query, Header, Cookie, Body, Form, File, Depends, and 1 more.
- `fastapi/params.py` Defines ParamTypes, Param, Path, Query, Header, Cookie, Body, Form, and 3 more.
- `fastapi/requests.py`
- `fastapi/responses.py` Defines UJSONResponse, ORJSONResponse.
- `fastapi/routing.py` Defines request_response, websocket_session, serialize_response, run_endpoint_function, get_request_handler, get_websocket_app, APIWebSocketRoute, APIRoute, and 1 more.
- `fastapi/sse.py` Defines EventSourceResponse, ServerSentEvent, format_sse_event.
- `fastapi/staticfiles.py`
- `fastapi/templating.py`
- `fastapi/testclient.py`
- `fastapi/types.py`
- `fastapi/utils.py` Defines is_body_allowed_for_status_code, get_path_param_names, create_model_field, generate_operation_id_for_path, generate_unique_id, deep_dict_update, get_value_or_default.
- `fastapi/websockets.py`
