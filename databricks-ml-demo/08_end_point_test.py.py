# Databricks notebook source
dbutils.widgets.text("model_name", "kyber_db_ml_churn")
model_name = dbutils.widgets.get("model_name")

# COMMAND ----------

import os
import requests
import numpy as np
import pandas as pd
import json

def create_tf_serving_json(data):
    return {'inputs': {name: data[name].tolist() for name in data.keys()} if isinstance(data, dict) else data.tolist()}

def score_model(dataset):
    url = 'https://disney-cpdl-sbx.cloud.databricks.com/serving-endpoints/kyber-db-ml-test1/invocations'
    headers = {'Authorization': f'Bearer dapiaf490edeb40aa338776d78d9efce39d4', 'Content-Type': 'application/json'}
    ds_dict = {'dataframe_split': dataset.to_dict(orient='split')} if isinstance(dataset, pd.DataFrame) else create_tf_serving_json(dataset)
    data_json = json.dumps(ds_dict, allow_nan=True)
    response = requests.request(method='POST', headers=headers, url=url, data=data_json)
    if response.status_code != 200:
        raise Exception(f'Request failed with status {response.status_code}, {response.text}')

    return response.json()

# COMMAND ----------

import mlflow
path = mlflow.artifacts.download_artifacts(f'models:/{model_name}/7')
model = mlflow.pyfunc.load_model(f'models:/{model_name}/7')
input_example = model.metadata.load_input_example(path)

# COMMAND ----------

input_example

# COMMAND ----------

score_model(input_example)

# COMMAND ----------


