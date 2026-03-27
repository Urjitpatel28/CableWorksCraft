import json

def load_json_as_dict(json_file):
    """
    Loads a JSON file and returns its contents as a dictionary.
    """
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data

def layercount(variables_dict,keys):
    #Counts the number of variables in the dictionary that are numeric and not equal to zero.
    count = 0
    for key in keys:
        value = variables_dict.get(key)
        if isinstance(value, (int, float)) and value != 0:
            count += 1
    return count

def get_non_zero_count(json_path, keys):
    variables = load_json_as_dict(json_path)
    nested_vars = variables.get("parameters", {})
    return layercount(nested_vars, keys)

if __name__ == "__main__":
    variables = load_json_as_dict("C:\\ProjectRoot\\ftest_2\\Outputs\\projectDetail.json")
    nested_vars = variables.get("parameters", {})

    # Print all keys and values
    print("Loaded variables:")
    for key, value in nested_vars.items():
        print(f"{key} = {value}")
    
    keys_to_check = ["preinnersheaththickness", "outersheaththickness","innersheaththickness","overinnersheaththickness","armortapingthickness","cylinder_radius","side_thickness"]
    non_zero_count = layercount(nested_vars,keys_to_check)
    print(f"Number of variables not equal to zero: {non_zero_count}")
 