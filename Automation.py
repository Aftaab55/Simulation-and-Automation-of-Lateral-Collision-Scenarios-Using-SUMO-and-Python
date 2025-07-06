import os
import pandas as pd
import xml.etree.ElementTree as ET
import subprocess
import shutil
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed

def extract_data_from_csv(csv_file):
    """Extract relevant data from the CSV file for all IDs."""
    data = {}
    try:
        df = pd.read_csv(csv_file)
        required_columns = ["ID", "Attributes", "Start Value", "End Value", "Steplength", "Number of Simulations"]
        if not all(col in df.columns for col in required_columns):
            print(f"Error: CSV must contain columns: {', '.join(required_columns)}.")
            return data

        for _, row in df.iterrows():
            sim_id = row["ID"]
            param = row["Attributes"].strip()
            start_value = row.get("Start Value")
            end_value = row.get("End Value")
            step_length = row.get("Steplength")
            num_simulations = row.get("Number of Simulations")

            if pd.notna(start_value) and pd.notna(end_value) and pd.notna(step_length) and pd.notna(num_simulations):
                if sim_id not in data:
                    data[sim_id] = {}
                data[sim_id][param] = {
                    "start": float(start_value),
                    "end": float(end_value),
                    "step": float(step_length),
                    "num_simulations": int(num_simulations)
                }
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
    except Exception as e:
        print(f"An error occurred while processing the CSV file: {e}")
    return data

def frange(start, stop, step):
    """Generate a range of float values for increasing or decreasing ranges, including the end value."""
    if step == 0:
        raise ValueError("Step size cannot be zero.")
    
    if start < stop:
        current = start
        while current <= stop + 1e-10:
            yield round(current, 2)
            current += step
    else:
        current = start
        while current >= stop - 1e-10:
            yield round(current, 2)
            current -= step

def generate_route_files(input_file, output_dir, csv_data):
    """Generate route files by modifying each ID's parameters while keeping others constant."""
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return

    os.makedirs(output_dir, exist_ok=True)
    original_tree = ET.parse(input_file)
    original_root = original_tree.getroot()

    original_values = {}
    for vtype in original_root.findall("vType"):
        original_values[vtype.get("id")] = vtype.attrib.copy()

    for sim_id, params in csv_data.items():
        param_values = {}
        for param_name, values in params.items():
            start, end, step = values["start"], values["end"], values["step"]
            param_values[param_name] = list(frange(start, end, step))

        param_names = list(param_values.keys())
        combined_values = list(product(*param_values.values()))

        for values in combined_values:
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            for param_name, value in zip(param_names, values):
                for vtype in root.findall("vType"):
                    if vtype.get("id") == str(sim_id) and param_name in vtype.attrib:
                        vtype.set(param_name, str(value))

            combination_str = "_".join(f"{param}{value}" for param, value in zip(param_names, values))
            output_file = os.path.join(output_dir, f"route_{sim_id}_{combination_str}.rou.xml")
            try:
                tree.write(output_file, encoding="UTF-8", xml_declaration=True)
                print(f"Generated: {output_file}")
            except Exception as e:
                print(f"Error writing file {output_file}: {e}")

def filter_collision_files(output_collisions_dir, filtered_collisions_dir):
    """Filter collision files for those containing victim='v_0'."""
    if not os.path.exists(output_collisions_dir):
        print(f"Error: Collisions directory '{output_collisions_dir}' does not exist.")
        return

    os.makedirs(filtered_collisions_dir, exist_ok=True)
    collision_files = [f for f in os.listdir(output_collisions_dir) if f.endswith(".xml")]

    for file_name in collision_files:
        file_path = os.path.join(output_collisions_dir, file_name)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            save_file = any(collision.get("victim") == "v_0" for collision in root.findall("collision"))
            
            if save_file:
                target_path = os.path.join(filtered_collisions_dir, file_name)
                shutil.copy(file_path, target_path)
                print(f"Filtered file saved: {target_path}")
        except ET.ParseError:
            print(f"Error parsing XML file: {file_name}")
        except Exception as e:
            print(f"Error processing file {file_name}: {e}")

