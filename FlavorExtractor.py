## This script's purpose is to digest the flavors (and potentially scrape for products/sensors) from two different supported file formats (wxl_dif.dat and txt)
import os, logging, coloredlogs
import DIFDecode
log = logging.getLogger(__name__)
coloredlogs.install("INFO")

def extract_flavors_from_file(file_path:str):
    log.info(f"Extracting flavors from XL DIF: '{file_path}'")
    database = DIFDecode.parse(file_path)
    flavors = {}
    for key, data in database.items():
        if key.startswith("c_flavor_"):
            #flavor_name = key.lstrip("c_flavor_")
            flavor_name = key[len("c_flavor_"):]
            if flavor_name in ["name_prefix", "rule_file_name", "version_name", "SENSORS", "PERM", "TAG"]:
                continue # ignore
            # Potential Init key
            if data.startswith("@Init"):
                log.debug(f"Found Init key for flavor '{flavor_name}'")
                if not flavors.get(flavor_name): flavors[flavor_name] = {} # create a dict object for the flavor if not present
                flavors[flavor_name]["init"] = True
                flavors[flavor_name]["name"] = flavor_name
                #flavor_mods = data.lstrip(f"@Init({flavor_name})") # this will return everything after the init call
                flavor_mods = data[len(f"@Init({flavor_name})"):]
                if flavor_mods != "":
                    log.debug(f"Flavor has modifiers: '{flavor_mods}'")
                    flavors[flavor_name]["modifiers"] = flavor_mods
            # End Init
            else:
                log.warning(f"Flavor key '{key}' ({flavor_name}) exists but is not initialized as a callable flavor.")
                if not flavors.get(flavor_name): flavors[flavor_name] = {} # create a dict object for the flavor if not present
                flavors[flavor_name]["init"] = False
                flavors[flavor_name]["name"] = flavor_name
        if key.startswith("c_"):

            # So, this is a bit annoying, but it's better to just sift through all the config items in order to catch the non-initialized flavors (mainly for modifiers like DH1H2)
            maybe_flavor_name = key.lstrip("c_").split("_")[0]
            if maybe_flavor_name in ["name_prefix", "rule_file_name", "version_name", "SENSORS", "PERM", "TAG"]:
                continue # ignore
            # We're only going to search for:
            # product_num, sensor_num, and misc_num
            # and then once we find counts for each layer, we'll manually search for the definitions
            if "product_num" in key:
                flavor_name = maybe_flavor_name
                log.debug(f"Got product count for flavor '{flavor_name}': {data}")
                if not flavors.get(flavor_name): flavors[flavor_name] = {} # create a dict object for the flavor if not present
                if not flavors[flavor_name].get("name"): flavors[flavor_name]["name"] = flavor_name # set the flavor name for flavors without an Init call
                if not flavors[flavor_name].get("products"): flavors[flavor_name]["products"] = {}
                flavors[flavor_name]["products"]["count"] = int(data)
            if "sensor_num" in key:
                flavor_name = maybe_flavor_name
                log.debug(f"Got sensor count for flavor '{flavor_name}': {data}")
                if not flavors.get(flavor_name): flavors[flavor_name] = {} # create a dict object for the flavor if not present
                if not flavors[flavor_name].get("name"): flavors[flavor_name]["name"] = flavor_name # set the flavor name for flavors without an Init call
                if not flavors[flavor_name].get("sensors"): flavors[flavor_name]["sensors"] = {}
                flavors[flavor_name]["sensors"]["count"] = int(data)
            if "misc_num" in key:
                flavor_name = maybe_flavor_name
                log.debug(f"Got misc count for flavor '{flavor_name}': {data}")
                if not flavors.get(flavor_name): flavors[flavor_name] = {} # create a dict object for the flavor if not present
                if not flavors[flavor_name].get("name"): flavors[flavor_name]["name"] = flavor_name # set the flavor name for flavors without an Init call
                if not flavors[flavor_name].get("misc"): flavors[flavor_name]["misc"] = {}
                flavors[flavor_name]["misc"]["count"] = int(data)
    # Now we'll try to find all the products, sensors, and misc via indexing based on the item counts
    for flavor, conf in flavors.items():
        flavor_name = flavor # whoops
        log.debug(f"Trying to find flavor '{flavor}' via index.")
        # GET ALL PRODUCT INFORMATION
        prod_count = conf.get("products", {}).get("count", 0)
        for i in range(prod_count):
            log.debug(f"Getting name and duration for product {i}...")
            i = f"{i:02}"
            product_header = f"c_{flavor}_product_{i}"
            product_duration_header = f"c_{flavor}_product_duration_{i}"
            product_name = database.get(product_header, None)
            product_duration = database.get(product_duration_header, None)
            product = {
                "name": product_name,
                "duration": product_duration
            }
            if product_name and product_duration:
                if not flavors[flavor_name]["products"].get("order"): flavors[flavor_name]["products"]["order"] = []
                flavors[flavor_name]["products"]["order"].append(product)
        # GET ALL SENSOR INFORMATION
        sens_count = conf.get("sensors", {}).get("count", 0)
        for i in range(sens_count):
            log.debug(f"Getting name and duration for sensor {i}...")
            i = f"{i:02}"
            sensor_header = f"c_{flavor}_sensor_{i}"
            sensor_duration_header = f"c_{flavor}_sensor_duration_{i}"
            sensor_name = database.get(sensor_header, None)
            sensor_duration = database.get(sensor_duration_header, None)
            sensor = {
                "name": sensor_name,
                "duration": sensor_duration
            }
            if sensor_name and sensor_duration:
                if not flavors[flavor_name]["sensors"].get("order"): flavors[flavor_name]["sensors"]["order"] = []
                flavors[flavor_name]["sensors"]["order"].append(sensor)
        # GET ALL MISC INFORMATION (it's just clock.)
        misc_count = conf.get("misc", {}).get("count", 0)
        for i in range(misc_count):
            log.debug(f"Getting name and duration for misc {i}...")
            i = f"{i:02}"
            misc_header = f"c_{flavor}_misc_{i}"
            misc_duration_header = f"c_{flavor}_misc_duration_{i}"
            misc_name = database.get(misc_header, None)
            misc_duration = database.get(misc_duration_header, None)
            misc = {
                "name": misc_name,
                "duration": misc_duration
            }
            if misc_name and misc_duration:
                if not flavors[flavor_name]["misc"].get("order"): flavors[flavor_name]["misc"]["order"] = []
                flavors[flavor_name]["misc"]["order"].append(misc)
        log.info(f"Got details for discovered flavor '{flavor}'")
    #log.warning(flavors)
    return flavors

