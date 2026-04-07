import os
print("Hello", os.getenv("NAME"))

'''
FOR CHECKING ISOLATION - run build and the run and check if the file is not created using ls /
with open("/outside.txt", "w") as f:
    f.write("HACK")
'''