import os
import xml.etree.ElementTree as ET
import pandas as pd

# Define the folder containing XML files and the output directory
xml_folder = r'C:\Users\aftaa\OneDrive\Desktop\Polito Mechanical\Thesis\Simulations\Automatisation\4\Output_new\Statistics'  # Replace with the path to your folder
output_dir = r'C:\Users\aftaa\OneDrive\Desktop\Polito Mechanical\Thesis\Simulations\Automatisation\4\Output_new\Statistics'  # Replace with your desired output directory

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Define the output file paths
output_file = os.path.join(output_dir, "extracted_data.xlsx")
error_log_file = os.path.join(output_dir, "error_log.txt")

# Initialize a list to store the extracted data
extracted_data = []

# Initialize a list to store errors
errors = []

# Function to extract parameters from the file name
def extract_parameters_from_filename(filename):
    """Extract route ID, lcSigma, tau, actionStepLength, and minGapLat from the file name."""
    params = {}
    try:
        # Split the file name by underscores
        parts = filename.split("_")
        for i, part in enumerate(parts):
            if part == "route" and i + 1 < len(parts):
                # The next part should be the route ID
                params["routeID"] = parts[i + 1]
            elif part.startswith("lcSigma"):
                params["lcSigma"] = part.replace("lcSigma", "")
            elif part.startswith("tau"):
                params["tau"] = part.replace("tau", "")
            elif part.startswith("actionStepLength"):
                params["actionStepLength"] = part.replace("actionStepLength", "")
            elif part.startswith("minGapLat"):
                params["minGapLat"] = part.replace("minGapLat", "")
    except Exception as e:
        errors.append(f"Error extracting parameters from filename {filename}: {e}")
    return params

# Iterate over all XML files in the folder
for xml_file in os.listdir(xml_folder):
    if xml_file.endswith(".xml"):
        xml_path = os.path.join(xml_folder, xml_file)
        
        # Parse the XML file
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Initialize a dictionary to store the extracted values for this file
            file_data = {"File": xml_file}
            
            # Extract total teleports
            teleports_element = root.find("teleports")
            if teleports_element is not None:
                file_data["totalTeleports"] = teleports_element.get("total")
            else:
                file_data["totalTeleports"] = None  # If the element is not found, store None
            
            # Extract emergencyBraking and collisions from the <safety> element
            safety_element = root.find("safety")
            if safety_element is not None:
                file_data["emergencyBraking"] = safety_element.get("emergencyBraking")
                file_data["collisions"] = safety_element.get("collisions")
            else:
                file_data["emergencyBraking"] = None
                file_data["collisions"] = None
            
            # Extract parameters from the file name
            params = extract_parameters_from_filename(xml_file)
            file_data.update(params)  # Add the extracted parameters to the dictionary
            
            # Add the extracted data to the list
            extracted_data.append(file_data)
        except ET.ParseError as e:
            errors.append(f"Error parsing {xml_file}: {e}")
        except Exception as e:
            errors.append(f"Unexpected error processing {xml_file}: {e}")

# Save extracted data to an Excel file
if extracted_data:
    # Create a DataFrame
    df = pd.DataFrame(extracted_data)
    
    # Clean the minGapLat column: Remove text and keep only numerical values
    df['minGapLat'] = df['minGapLat'].str.extract(r'(\d+\.\d+)').astype(float)
    
    # Write to Excel
    df.to_excel(output_file, index=False)
    print(f"Data successfully extracted and saved to {output_file}")
else:
    print("No data extracted. Please check your XML files or folder path.")

# Log errors to a text file
if errors:
    with open(error_log_file, "w") as f:
        for error in errors:
            f.write(error + "\n")
    print(f"Errors logged to {error_log_file}")