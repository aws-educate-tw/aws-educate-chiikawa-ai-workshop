# CloudFormation Usage Guide

I currently used CloudFormation to provision the resources we will utilize in workshop.

We will first create a template in **Infrastructure Composer**, and the template would be stored in a S3 bucket. Then, continue to **Create stack** section and following steps could be done here.

## Steps in Infrastructure Composer

Head into "Infrastructure Composer" page, then:

1. Toggle to "Template" view
2. Paste the content of YAML file (`template.yaml`)
3. Click "Validate" to verify everything is good.
4. Then, click "Create Template".
5. Ideally, a S3 bucket URL will be generated automatically, and the popup window will help direct to "Create Stack" section.

## Steps in Stacks

1. Create Stack: Ideally, "**Build from Infrastructure Composer**" is chosen by default and the "**S3 URL**" is also filled automatically.
2. Specify stack details: Provide a stack name and parameters defined in template.
3. Configure stack options: I follow default options now.
4. Review and create: Verifying everything is fulfilled the requirements.

After reviewing, click "Submit" and wait for the resources created in 3~5 minutes.