import tiktoken
from collections import defaultdict


encoding = tiktoken.encoding_for_model("gpt-4o")

statue_map = {
    1: "WAIT",
    0: "WORK",
    -1: "FINISH"
}

def json_to_prompt(data: dict):
    # 距离信息 [ (x, y) dist ]
    output = "Distance(The distance between two points):\n\t"
    output += "\t\n".join(
        f"{point1} {point2} {dist}"
        for (point1, point2), dist in data['distance'].items()
    ) + "\n"
    
    # 机器信息 [ { id, tags, on_wait, on_work, on_road } ]
    output += "Machines(The information about machine):\n"
    for machine in data['machines']:
        used = len(machine['on_work']) + len(machine['on_wait']) + len(machine['on_road'])
        output += f"{machine["id"]}: id {machine['id']} max {machine['max']} free {machine['max'] - used}\n"
        output += "\tSteps: " + " ".join(machine['tags']) + '\n'
        output += "\twait: " + " ".join(machine['on_wait']) + '\n'
        # output += "\twork:" + " ".join(machine['on_work']) + '\n'
        # output += "\troad:" + " ".join(machine['on_road']) + '\n'
    
    ban_carriers = []
    output += "Shelves(The information about shelf):\n"
    for shelf in data['shelves']:
        output += f"{shelf["id"]}: id {shelf['id']} max {shelf['max']}\n\twait:"
        if shelf["id"] == "Input":
            for i, carrier_id in enumerate(shelf["on_wait"]):
                if i > 5:
                    ban_carriers.append(carrier_id)
                else:
                    output += f" {carrier_id}"
        elif shelf["id"] == "Output":
            ban_carriers.extend(shelf["on_wait"])
        else:
            for carrier_id in shelf["on_wait"]:
                output += f" {carrier_id}"
        # output += "\n\troad: " + " ".join(shelf["on_road"])
        output += "\n"
                
    output += "Carriers(The information about carrier):\n"
    for carrier in data['carriers']:
        if carrier["id"] in ban_carriers: 
            continue
        output += f"{carrier["id"]}: id {carrier['id']} status {statue_map[carrier['status']]} at {carrier['at']}"
        if carrier["current"] != len(carrier["workflow"]):
            output += f" cur_workflow {carrier["workflow"][carrier['current']][0]}"
        else:
            output += " cur_workflow Output"
        output += "\n\tworkflow: " + ' '.join(map(lambda w: f"{w[0]} {w[1]}", carrier['workflow'])) + "\n"
    
    # tag信息（worksteps信息）
    tags = defaultdict(list)
    for machine in data['machines']:
        for tag in machine['tags']:
            tags[tag].append(machine['id'])
    output += "Steps(Which machine can deal with this steps):\n"
    for tag in tags.keys():
        output += "\t" + tag + ": " + " ".join(tags[tag]) + "\n"
    return output