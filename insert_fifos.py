#!/usr/bin/env python3

import pathlib
import sys


def gen_fifo(stage_name: str, subpipe_name: str, depth: int, end_action: str) -> str:
    assert depth >= 1
    resources = [f"{stage_name}_Shifter_{i}" for i in range(depth)]
    resources_instance = "Resource {\n"
    for i in range(depth - 1):
        resources_instance += f"  {resources[i]},\n"
    resources_instance += f"  {resources[depth-1]}\n}}\n\n"

    microactions_instance = "Microaction {\n"
    microactions = []
    for i in range(depth):
        microaction = f"uA_{stage_name}_Shift_{i}"
        microactions.append(microaction)
        microactions_instance += (
            f"  {microaction} ({resources[i]}){"," if i < depth - 1 else ""}\n"
        )
    microactions_instance += "}\n\n"

    fifo_stages = "Stage {\n"
    for i in range(depth - 1):
        fifo_stages += f"  {subpipe_name}_r{i} ({microactions[i]}),\n"
    fifo_stages += f"  {subpipe_name}_r{depth - 1} ({end_action})\n"
    fifo_stages += "}\n\n"

    fifo_subpipe = f"Pipeline {subpipe_name} (\n"
    for i in range(depth):
        fifo_subpipe += f"  {subpipe_name}_r{i}{" ->" if i < depth - 1 else ""}\n"
    fifo_subpipe += ")\n\n"

    containing_stage = (
        f"Stage {{{stage_name} [capacity: {depth}] ({subpipe_name})}}\n\n"
    )
    # print(fifo_stages)
    # print(fifo_subpipe)
    # print(containing_stage)
    return (
        resources_instance
        + microactions_instance
        + fifo_stages
        + fifo_subpipe
        + containing_stage
    )


def gen_shifts(fifo_name: str, fifo_dict: dict, end: bool) -> str:
    depth = fifo_dict[fifo_name][0]
    end_action = fifo_dict[fifo_name][1]
    shifts = ""
    for i in range(depth - 1):
        shifts += f"    uA_{fifo_name}_Shift_{i},\n"
    shifts += f"    {end_action}{",\n" if not end else "\n}\n\n"}"
    return shifts


def main(infile_path: pathlib.Path, outfile_path: pathlib.Path):
    with open(infile_path, "r", encoding="utf-8") as infile, open(
        outfile_path, "w", encoding="utf-8"
    ) as outfile:

        fifo_dict: dict[str, tuple[int, str]] = {}
        for line in infile:
            if "@FIFO" in line and "@SHIFT" in line:
                print("Error both fifo and shift in same line")
                exit(1)
            # Format @FIFO <DEPTH> <STAGE_NAME> <SUBPIPE_NAME> [<END_ACTION>]
            if "@FIFO" in line:
                split_line = line.strip().split(" ")
                depth = int(split_line[1])
                stage_name = split_line[2]
                subpipe_name = split_line[3]
                end_action = (
                    f"uA_{stage_name}_Shift_{depth-1}"
                    if len(split_line) < 5
                    else split_line[4]
                )
                fifo_description = gen_fifo(stage_name, subpipe_name, depth, end_action)
                fifo_dict[stage_name] = (depth, end_action)
                outfile.write(fifo_description)
            # Format @SHIFT <STAGE_NAME> [end]
            elif "@SHIFT" in line:
                split_line = line.strip().split(" ")
                fifo_name = split_line[1]
                end = False
                if len(split_line) > 2 and split_line[2] == "end":
                    end = True
                fifo_shifts = gen_shifts(fifo_name, fifo_dict, end)
                outfile.write(fifo_shifts)
            else:
                outfile.write(line)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("insert_fifos.py <infile_path> <outfile_path>")

    infile_path = pathlib.Path(sys.argv[1]).resolve()
    outfile_path = pathlib.Path(sys.argv[2]).resolve()
    main(infile_path, outfile_path)
