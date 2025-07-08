import yaml

def extract_code_leafs(data):
    leafs = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'codes':
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'code' in item:
                            leafs.append(item['code'])
                        elif isinstance(item, str):
                            leafs.append(item)
            else:
                leafs.extend(extract_code_leafs(value))

    elif isinstance(data, list):
        for item in data:
            leafs.extend(extract_code_leafs(item))

    return leafs

# Load YAML from file
with open('./CP/ecs.yaml', 'r') as f:
    yaml_data = yaml.safe_load(f)

# Extract and print all code leafs
all_codes = extract_code_leafs(yaml_data)
for code in all_codes:
    print(code)
