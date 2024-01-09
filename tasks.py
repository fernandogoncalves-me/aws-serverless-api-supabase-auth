
from invoke import task
import shutil

@task
def package(c):
    shutil.make_archive("infra/bubamara_backend", "zip", "bubamara_backend")
