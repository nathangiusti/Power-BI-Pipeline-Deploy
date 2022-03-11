# Power-BI-Pipeline-Deploy
Deploys a PBIX file via a pipeline to the prod workspace

Requires a workflow config file in .github/config/deploy_config.yaml

Sample deploy config:

    My_Workspace:
      pipeline_id: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    My_other_workspace:
      pipeline_id:  'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

PBIX file should be placed in a folder which corresponds to the key in the deploy config file. 

For the sample config there would be two folders with PBIX files, My_Workspace and My_other_workspace.

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

Following is the sample action.yaml file needed to configure the action itself

name: 'Power BI Pipeline Deploy'
description: 'Deploy Thin PBIX file to through pipeline'
author: 'Nathan Giusti & Ravi Yerramilli'
inputs:
  files:
    description: 'Files to deploy'
    required: true
  seperator:
    description: 'seperates files names/paths'
    required: true
    default: ","
  tenant_id:
    description: 'tenant id'
    required : false
  source-stage-order:
    description: 'defines the staging order'
    required: true
    defualt: 1
  update-app-in-targetWorkspace:
    desription: 'sets the boolean value'
    required: true
    default: True 
  allow-purgeData:
    description: 'Should not be needed because this is for reports but fail safe'
    required: true
    default: False
    
runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.files }}
    - ${{ inputs.seperator }}
    - ${{ inputs.tenant_id}}
    - ${{ inputs.source-stage-order}}
    - ${{ inputs.update-app-in-targetWorkspace}}
    - ${{ inputs.allow-purgeData}}
  
  

Current todo
- Create composite action
