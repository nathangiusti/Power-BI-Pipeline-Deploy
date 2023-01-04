import os
import requests


def parse_response(response):
    if response.status_code not in [200, 201, 202, 204]:
        raise Exception(
            "ERROR: {}: {}\nURL: {}".format(
                response.status_code, response.content, response.url
            )
        )
    return response.json()


def main():
    pipeline_id = ''  
    report_id = ''
    client_id = ''
    client_secret = ''
    dataset_id = ''
    tenant_id = ''
    source_stage_order = 0 
    data = {
        "client_id": client_id,
        "grant_type": "client_credentials",
        "resource": "https://analysis.windows.net/powerbi/api",
        "response_mode": "query",
        "client_secret": client_secret,
    }

    resp = requests.get(
        "https://login.microsoftonline.com/{}/oauth2/token".format(tenant_id), data=data
    )
    access_token = resp.json()["access_token"]
    token = {"Authorization": "Bearer {}".format(access_token)}

    body = {
        "sourceStageOrder": source_stage_order, 
        "reports": [{"sourceId": report_id }],
        "options": {
            "allowOverwriteArtifact": True,
            "allowCreateArtifact": True,
            "allowPurgeData": False,
        },
        "updateAppSettings": {
            "updateAppInTargetWorkspace": False  
        }, "datasets": [{ 
            "sourceId": dataset_id
        }] 
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


if __name__ == "__main__":
    main()
