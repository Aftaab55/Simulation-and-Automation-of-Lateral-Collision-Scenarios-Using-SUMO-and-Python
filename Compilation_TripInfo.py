import os
import xml.etree.ElementTree as ET
import pandas as pd
import logging
import re

# Set up logging
logging.basicConfig(filename='xml_processing.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Hardcoded input and output paths
xml_folder = r"C:\Users\aftaa\OneDrive\Desktop\Polito Mechanical\Thesis\Simulations\Automatisation\4\Output_new\Tripinfo"
output_file = r"C:\Users\aftaa\OneDrive\Desktop\Polito Mechanical\Thesis\Simulations\Automatisation\4\Output_new\Tripinfo\Compiled.xlsx"

# Ensure the output file has a valid extension (e.g., .xlsx)
if not output_file.lower().endswith('.xlsx'):
    output_file += '.xlsx'  # Append .xlsx if missing

# Initialize a list to store the extracted rows
combined_data = []

# Flag to check if the header has been added
header_added = False

# Function to extract parameters from the file name
def extract_parameters_from_filename(filename):
    """Extract routeID, lcSigma, tau, actionStepLength, and minGapLat from the file name."""
    params = {}
    try:
        # Refined regex to capture parameter names followed by numeric values (including negative values)
        matches = re.findall(r"(route_|lcSigma|tau|actionStepLength|minGapLat)(-?\d+\.\d+|-?\d+)", filename)
        for key, value in matches:
            # Store the value as-is (no conversion to float)
            params[key] = value
        
        # Log if any required parameter is missing
        required_params = {"route_", "lcSigma", "tau", "actionStepLength", "minGapLat"}
        missing_params = required_params - set(params.keys())
        if missing_params:
            logging.warning(f"Missing parameters in filename {filename}: {missing_params}")
            for param in missing_params:
                params[param] = "N/A"  # Assign default value for missing parameters
    
    except Exception as e:
        logging.error(f"Error extracting parameters from filename {filename}: {e}")
        # Assign default values if extraction fails
        params = {
            "route_": "N/A",
            "lcSigma": "N/A",
            "tau": "N/A",
            "actionStepLength": "N/A",
            "minGapLat": "N/A"
        }
    
    return params

# Iterate over all XML files in the folder
for xml_file in os.listdir(xml_folder):
    if xml_file.endswith(".xml"):
        xml_path = os.path.join(xml_folder, xml_file)
        
        try:
            # Parse the XML file
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract the first row (header) - from the first child element
            if not header_added and len(root) > 0:
                header_row = list(root[0].attrib.keys())
                # Add headers for the additional columns
                combined_data.append(["File", "route_", "lcSigma", "tau", "actionStepLength", "minGapLat"] + header_row)
                header_added = True
            
            # Extract the row with id="v_0"
            v_0_row = None
            for child in root:
                if child.attrib.get("id") == "v_0":
                    v_0_row = list(child.attrib.values())
                    break
            
            # If the row with id="v_0" exists, add it to the combined data
            if v_0_row:
                # Extract parameters from the file name
                params = extract_parameters_from_filename(xml_file)
                
                # Debugging: Log the extracted parameters
                logging.info(f"Extracted parameters from {xml_file}: {params}")
                
                # Add the file name and parameters to the row
                combined_data.append([
                    xml_file, 
                    params.get("route_", "N/A"),  # Fixed to use "route_" instead of "route"
                    params.get("lcSigma", "N/A"), 
                    params.get("tau", "N/A"), 
                    params.get("actionStepLength", "N/A"), 
                    params.get("minGapLat", "N/A")
                ] + v_0_row)
        
        except ET.ParseError as e:
            logging.error(f"Error parsing file {xml_file}: {e}")
            continue  # Skip to the next file
        except Exception as e:
            logging.error(f"Unexpected error processing file {xml_file}: {e}")
            continue

# Save combined data to an Excel file
if combined_data:
    try:
        # Create a DataFrame
        df = pd.DataFrame(combined_data[1:], columns=combined_data[0])

        # Ensure numeric formatting is retained while writing to Excel
        df.to_excel(output_file, index=False)
        print(f"Data successfully combined and saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving data to Excel file: {e}")
        print(f"Error saving data to Excel file: {e}")
else:
    print("No data extracted. Please check your XML files or folder path.")