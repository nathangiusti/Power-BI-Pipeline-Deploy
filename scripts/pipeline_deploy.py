import os
import sys
from pathlib import Path
import requests
import yaml
from fabric_items import import_fabric_item
from http_helpers import parse_response

def main():
    separator = sys.argv[2]
    file_list = sys.argv[1].split(separator)
    tenant_id = sys.argv[3]
    source_stage_order = sys.argv[4]
    update_app = sys.argv[5]
    allow_purge_data = sys.argv[6]
    config_file = sys.argv[7]
    deploy_datasets = sys.argv[8]

    with open(config_file, "r") as yml_file:
        cfg = yaml.safe_load(yml_file)  # Loading Config file

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
    token = {"Authorization": f"Bearer {access_token}"}

    for file in file_list:
        if file.endswith(".pbip") and os.path.exists(file):
            path = Path(file)
            workspace = os.path.basename(
                path.parent.absolute()
            )  # Get workspace name from parent folder
            file_name = os.path.basename(file)
            display_name = file_name.replace("_", " ")[:-5]
            workspace_id = cfg[workspace]["workspace_id"]
            dir = os.path.dirname(file)
            model_dir = [f for f in os.listdir(dir) if f.endswith((".SemanticModel"))][0]
            model_path = os.path.join(dir, model_dir)

            model_result = import_fabric_item(
                path=model_path,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                item_properties={
                    "type": "SemanticModel",
                    "displayName": display_name,
                },
            )

            print(f"{display_name}.SemanticModel deployed to prod")

            report_dir = [f for f in os.listdir(dir) if f.endswith((".Report"))][0]
            report_path = os.path.join(dir, report_dir)

            import_fabric_item(
                path=report_path,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                item_properties={"semanticModelId": model_result["id"]},
            )

            print(f"{display_name}.Report deployed to prod")
            
        if file.endswith(".pbix") and os.path.exists(file):
            path = Path(file)
            workspace = os.path.basename(
                path.parent.absolute()
            )  # Get workspace name from parent folder
            file_name = os.path.basename(file)

            # For display name, remove .pbix from end
            # For display name, replace _ with ' ' and remove .pbix from end
            display_name = file_name.replace("_", " ")[:-5]

            # Load pipeline ids from config
            pipeline_id = cfg[workspace]["pipeline_id"]

            # Get the workspace id of the source workspace
            response = requests.request(
                "GET", f"https://api.powerbi.com/v1.0/myorg/pipelines/{pipeline_id}?$expand=stages",
                headers=token,
            )
            workspace_id = ""
            response_json = parse_response(response)
            for stage in response_json["stages"]:
                if stage["order"] == int(source_stage_order):
                    workspace_id = stage["workspaceId"]
                
            # Get all assets in target workspace
            response = requests.request(
                "GET",
                f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports",
                headers=token
            )
            response_json = parse_response(response)["value"]

            for report in response_json:
                if (
                    report["reportType"] == "PowerBIReport"
                    and report["name"] == display_name
                ):
                    body = {
                        "sourceStageOrder": source_stage_order,
                        "reports": [{"sourceId": report["id"]}],
                        "options": {
                            "allowOverwriteArtifact": True,
                            "allowCreateArtifact": True,
                            "allowPurgeData": allow_purge_data,
                        },
                        "updateAppSettings": {
                            "updateAppInTargetWorkspace": update_app
                        },
                    }
                    if deploy_datasets:
                        response = requests.request(
                            "GET",
                            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets",
                            headers=token
                        )
                        response_json = parse_response(response)["value"]
                        for dataset in response_json:
                            if report["name"] == display_name:
                                body["datasets"] = [{"sourceId": dataset["id"]}]
                    response = requests.request(
                        "POST",
                        f"https://api.powerbi.com/v1.0/myorg/pipelines/{pipeline_id}/deploy",
                        json=body,
                        headers=token,
                    )

                    parse_response(response, body)
                    print(f"{display_name} deployed to prod")


if __name__ == "__main__":
    main()
