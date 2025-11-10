"""Additional views and reverse proxy endpoints for IIIF."""

from flask import Blueprint, Response, request
import requests
from urllib.parse import quote

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
        # Reconstruct the upstream URL while preserving the IIIF identifier semantics.
        # We extract the decoded path, isolate the identifier segment, re-encode it,
        # and then append the remaining operation segments and original query string.
        decoded_path = request.path  # e.g., /iiif/2/https://host/.../files/x.pdf/full/1200,/0/default.jpg
        if "/iiif/" not in decoded_path:
            return Response("Bad IIIF request", status=400)
        after_prefix = decoded_path.split("/iiif/", 1)[1]  # e.g., 2/https://host/.../files/x.pdf/full/...
        if "/" not in after_prefix:
            return Response("Bad IIIF path", status=400)
        version, rest = after_prefix.split("/", 1)
        # Determine whether this is an info.json or image request
        if rest.endswith("/info.json"):
            # identifier is everything before the trailing /info.json
            id_part = rest[: -len("/info.json")]
            op_part = "/info.json"
        else:
            # assume image request and find the operation pivot (e.g., /full/)
            pivot = "/full/"
            pivot_pos = rest.find(pivot)
            if pivot_pos == -1:
                # Fallback: try to split at the last slash before parameters
                last_slash = rest.rfind("/")
                if last_slash <= 0:
                    return Response("Unsupported IIIF path", status=400)
                id_part = rest[:last_slash]
                op_part = rest[last_slash:]
            else:
                id_part = rest[:pivot_pos]
                op_part = rest[pivot_pos:]
        # Re-encode identifier so that slashes are percent-encoded as required by IIIF
        encoded_id = quote(id_part, safe="")
        # Reconstruct upstream URL
        target_url = f"{target_base}/{version}/{encoded_id}{op_part}"
        # Append original query string if any
        if request.query_string:
            target_url = f"{target_url}?{request.query_string.decode('utf-8')}"

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

        def generate():
            for chunk in upstream.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        excluded = {"transfer-encoding", "content-encoding", "connection"}
        resp_headers = [
            (k, v) for k, v in upstream.headers.items() if k.lower() not in excluded
        ]
        return Response(generate(), status=upstream.status_code, headers=resp_headers)

    return blueprint
