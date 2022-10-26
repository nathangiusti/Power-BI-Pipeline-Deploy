# PBIX Pipeline Deploy

Deploys a PBIX file between stages in a Power BI Pipeline

# Set Up

Add an environment variable to your GitHub repo for your service principle's id and secret key. 
Pass these credentials to the action as seen in the usage example below

Create a yaml config file and place it in your repo.
The config file will map folder names to pipeline ids. This allows the action to deploy to multiple pipeline from a single repository. 

Example:

```yaml
    My_Workspace:
      pipeline_id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    My_other_workspace:
      pipeline_id:  'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
```

PBIX file should be placed in a folder which corresponds to the key in the deploy config file. 

For the sample config there would be two folders with PBIX files, My_Workspace and My_other_workspace.

A PBIX file placed in a folder called Workspace_name1 will be deployed via the pipeline id listed in the config file. 

The folder does not need to be at root. 

/foo/bar/Workspsace_name1/myfile.pbix will deploy myfile.pbix to the pipeline listed in the config file for Workspace_name1


# Usage

```yaml
    name: Migrate via Pipeline
    on:
      push:
        branches:
          - main
    jobs:
      Deploy-Asset:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v2
            with:
              fetch-depth: 0
          - name: Get changed files
            id: changed-files
            uses: tj-actions/changed-files@v12
            with:
              separator: ","
              quotepath: false
          - name: Power BI Pipeline Deploy
            uses: nathangiusti/Power-BI-Pipeline-Deploy@v2.4
            with:
              files: ${{ steps.changed-files.outputs.all_modified_files }}
              separator: ","
              tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              config_file: ".github/config/pipeline-deploy-config.yaml"
            env:
              CLIENT_ID: ${{ secrets.CLIENT_ID }}
              CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
```


|               Input               |          type          | required |        default        |                                                                                                                                                          description                                                                                                                                                          |
|:---------------------------------:|:----------------------:|:--------:|:---------------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| files | `string` | `true` | | List of files to process. Will only deploy files with .pbix ending. The rest will be ignored. |
| separator | `string` | `false` | `","` | Character which separates file names. |
| tenant_id | `string` | `true` | | Your tenant id. |
| config_file | `string` | `true` | | The location of your config file |
| source_stage_order | `int` | `true` | | Which stage to deploy from. 0 to deploy dev to test. 1 to deploy test to prod  |
| update_app_in_target_workspace | `boolean` | `false` | `false` | True to update app in target workspace after deploy. |
| allow_purge_data | `boolean` | `false` | `false` | Whether to delete all data from the target Power BI item (such as a report or a dashboard) when there's a schema mismatch. If this option isn't set to true when it's required for deployment, the deployment will fail. |
| deploy_related_datasets | `boolean` | `false` | `false` | If true, will also try to deploy the dataset in the same workspace with the same name as the report |
