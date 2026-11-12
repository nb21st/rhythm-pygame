def read_data(filename):
    result = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if line == "":
                continue

            key, val = line.split("=")
            result[key] = val
    return result

def write_data(filename, changes):
    previous_data = read_data(filename)
    for key, val in changes.items():
        previous_data[key] = val
    with open(filename, "w") as f:
        for key, val in previous_data.items():
            f.write(f"{key}={val}\n")
