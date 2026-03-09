import os
import yaml
import json

from collections import OrderedDict

def get_tree(site, category):
    merged_data = {}
    yaml_files = os.listdir(f"/ted-api/pv_tree/channels/{site}/{category}")
    for file_path in yaml_files:
        with open(f"/ted-api/pv_tree/channels/{site}/{category}/{file_path}") as f:
            data = yaml.full_load(f)
            if data:
                merged_data.update(data)
    tree = OrderedDict(sorted(merged_data.items()))
    return tree
    
# def get_system_tree(categroy, system):
#     with open(f"./channels/CP/{category}/{system}.yaml") as f:
#         data = yaml.full_load(f)
#     sorted_merged = OrderedDict(sorted(data.items()))
#     tree = json.dumps(sorted_merged, indent=2)
#     return tree

# def get_category_tree(category):
#     yaml_files = os.listdir(f"./channels/CP/{category}")
#     systems=[]
#     for file in yaml_files:
#         systems.append(file.split(".")[0].upper())
#     tree = json.dumps(systems, indent=2)