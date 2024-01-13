
from invoke import task
import shutil

@task(optional=['deps'])
def package(c, deps=False):
  # Packages the source code
  shutil.make_archive("infra/files/artifacts/lambda_package", "zip", "../bubamara-backend", "bubamara_backend")
  
  if deps:
    # Export dependencies as requirements.txt
    c.run("pipenv requirements --hash > requirements.txt")
    
    # Install dependencies in target directory
    c.run("pipenv run pip install -r requirements.txt -t opt/python/lib/python3.9/site-packages --force-reinstall")
    
    # Create archive file
    shutil.make_archive("infra/files/artifacts/lambda_layer", "zip", "opt", "python")

    # Removes dependencies target directory
    c.run("rm -rf opt/python/lib/python3.9/site-packages")


@task
def deploy(c):
  c.run("cd infra/ && terraform init && terraform apply --auto-approve")
