import os
import sys
from pathlib import Path
import requests
import yaml


# Check whether status is successful, if so, return json value of response
def parse_response(response):
    if response.status_code not in [200, 201, 202, 204]:
        raise Exception(
            "ERROR: {}: {}\nURL: {}".format(
                response.status_code, response.content, response.url
            )
        )
    return response.json()


def main():

    config_file = sys.argv[7]
    with open(config_file, "r") as yml_file:
        cfg = yaml.safe_load(yml_file)  # Loading Config file

    data = {
        "client_id": os.environ["CLIENT_ID"],
        "grant_type": "client_credentials",
        "resource": "https://analysis.windows.net/powerbi/api",
        "response_mode": "query",
        "client_secret": os.environ["CLIENT_SECRET"],
    }
    tenant_id = sys.argv[3]  # P3
    resp = requests.get(
        "https://login.microsoftonline.com/{}/oauth2/token".format(tenant_id), data=data
    )
    access_token = resp.json()["access_token"]
    token = {"Authorization": "Bearer {}".format(access_token)}

    separator = sys.argv[2]  # P2
    file_list = sys.argv[1].split(separator)  # P1
    source_stage_order = sys.argv[4]

    for file in file_list:
        if file.endswith(".pbix") and os.path.exists(file):
            path = Path(file)
            workspace = os.path.basename(
                path.parent.absolute()
            )  # Get workspace name from parent folder
            file_name = os.path.basename(file)

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
                "https://api.powerbi.com/v1.0/myorg/groups/{}/reports".format(
                    workspace_id
                ),
                headers=token,
            )
            response_json = parse_response(response)["value"]

            for report in response_json:
                if (
                    report["reportType"] == "PowerBIReport"
                    and report["name"] == display_name
                ):
                    body = {
                        "sourceStageOrder": sys.argv[4],  # P4
                        "reports": [{"sourceId": report["id"]}],
                        "options": {
                            "allowOverwriteArtifact": True,
                            "allowCreateArtifact": True,
                            # Should not be needed because this is for reports but fail safe
                            "allowPurgeData": sys.argv[6],
                        },
                        "updateAppSettings": {
                            "updateAppInTargetWorkspace": sys.argv[5]  # P5
                        },
                    }
                    response = requests.request(
                        "POST",
                        "https://api.powerbi.com/v1.0/myorg/pipelines/{}/deploy".format(
                            pipeline_id
                        ),
                        json=body,
                        headers=token,
                    )
                    parse_response(response)
                    print("{} deployed to prod".format(display_name))


if __name__ == "__main__":
    main()
