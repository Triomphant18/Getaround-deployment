docker run -it\
 -p 8000:8000\
 -v "$(pwd):/home/app"\
 -e PORT=8000\
 -e APP_URI=$APP_URI\
 -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID\
 -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY\
 -e BACKEND_STORE_URI=$BACKEND_STORE_URI\
 -e ARTIFACT_ROOT=$ARTIFACT_ROOT\
 mlflow-get-around jupyter-notebook --allow-root --ip=0.0.0.0 --port=8000 --no-browser