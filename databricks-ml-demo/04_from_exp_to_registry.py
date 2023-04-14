# Databricks notebook source
# MAGIC %md
# MAGIC ### How to Use the Model Registry
# MAGIC Typically, data scientists who use MLflow will conduct many experiments, each with a number of runs that track and log metrics and parameters. During the course of this development cycle, they will select the best run within an experiment and register its model with the registry.  Think of this as **committing** the model to the registry, much as you would commit code to a version control system.  
# MAGIC 
# MAGIC The registry defines several model stages: `None`, `Staging`, `Production`, and `Archived`. Each stage has a unique meaning. For example, `Staging` is meant for model testing, while `Production` is for models that have completed the testing or review processes and have been deployed to applications. 
# MAGIC 
# MAGIC Users with appropriate permissions can transition models between stages.

# COMMAND ----------

# MAGIC %run ./commons

# COMMAND ----------

# MAGIC %md
# MAGIC #### Promote to Registry
# MAGIC ```
# MAGIC model_name = "Example"
# MAGIC 
# MAGIC model_uri = f"runs:/{ mlflow_run.info.run_id }/model"
# MAGIC registered_model_version = mlflow.register_model(model_uri, model_name)
# MAGIC ```

# COMMAND ----------

import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()

run_id = 'db19dd046eda4677bb0ffe24e1673e3f' # replace with your own run ID, etc
model_name = f"{database_name}_churn"
model_uri = f"runs:/{run_id}/model"

# COMMAND ----------

client.set_tag(run_id, key='db_table', value=f'{database_name}.churn_features')
client.set_tag(run_id, key='demographic_vars', value='seniorCitizen,gender_Female')

model_details = mlflow.register_model(model_uri, model_name)

# COMMAND ----------

# MAGIC %md
# MAGIC At this point the model will be in `None` stage.  Let's update the description before moving it to `Staging`.

# COMMAND ----------

# MAGIC %md
# MAGIC #### Update Description

# COMMAND ----------

from mlflow.tracking.client import MlflowClient

client = MlflowClient()
model_version_details = client.get_model_version(name=model_name, version=model_details.version)

client.update_registered_model(
  name=model_details.name,
  description="This model predicts whether a customer will churn using features from the ibm_telco_churn database.  It is used to update the Telco Churn Dashboard in SQL Analytics."
)

client.update_model_version(
  name=model_details.name,
  version=model_details.version,
  description="This model version was built using sklearn's Logistic Regression."
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Request Transition to Staging
# MAGIC 
# MAGIC <img src="https://github.com/dnguyenv/duyhard-ml4fun/blob/master/databricks-ml-roles/webhooks2.png?raw=true" width = 800>

# COMMAND ----------

# Helper functions
import mlflow
from mlflow.utils.rest_utils import http_request
import json

def client():
  return mlflow.tracking.client.MlflowClient()

host_creds = client()._tracking_client.store.get_host_creds()
host = host_creds.host
token = host_creds.token

def mlflow_call_endpoint(endpoint, method, body='{}'):
  if method == 'GET':
      response = http_request(
          host_creds=host_creds, endpoint="/api/2.0/mlflow/{}".format(endpoint), method=method, params=json.loads(body))
  else:
      response = http_request(
          host_creds=host_creds, endpoint="/api/2.0/mlflow/{}".format(endpoint), method=method, json=json.loads(body))
  return response.json()

# COMMAND ----------

# Transition request to staging
staging_request = {'name': model_name,
                   'version': model_details.version,
                   'stage': 'Staging',
                   'archive_existing_versions': 'true'}

mlflow_call_endpoint('transition-requests/create', 'POST', json.dumps(staging_request))

# COMMAND ----------

# Transition request to prod
prod_request = {'name': model_name,
                   'version': model_details.version,
                   'stage': 'Production',
                   'archive_existing_versions': 'true'}

mlflow_call_endpoint('transition-requests/create', 'POST', json.dumps(prod_request))

# COMMAND ----------

# Leave a comment for the ML engineer who will be reviewing the tests
comment = "Ready for Prod, good job!"
comment_body = {'name': model_name, 'version': model_details.version, 'comment': comment}
mlflow_call_endpoint('comments/create', 'POST', json.dumps(comment_body))

# COMMAND ----------


