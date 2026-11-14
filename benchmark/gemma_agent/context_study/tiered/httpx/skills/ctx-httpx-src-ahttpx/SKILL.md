---
name: ctx-httpx-src-ahttpx
description: "Package layout of src/ahttpx in encode/httpx, 16 modules"
---

- `src/ahttpx/__init__.py`
- `src/ahttpx/__version__.py`
- `src/ahttpx/_client.py` Defines Client, RedirectMiddleware.
- `src/ahttpx/_content.py` Defines Content, Form, File, Files, JSON, Text, HTML, MultiPart.
- `src/ahttpx/_headers.py` Defines headername, headervalue, Headers, parse_opts_header.
- `src/ahttpx/_network.py` Defines NetworkStream, NetworkServer, NetworkBackend.
- `src/ahttpx/_parsers.py` Defines State, Mode, ProtocolError, HTTPParser, ReadAheadParser, bounded_int, bounded_hex.
- `src/ahttpx/_pool.py` Defines Transport, ConnectionPool, Connection, open_connection.
- `src/ahttpx/_quickstart.py` Defines get, post, put, patch, delete.
- `src/ahttpx/_request.py` Defines Request.
- `src/ahttpx/_response.py` Defines Response.
- `src/ahttpx/_server.py` Defines ConnectionClosed, HTTPConnection, HTTPServer, serve_http, run.
- `src/ahttpx/_streams.py` Defines Stream, ByteStream, DuplexStream, FileStream, HTTPStream, MultiPartStream.
- `src/ahttpx/_urlencode.py` Defines urlencode, urldecode, quote, unquote, percent.
- `src/ahttpx/_urlparse.py`: An implementation of `urlparse` that provides URL validation and normalization Defines InvalidURL, ParseResult, urlparse, encode_host, normalize_port, validate_path, normalize_path, PERCENT, and 2 more.
- `src/ahttpx/_urls.py` Defines URL, QueryParams.
