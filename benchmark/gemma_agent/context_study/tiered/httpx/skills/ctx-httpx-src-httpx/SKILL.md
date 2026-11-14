---
name: ctx-httpx-src-httpx
description: "Package layout of src/httpx in encode/httpx, 16 modules"
---

- `src/httpx/__init__.py`
- `src/httpx/__version__.py`
- `src/httpx/_client.py` Defines Client, RedirectMiddleware.
- `src/httpx/_content.py` Defines Content, Form, File, Files, JSON, Text, HTML, MultiPart.
- `src/httpx/_headers.py` Defines headername, headervalue, Headers, parse_opts_header.
- `src/httpx/_network.py` Defines timeout, get_current_timeout, NetworkStream, NetworkListener, NetworkServer, NetworkBackend.
- `src/httpx/_parsers.py` Defines State, Mode, ProtocolError, HTTPParser, ReadAheadParser, bounded_int, bounded_hex.
- `src/httpx/_pool.py` Defines Transport, ConnectionPool, Connection, open_connection.
- `src/httpx/_quickstart.py` Defines get, post, put, patch, delete.
- `src/httpx/_request.py` Defines Request.
- `src/httpx/_response.py` Defines Response.
- `src/httpx/_server.py` Defines ConnectionClosed, HTTPConnection, HTTPServer, serve_http, run.
- `src/httpx/_streams.py` Defines Stream, ByteStream, DuplexStream, FileStream, HTTPStream, MultiPartStream.
- `src/httpx/_urlencode.py` Defines urlencode, urldecode, quote, unquote, percent.
- `src/httpx/_urlparse.py`: An implementation of `urlparse` that provides URL validation and normalization Defines InvalidURL, ParseResult, urlparse, encode_host, normalize_port, validate_path, normalize_path, PERCENT, and 2 more.
- `src/httpx/_urls.py` Defines URL, QueryParams.
