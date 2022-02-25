# Power-BI-Pipeline-Deploy

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
