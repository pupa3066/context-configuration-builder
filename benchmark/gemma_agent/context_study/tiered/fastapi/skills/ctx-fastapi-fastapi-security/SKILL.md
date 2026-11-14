---
name: ctx-fastapi-fastapi-security
description: "Package layout of fastapi/security in fastapi/fastapi, 7 modules"
---

- `fastapi/security/__init__.py`
- `fastapi/security/api_key.py` Defines APIKeyBase, APIKeyQuery, APIKeyHeader, APIKeyCookie.
- `fastapi/security/base.py` Defines SecurityBase.
- `fastapi/security/http.py` Defines HTTPBasicCredentials, HTTPAuthorizationCredentials, HTTPBase, HTTPBasic, HTTPBearer, HTTPDigest.
- `fastapi/security/oauth2.py` Defines OAuth2PasswordRequestForm, OAuth2PasswordRequestFormStrict, OAuth2, OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer, SecurityScopes.
- `fastapi/security/open_id_connect_url.py` Defines OpenIdConnect.
- `fastapi/security/utils.py` Defines get_authorization_scheme_param.
