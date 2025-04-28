from git import Repo
import os

# Config parameters
repo_url = "https://dev.azure.com/xuzhenyang85/APIM/_git/Repo1"

# Replace your repo's URL
clone_path = "temp_repo" # temp folder

# Clone operation
if not os.pah.exists(clone_path):
    Repo.clone_from(repo_url, clone_path)
    print(f"Repo has ben cloned to: {clone_path}")
else:
    print("Folder already exists, skipped clone operation")