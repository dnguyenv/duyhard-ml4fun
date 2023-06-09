# Databricks notebook source
# MAGIC %md
# MAGIC ## AutoML Retrain

# COMMAND ----------

# MAGIC %run ./commons

# COMMAND ----------

# MAGIC %md
# MAGIC #### Load Features

# COMMAND ----------

# MAGIC %md
# MAGIC - [Feature Store Job Schedule](https://docs.databricks.com/applications/machine-learning/feature-store/feature-tables.html#schedule-a-job-to-update-a-feature-table)
# MAGIC - [Azure online feature store](https://docs.microsoft.com/en-ca/azure/databricks/applications/machine-learning/feature-store/concepts#--online-store)
# MAGIC - [Publish to Azure online feature store](https://docs.microsoft.com/en-ca/azure/databricks/applications/machine-learning/feature-store/feature-tables#publish-features-to-an-online-feature-store)

# COMMAND ----------

from databricks.feature_store import FeatureStoreClient

# Set config for database name, file paths, and table names
feature_table = f'{database_name}.churn_features'

fs = FeatureStoreClient()

features = fs.read_table(feature_table)

# COMMAND ----------

dbutils.fs.ls('dbfs:/tmp/duy.nguyen@disney.com/')

# COMMAND ----------

import databricks.automl
model = databricks.automl.classify(features, 
                                   target_col = "churn",
                                   data_dir= f"dbfs:/tmp/{user}/",
                                   timeout_minutes=120,
                                   experiment_name="kyber_db_ml_churn") 

# COMMAND ----------

# MAGIC %md
# MAGIC #### Promote to Registry

# COMMAND ----------

import mlflow
from mlflow.tracking.client import MlflowClient

client = MlflowClient()

run_id = model.best_trial.mlflow_run_id
model_name = f"{database_name}_churn"
model_uri = f"runs:/{run_id}/model"

client.set_tag(run_id, key='db_table', value=f'{database_name}.churn_features')
client.set_tag(run_id, key='demographic_vars', value='seniorCitizen,gender_Female')

model_details = mlflow.register_model(model_uri, model_name)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Add Comments

# COMMAND ----------

model_version_details = client.get_model_version(name=model_name, version=model_details.version)

client.update_registered_model(
  name=model_details.name,
  description="This model predicts whether a customer will churn using features from the ibm_telco_churn database.  It is used to update the Telco Churn Dashboard in SQL Analytics."
)

client.update_model_version(
  name=model_details.name,
  version=model_details.version,
  description="This model version was built using sklearn's LogisticRegression."
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Request Transition to Staging

# COMMAND ----------

# Helper function
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
staging_request = {'name': model_name, 'version': model_details.version, 'stage': 'Staging', 'archive_existing_versions': 'true'}
mlflow_call_endpoint('transition-requests/create', 'POST', json.dumps(staging_request))

# COMMAND ----------

# Leave a comment for the ML engineer who will be reviewing the tests
comment = "This was the best model from AutoML, I think we can use it as a baseline."
comment_body = {'name': model_name, 'version': model_details.version, 'comment': comment}
mlflow_call_endpoint('comments/create', 'POST', json.dumps(comment_body))

# COMMAND ----------


