# Repository context: fastapi/fastapi

Source: snapshot at commit ee22a4b8ca46.

## Tests

Tests live in `tests/` (482 test files).

## Documentation examples

`docs_src/` holds 454 example Python files used by the documentation, in folders: additional_responses, additional_status_codes, advanced_middleware, app_testing, async_tests, authentication_error_status_code, background_tasks, behind_a_proxy, bigger_applications, body, body_fields, body_multiple_params, body_nested_models, body_updates, conditional_openapi, configure_swagger_ui, cookie_param_models, cookie_params, cors, custom_docs_ui, custom_request_and_route, custom_response, dataclasses_, debugging, dependencies, dependency_testing, encoder, events, extending_openapi, extra_data_types, extra_models, first_steps, generate_clients, graphql_, handling_errors, header_param_models, header_params, json_base64_bytes, metadata, middleware, and 36 more.

## Package layout

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
- `fastapi/_compat/__init__.py`
- `fastapi/_compat/shared.py` Defines lenient_issubclass, field_annotation_is_sequence, value_is_sequence, field_annotation_is_complex, field_annotation_is_scalar, field_annotation_is_scalar_sequence, is_bytes_or_nonable_bytes_annotation, is_uploadfile_or_nonable_uploadfile_annotation, and 5 more.
- `fastapi/_compat/v2.py` Defines evaluate_forwardref, GenerateJsonSchema, asdict, ModelField, get_schema_from_model_field, get_definitions, is_scalar_field, copy_field_info, and 11 more.
- `fastapi/dependencies/__init__.py`
- `fastapi/dependencies/models.py` Defines Dependant.
- `fastapi/dependencies/utils.py` Defines ensure_multipart_is_installed, get_parameterless_sub_dependant, get_flat_dependant, get_flat_params, get_typed_signature, get_typed_annotation, get_typed_return_annotation, get_stream_item_type, and 12 more.
- `fastapi/middleware/__init__.py`
- `fastapi/middleware/asyncexitstack.py` Defines AsyncExitStackMiddleware.
- `fastapi/middleware/cors.py`
- `fastapi/middleware/gzip.py`
- `fastapi/middleware/httpsredirect.py`
- `fastapi/middleware/trustedhost.py`
- `fastapi/middleware/wsgi.py`
- `fastapi/openapi/__init__.py`
- `fastapi/openapi/constants.py`
- `fastapi/openapi/docs.py` Defines get_swagger_ui_html, get_redoc_html, get_swagger_ui_oauth2_redirect_html.
- `fastapi/openapi/models.py` Defines BaseModelWithConfig, Contact, License, Info, ServerVariable, Server, Reference, Discriminator, and 32 more.
- `fastapi/openapi/utils.py` Defines get_openapi_security_definitions, get_openapi_operation_request_body, generate_operation_id, generate_operation_summary, get_openapi_operation_metadata, get_openapi_path, get_fields_from_routes, get_openapi.
- `fastapi/security/__init__.py`
- `fastapi/security/api_key.py` Defines APIKeyBase, APIKeyQuery, APIKeyHeader, APIKeyCookie.
- `fastapi/security/base.py` Defines SecurityBase.
- `fastapi/security/http.py` Defines HTTPBasicCredentials, HTTPAuthorizationCredentials, HTTPBase, HTTPBasic, HTTPBearer, HTTPDigest.
- `fastapi/security/oauth2.py` Defines OAuth2PasswordRequestForm, OAuth2PasswordRequestFormStrict, OAuth2, OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer, SecurityScopes.
- `fastapi/security/open_id_connect_url.py` Defines OpenIdConnect.
- `fastapi/security/utils.py` Defines get_authorization_scheme_param.
