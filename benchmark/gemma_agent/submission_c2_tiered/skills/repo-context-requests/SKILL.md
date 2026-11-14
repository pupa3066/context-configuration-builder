---
name: repo-context-requests
description: Context file for psf/requests: package layout, module summaries and tests, generated from the repository snapshot.
---

# Repository context: psf/requests

Source: snapshot at commit 6f205ff422bc.

## Tests

Tests live in `tests/` (9 test files).

Pytest settings from the repository's own config:

```
pyproject.toml [tool.pytest.ini_options]
  addopts = "--doctest-modules"
  doctest_optionflags = "NORMALIZE_WHITESPACE ELLIPSIS"
  minversion = "6.2"
  testpaths = ["tests"]
```

## Package layout

- `src/requests/__init__.py`: Requests HTTP Library Defines check_compatibility.
- `src/requests/__version__.py`
- `src/requests/_internal_utils.py`: requests._internal_utils Defines to_native_string, unicode_is_ascii.
- `src/requests/_types.py`: requests._types Defines SupportsRead, SupportsItems, is_prepared.
- `src/requests/adapters.py`: requests.adapters Defines BaseAdapter, HTTPAdapter.
- `src/requests/api.py`: requests.api Defines request, get, options, head, post, put, patch, delete.
- `src/requests/auth.py`: requests.auth Defines AuthBase, HTTPBasicAuth, HTTPProxyAuth, HTTPDigestAuth.
- `src/requests/certs.py`: requests.certs
- `src/requests/compat.py`: requests.compat
- `src/requests/cookies.py`: requests.cookies Defines MockRequest, MockResponse, extract_cookies_to_jar, get_cookie_header, remove_cookie_by_name, CookieConflictError, RequestsCookieJar, create_cookie, and 5 more.
- `src/requests/exceptions.py`: requests.exceptions Defines RequestException, InvalidJSONError, JSONDecodeError, HTTPError, ConnectionError, ProxyError, SSLError, Timeout, and 17 more.
- `src/requests/help.py`: Module containing bug report helper(s). Defines info, main.
- `src/requests/hooks.py`: requests.hooks Defines default_hooks, dispatch_hook.
- `src/requests/models.py`: requests.models Defines RequestEncodingMixin, RequestHooksMixin, Request, PreparedRequest, Response.
- `src/requests/packages.py`
- `src/requests/sessions.py`: requests.sessions Defines merge_setting, merge_hooks, SessionRedirectMixin, Session, session.
- `src/requests/status_codes.py`: The ``codes`` object defines a mapping from common names for HTTP statuses
- `src/requests/structures.py`: requests.structures Defines CaseInsensitiveDict, LookupDict.
- `src/requests/utils.py`: requests.utils Defines dict_to_sequence, super_len, get_netrc_auth, guess_filename, extract_zipped_paths, atomic_open, from_key_val_list, to_key_val_list, and 34 more.
