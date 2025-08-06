import orjson
import tiktoken


encoding = tiktoken.encoding_for_model("gpt-4o")

def json_to_prompt(data: dict):
    # print(data.keys())
    output = ""
    # output += "Tags(Which machine can deal with this tag):"
    # for tag in data['tags']:
    #     output += f"\n{tag}:"
    #     for machine in data['tags'][tag]:
    #         output += f" {machine}"
    output += "\nMachines(The information about machine):"
    for machine in data['machines']:
        output += f"\n{machine["id"]}:"
        output += f" id {machine['id']} max {machine['max']}"
        output += "\n\ttags:"
        for tag in machine['tags']:
            output += f" {tag}"
        output += "\n\troad:"
        for road in machine['on_road']:
            output += f" {road}"
        output += "\n\twork:"
        for work in machine['on_work']:
            output += f" {work}"
        output += "\n\twait:"
        for wait in machine['on_wait']:
            output += f" {wait}"

    output += "\nShelves(The information about shelf):"
    for shelf in data['shelves']:
        output += f"\n{shelf["id"]}:"
        output += f" id {shelf['id']} max {shelf['max']}"
        output += "\n\troad:"
        for road_id in range(len(shelf["on_road"])):
            if road_id > 5: break
            output += f" {shelf['on_road'][road_id]}"
        output += "\n\twait:"
        for wait_id in range(len(shelf["on_wait"])):
            if wait_id > 5: break
            output += f" {shelf['on_wait'][wait_id]}"

    output += "\nCarriers(The information about carrier):"
    for carrier in data['carriers']:
        output += f"\n{carrier["id"]}:"
        for key in carrier:
    # 输出搬运车信息
            if key == "workflow": continue
            output += f" {key} {carrier[key]}"
        output += f"\n\tworkflow:"
        for workflow in carrier['workflow']:
            output += f" {workflow[0]} {workflow[1]}"
    # output += "\nDistance(The distance between two points):"
    # for distance in data['distance']:
    #     # road = eval(distance)
    #     output += f"\n{distance[0]} {distance[1]} {data['distance'][distance]}"
    # # 输出两点之间的距离
    # print(len(encoding.encode(output)))
    return output