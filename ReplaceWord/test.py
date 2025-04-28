print("Hello Azure DevOps!") # print texts

# variables and string operations
old_text = "I love COBOL"
new_text = old_text.replace("COBOL", "Python")
print(f"Replace result: {new_text}")

# List current folder's files, similar to command ls/dir
import os
print("Current Folder file:", os.listdir())