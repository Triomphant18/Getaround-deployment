import requests 
import json
import pandas as pd 

### Test groupby endpoint
def test_categories():
    payload = {
        "column": "BusinessTravel", 
        "by_method": "sum"
    }

    r = requests.post(
        "http://localhost:4000/groupby", 
        data= json.dumps(payload)
        )

    response = r.json()
    print(pd.read_json(response))

#test_categories()
### Test filter-by endpoint
def test_filterBy():

    payload = {
        "column": "BusinessTravel",
        "by_category": ["Travel_Rarely", "Non-Travel"]
    }

    r = requests.post(
        "http://localhost:4000/filter-by",
        data = json.dumps(payload)
    )

    response = r.json()
    print(pd.read_json(response))

#test_filterBy()


#### Test ML Model 

def test_prediction():

    df = pd.read_excel("https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/ibm_hr_attrition.xlsx", index_col=0)
    df = df.sample(1)
    values = []
    for element in df.iloc[0,:].values.tolist():
        if type(element) != str:
            values.append(element.item())
        else:
            values.append(element)
    df_dict = {key:value for key, value in zip(df.columns, values)}

    r = requests.post(
        "http://localhost:4000/predict",
        data=json.dumps(df_dict)
    )

    response = r
    print(response)

test_prediction()

#### Test batch pred
def test_batch():
    import csv
    import urllib3

    df = pd.read_csv('https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/ibm_hr_attrition.csv', index_col=0)
    myfile = df.to_csv()
    r = requests.post(
        "http://localhost:4000/batch-predict",
        files={"file":myfile}
    )

    response = r
    print(response)

test_batch()

#### Prepare test data 
def prepare_test_file():

    df = pd.read_excel("https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/ibm_hr_attrition.csv")

    target_col_name= "Attrition"
    df = df.loc[:, df.columns != target_col_name]
    df = df.sample(20)
    df.to_csv("data/test_data.csv", index=False)
    return "Done"