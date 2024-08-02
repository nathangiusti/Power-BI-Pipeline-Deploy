import json

def parse_response(response, body=None):
    if response.status_code not in [200, 201, 202, 204]:
        raise Exception(
            f"ERROR: {response.status_code}: {response.content}\n"
            f"URL:{response.url}\n"
            f"Body:\n{json.dumps(body, indent=4)}"
        )
    try:
        return response.json()
    except:
        return "{}"
