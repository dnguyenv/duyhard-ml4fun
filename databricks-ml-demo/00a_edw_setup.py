# Databricks notebook source
# MAGIC %md
# MAGIC # Set things up

# COMMAND ----------

# MAGIC %sh
# MAGIC wget https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv

# COMMAND ----------

# Set config for database name, file paths, and table names
database_name = 'kyber_db_ml'
#spark.sql(f"USE CATALOG kyber_sbx")
spark.sql(f"DROP DATABASE IF EXISTS {database_name} CASCADE;")
spark.sql(f"CREATE DATABASE {database_name} COMMENT 'This database is used to maintain Inventory';")
spark.sql(f"USE {database_name}")

# COMMAND ----------

# Load libraries
import shutil
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from pyspark.sql.functions import col, when
from pyspark.sql.types import StructType,StructField,DoubleType, StringType, IntegerType, FloatType

# Move file from driver to DBFS
user = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().apply('user')
driver_to_dbfs_path = 'dbfs:/home/{}/ibm-telco-churn/Telco-Customer-Churn.csv'.format(user)
dbutils.fs.cp('file:/Workspace/Repos/duy.nguyen@disney.com/duyhard-ml4fun/databricks-ml-demo/Telco-Customer-Churn.csv', driver_to_dbfs_path)

# Paths for various Delta tables
bronze_tbl_path = '/home/{}/ibm-telco-churn/bronze/'.format(user)
silver_tbl_path = '/home/{}/ibm-telco-churn/silver/'.format(user)
automl_tbl_path = '/home/{}/ibm-telco-churn/automl-silver/'.format(user)
telco_preds_path = '/home/{}/ibm-telco-churn/preds/'.format(user)

bronze_tbl_name = 'bronze_customers'
silver_tbl_name = 'silver_customers'
automl_tbl_name = 'gold_customers'
telco_preds_tbl_name = 'telco_preds'

# # Delete the old database and tables if needed
# _ = spark.sql('DROP DATABASE IF EXISTS {} CASCADE'.format(database_name))

# # Create database to house tables
# _ = spark.sql('CREATE DATABASE {}'.format(database_name))
# Drop any old delta lake files if needed (e.g. re-running this notebook with the same bronze_tbl_path and silver_tbl_path)

shutil.rmtree('/dbfs'+bronze_tbl_path, ignore_errors=True)
shutil.rmtree('/dbfs'+silver_tbl_path, ignore_errors=True)
shutil.rmtree('/dbfs'+telco_preds_path, ignore_errors=True)

# COMMAND ----------

# MAGIC %md
# MAGIC # Read Data

# COMMAND ----------

df = (spark.read
      .option("header", "true")
      .option("delimiter", ",")
      .option("inferSchema", "true")
      .csv("/home/duy.nguyen@disney.com/ibm-telco-churn/Telco-Customer-Churn.csv")
     )
      

# COMMAND ----------

display(df)

# COMMAND ----------