def run_simulation(config_file):
    """Run a single SUMO simulation."""
    try:
        result = subprocess.run(["sumo", "-c", config_file], check=True, capture_output=True, text=True)
        print(f"Simulation completed for {config_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during simulation for {config_file}: {e}")
        print(f"SUMO Error Output: {e.stderr}")
    except Exception as e:
        print(f"Unexpected error during simulation: {e}")

def main():
    
    base_dir = r"C:\Users\aftaa\OneDrive\Desktop\Polito Mechanical\Thesis\Simulations\Automatisation\4"
    input_csv_file = os.path.join(base_dir, "Parameters_to_change - Copy.csv")
    input_xml_file = os.path.join(base_dir, "Rou04.rou.xml")
    config_file = os.path.join(base_dir, "town04.sumocfg")
    net_file_path = os.path.join(base_dir, "Town04.net.xml")  
    
    # Output directories
    output_dir = os.path.join(base_dir, "Output_new")
    os.makedirs(output_dir, exist_ok=True)
    
    route_files_dir = os.path.join(output_dir, "Route_files")
    output_collisions_dir = os.path.join(output_dir, "Collisions")
    output_statistics_dir = os.path.join(output_dir, "Statistics")
    output_tripinfo_dir = os.path.join(output_dir, "Tripinfo")
    output_lanechange_dir = os.path.join(output_dir, "lanechange")
    filtered_collisions_dir = os.path.join(output_dir, "Filtered_Collisions")
    temp_config_dir = os.path.join(base_dir, "temp_configs")
    
    for directory in [route_files_dir, output_collisions_dir, output_statistics_dir, 
                     output_tripinfo_dir, output_lanechange_dir, filtered_collisions_dir, 
                     temp_config_dir]:
        os.makedirs(directory, exist_ok=True)

    print("Extracting data from CSV...")
    csv_data = extract_data_from_csv(input_csv_file)
    if not csv_data:
        print("No valid ranges found in CSV. Exiting.")
        return

    print("Generating route files...")
    generate_route_files(input_xml_file, route_files_dir, csv_data)
    print("Route file generation completed.")

    route_files = [f for f in os.listdir(route_files_dir) if f.endswith(".xml")]

    try:
        tree = ET.parse(config_file)
        root = tree.getroot()
    except ET.ParseError:
        print(f"Error parsing configuration file: {config_file}")
        return
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        return

    input_tag = root.find("input")
    if input_tag is None:
        input_tag = ET.SubElement(root, "input")
    
    output_tag = root.find("output")
    if output_tag is None:
        output_tag = ET.SubElement(root, "output")

    config_files = []
    for route_file in route_files:
        route_file_path = os.path.join(route_files_dir, route_file)
        base_name = os.path.splitext(route_file)[0]
        
        route_files_elem = input_tag.find("route-files")
        if route_files_elem is None:
            route_files_elem = ET.SubElement(input_tag, "route-files")
        route_files_elem.set("value", route_file_path)
        
        net_file_elem = input_tag.find("net-file")
        if net_file_elem is None:
            net_file_elem = ET.SubElement(input_tag, "net-file")
        net_file_elem.set("value", net_file_path)

        output_paths = {
            "collision-output": os.path.join(output_collisions_dir, f"collisions_{base_name}.xml"),
            "statistic-output": os.path.join(output_statistics_dir, f"statistics_{base_name}.xml"),
            "tripinfo-output": os.path.join(output_tripinfo_dir, f"tripinfo_{base_name}.xml"),
            "lanechange-output": os.path.join(output_lanechange_dir, f"lanechange_{base_name}.xml")
        }
        
        for output_type, output_path in output_paths.items():
            elem = output_tag.find(output_type)
            if elem is None:
                elem = ET.SubElement(output_tag, output_type)
            elem.set("value", output_path)

        updated_config_file = os.path.join(temp_config_dir, f"temp_config_{base_name}.sumocfg")
        tree.write(updated_config_file, encoding="UTF-8", xml_declaration=True)
        config_files.append(updated_config_file)

    print("Running simulations in parallel...")
    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(run_simulation, config_file) for config_file in config_files]
        for future in as_completed(futures):
            future.result()  

    try:
        shutil.rmtree(temp_config_dir)
    except Exception as e:
        print(f"Error cleaning up temporary files: {e}")

    print("\nFiltering collision files...")
    filter_collision_files(output_collisions_dir, filtered_collisions_dir)

    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()