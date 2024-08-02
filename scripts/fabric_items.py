import os
import json
import base64
import requests
from http_helpers import parse_response

def import_fabric_item(path, workspace_id, tenant_id, item_properties=None):
    """
    Imports items using the Power BI Project format (PBIP) into a Fabric workspace from a specified file system source.

    :param path: Path to the folder containing the PBIP files
    :param workspace_id: ID of the Fabric workspace
    :param item_properties: Dictionary to override item properties like type, displayName
    """
    # Search for folders with .pbir and .pbism in it
    items_in_folder = [f for f in os.listdir(path) if f.endswith((".pbism", ".pbir"))]

    if not items_in_folder:
        print(f"Cannot find valid item definitions (*.pbir; *.pbism) in the '{path}'")
        return

    if any(f.endswith(".pbir") for f in items_in_folder):
        item_type = "Report"
    elif any(f.endswith(".pbism") for f in items_in_folder):
        item_type = "SemanticModel"
    else:
        raise ValueError("Cannot determine the itemType.")

    # Get existing items of the workspace
    items = invoke_fabric_api_request(
        f"workspaces/{workspace_id}/items", tenant_id, method="GET"
    )
    print(f"Existing items in the workspace: {len(items)}")

    # Get all files in the directory
    files = [
        os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames
    ]

    # Remove files not required for the API
    files = [
        f
        for f in files
        if not (f.endswith(".abf") or "item." in f or f.endswith(".pbi"))
    ]

    # Get display name from item_properties or .platform file
    display_name = item_properties.get("displayName") if item_properties else None

    if (not item_type or not display_name) and os.path.exists(
        os.path.join(path, ".platform")
    ):
        with open(os.path.join(path, ".platform"), "r") as f:
            item_metadata = json.load(f)
        item_type = item_metadata["metadata"]["type"]
        display_name = item_metadata["metadata"]["displayName"]

    if not item_type or not display_name:
        raise ValueError(
            "Cannot import item if any of the following properties is missing: itemType, displayName"
        )

    # Prepare parts for the payload
    parts = []
    for file_path in files:
        with open(file_path, "rb") as f:
            file_content = f.read()

        if file_path.endswith(".pbir"):
            pbir_json = json.loads(file_content)
            if pbir_json.get("datasetReference", {}).get("byPath"):
                dataset_id = item_properties.get("semanticModelId")
                if not dataset_id:
                    raise ValueError(
                        "Cannot import directly a report using byPath connection. You must first resolve the semantic model id and pass it through the 'itemProperties' parameter."
                    )

                pbir_json["datasetReference"] = {
                    "byConnection": {
                        "connectionString": None,
                        "pbiServiceModelId": None,
                        "pbiModelVirtualServerName": "sobe_wowvirtualserver",
                        "pbiModelDatabaseName": dataset_id,
                        "name": "EntityDataSource",
                        "connectionType": "pbiServiceXmlaStyleLive",
                    }
                }
                file_content = json.dumps(pbir_json).encode("utf-8")

        part_path = os.path.relpath(file_path, path).replace("\\", "/")
        parts.append(
            {
                "Path": part_path,
                "Payload": base64.b64encode(file_content).decode("utf-8"),
                "PayloadType": "InlineBase64",
            }
        )

    print("Payload parts:")
    for part in parts:
        print(f"part: {part['Path']}")

    # Check if item already exists
    existing_item = next(
        (
            item
            for item in items["value"]
            if item["type"].lower() == item_type.lower()
            and item["displayName"].lower() == display_name.lower()
        ),
        None,
    )

    if existing_item:
        print(f"Item '{display_name}' of type '{item_type}' already exists. Updating item definition")
        item_id = existing_item["id"]
        item_request = {"definition": {"Parts": parts}}
        invoke_fabric_api_request(
            f"workspaces/{workspace_id}/items/{item_id}/updateDefinition",
            tenant_id,
            method="POST",
            json=item_request,
        )
        print(f"Updated item with ID '{item_id}'")
    else:
        print("Creating a new item")
        item_request = {
            "displayName": display_name,
            "type": item_type,
            "definition": {"Parts": parts},
        }
        create_item_result = invoke_fabric_api_request(
            f"workspaces/{workspace_id}/items",
            tenant_id,
            method="POST",
            json=item_request,
        )
        item_id = create_item_result["id"]
        print(f"Created a new item with ID '{item_id}'")

    return {"id": item_id, "displayName": display_name, "type": item_type}


def invoke_fabric_api_request(uri, tenant_id, method="GET", json=None):
    """
    Helper function to make API requests to Fabric API
    Note: You need to implement authentication here
    """
    data = {
        "client_id": os.environ["CLIENT_ID"],
        "grant_type": "client_credentials",
        "resource": "https://analysis.windows.net/powerbi/api",
        "response_mode": "query",
        "client_secret": os.environ["CLIENT_SECRET"],
    }

    resp = requests.get(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/token", data=data
    )
    access_token = resp.json()["access_token"]

    base_url = "https://api.fabric.microsoft.com/v1/"  # Replace with actual Fabric API base URL
    headers = {
        "Authorization": "Bearer {}".format(access_token),
        "Content-Type": "application/json",
    }

    response = requests.request(method, base_url + uri, headers=headers, json=json)
    return parse_response(response)
