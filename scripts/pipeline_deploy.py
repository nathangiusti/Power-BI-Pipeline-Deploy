import os
import sys
from pathlib import Path

import requests
import yaml

tenant_id = 'cef04b19-7776-4a94-b89b-375c77a8f936'


# Check whether status is successful, if so, return json value of response
def parse_response(response):
    if response.status_code not in [200, 201, 202, 204]:
        raise Exception('ERROR: {}: {}\nURL: {}'.format(response.status_code, response.content, response.url))
    return response.json()


def main():

    with open('.github/config/deploy_config.yaml', 'r') as yml_file:
        cfg = yaml.safe_load(yml_file)

    data = {
        'client_id': os.environ['CLIENT_ID'],
        'grant_type': 'client_credentials',
        'resource': 'https://analysis.windows.net/powerbi/api',
        'response_mode': 'query',
        'client_secret': os.environ['CLIENT_SECRET']
    }

    resp = requests.get('https://login.microsoftonline.com/{}/oauth2/token'.format(tenant_id), data=data)
    access_token = resp.json()['access_token']
    token = {
        'Authorization': 'Bearer {}'.format(access_token)
    }

    for file in sys.argv:
        if file.endswith('.pbix') and os.path.exists(file):
            path = Path(file)
            workspace = os.path.basename(path.parent.absolute())  # Get workspace name from parent folder
            file_name = os.path.basename(file)

            # For display name, replace _ with ' ' and remove .pbix from end
            display_name = file_name.replace('_', ' ')[:-5]

            # Load workspace and pipeline ids from config
            workspace_id = cfg[workspace]['test_workspace_id']
            pipeline_id = cfg[workspace]['pipeline_id']

            # Get all assets in target workspace
            response = requests.request("GET", "https://api.powerbi.com/v1.0/myorg/groups/{}/reports"
                                        .format(workspace_id), headers=token)
            response_json = parse_response(response)['value']

            for report in response_json:
                if report['reportType'] == 'PowerBIReport' and report['name'] == display_name:
                    body = {
                        "sourceStageOrder": 1,
                        "reports": [{"sourceId": report['id']}],
                        "options": {
                            "allowOverwriteArtifact": True,
                            "allowCreateArtifact": True,
                            "allowPurgeData": False  # Should not be needed because this is for reports but fail safe
                        },
                        "updateAppSettings": {
                            "updateAppInTargetWorkspace": True
                        }
                    }
                    response = requests.request("POST", "https://api.powerbi.com/v1.0/myorg/pipelines/{}/deploy"
                                                .format(pipeline_id), json=body, headers=token)

                    parse_response(response)
                    print("{} deployed to prod".format(display_name))


if __name__ == '__main__':
    main()
