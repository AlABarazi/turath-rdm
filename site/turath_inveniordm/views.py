"""Additional views and reverse proxy endpoints for IIIF."""

from flask import Blueprint, Response, request
import requests
import json
import re
from urllib.parse import quote, unquote

#
# Registration
#
def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "turath_inveniordm",
        __name__,
        template_folder="./templates",
        static_folder="./static",
    )

    # Add URL rules

    @blueprint.route("/iiif/<path:path>", methods=["GET", "HEAD"])  # Same-origin HTTPS proxy
    def proxy_iiif(path):
        """Reverse-proxy to local Cantaloupe to avoid mixed-content in dev.

        Maps https://127.0.0.1:5000/iiif/<path>?<query>
        to   http://127.0.0.1:8182/iiif/<path>?<query>
        """
        target_base = "http://127.0.0.1:8182/iiif"
        # Parse version and remaining path from route parameter (decoded by Werkzeug)
        # Example: path = "2/https://host.../files/x.pdf/full/256,/0/default.jpg"
        if "/" not in path:
            return Response("Bad IIIF path", status=400)
        version, rest = path.split("/", 1)

        # Extract identifier and operation part robustly.
        # The identifier is a URL (http/https) and may contain many '/'.
        # We detect operation by known prefixes: '/info.json' or '/full/'.
        id_raw = rest
        op_part = ""
        if "/info.json" in rest:
            idx = rest.rfind("/info.json")
            before = rest[:idx]
            # Determine if a page prefix exists just before info.json (e.g., /p2/info.json)
            pseg = before.rsplit("/", 1)[-1] if "/" in before else before
            if pseg.startswith("p") and pseg[1:].isdigit():
                id_raw = before.rsplit("/", 1)[0] if "/" in before else ""
                op_part = f"{pseg}/info.json"
            else:
                id_raw = before
                op_part = "info.json"
        elif "/full/" in rest:
            idx = rest.find("/full/")
            before = rest[:idx]
            after = rest[idx + 1 :]  # 'full/...' without leading '/'
            pseg = before.rsplit("/", 1)[-1] if "/" in before else before
            if pseg.startswith("p") and pseg[1:].isdigit():
                id_raw = before.rsplit("/", 1)[0] if "/" in before else ""
                op_part = f"{pseg}/{after}"
            else:
                id_raw = before
                op_part = after
        elif re.search(r"/p(\d+)/", rest):
            # Page-qualified region/size requests, e.g., .../<id>/p2/0,0,948,1380/...
            m = re.search(r"/p(\d+)/", rest)
            idx = m.start()
            id_raw = rest[:idx]
            # op_part should start with 'pN/...'
            op_part = rest[idx + 1 :]
        else:
            # Fallback: split once (may fail for complex identifiers but keeps compatibility)
            if "/" in rest:
                id_raw, op_part = rest.split("/", 1)
            else:
                id_raw, op_part = rest, ""

        encoded_id = quote(unquote(id_raw), safe="!")

        # Support page-qualified routes like .../{encoded_id}/p{N}/... by mapping to upstream ?page=N
        page_param = None
        if op_part.startswith("p") and "/" in op_part:
            pseg, remainder = op_part.split("/", 1)
            if pseg[1:].isdigit():
                page_param = int(pseg[1:])
                op_part = remainder  # strip the p{N}/ prefix

        # Build upstream URL path (preserve op_part exactly)
        upstream_path = f"{version}/{encoded_id}"
        if op_part:
            upstream_path = f"{upstream_path}/{op_part}"
        target_url = f"{target_base}/{upstream_path}"
        # Append query string and/or page parameter
        qs = request.query_string.decode("utf-8") if request.query_string else ""
        if page_param is not None:
            qs = (qs + ("&" if qs else "") + f"page={page_param}")
        if qs:
            target_url = f"{target_url}?{qs}"

        # Forward selected headers
        fwd_headers = {}
        for h in ("Accept", "Range", "If-Modified-Since", "If-None-Match"):
            if h in request.headers:
                fwd_headers[h] = request.headers[h]

        # Stream the response back to the client
        try:
            upstream = requests.request(
                method=request.method,
                url=target_url,
                headers=fwd_headers,
                stream=True,
                timeout=30,
            )
        except requests.RequestException:
            return Response("Upstream IIIF server unavailable", status=502)

        excluded = {"transfer-encoding", "content-encoding", "connection"}

        # info.json rewrite to same-origin @id (preserve page-qualified '@id' when pN used)
        if op_part.endswith("info.json"):
            try:
                data = upstream.json()
            except ValueError:
                try:
                    data = json.loads(upstream.content.decode("utf-8", "ignore"))
                except Exception:
                    data = {}
            route_prefix = request.path.split("/", 2)[1]
            base_id = (
                f"{request.host_url.rstrip('/')}/{route_prefix}/{version}/{encoded_id}"
            )
            if page_param is not None:
                base_id = f"{base_id}/p{page_param}"
            if isinstance(data, dict):
                data["@id"] = base_id
            body = json.dumps(data)
            resp_headers = [
                (k, v) for k, v in upstream.headers.items() if k.lower() not in excluded
            ]
            resp_headers = [(k, v) for k, v in resp_headers if k.lower() != "content-type"]
            resp_headers.append(("Content-Type", "application/json"))
            return Response(body, status=upstream.status_code, headers=resp_headers)

        def generate():
            for chunk in upstream.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        resp_headers = [
            (k, v) for k, v in upstream.headers.items() if k.lower() not in excluded
        ]
        return Response(generate(), status=upstream.status_code, headers=resp_headers)

    @blueprint.route("/iiif-pdf/<path:path>", methods=["GET", "HEAD"])
    def proxy_iiif_pdf(path):
        return proxy_iiif(path)

    return blueprint
