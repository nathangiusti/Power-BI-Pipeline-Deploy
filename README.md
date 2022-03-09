# Power-BI-Pipeline-Deploy
Deploys a PBIX file via a pipeline to the prod workspace

Requires a config in .github/config/deploy_config.yaml

Sample deploy config:

    My_Workspace:
      pipeline_id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    My_other_workspace:
      pipeline_id:  'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

PBIX file should be placed in a folder which corresponds to the key in the deploy config file. 

For the sample config there would be two folders with PBIX files, My_Workspace and My_other_workspace.

Sample use

    name: Migrate to prod
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
          - name: Power BI Pipeline Deploy
            uses: nathangiusti/Power-BI-Pipeline-Deploy@v2.1
            with:
              files: ${{ steps.changed-files.outputs.all_modified_files }}
            env:
              CLIENT_ID: ${{ secrets.NON_PROD_SPN_ID }}
              CLIENT_SECRET: ${{ secrets.NON_PROD_SPN_SECRET }}


  

Current todo
- Create composite action
