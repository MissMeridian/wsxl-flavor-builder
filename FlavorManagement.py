# Manages the flavor details
import json, re, time
import logging, coloredlogs
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO")

flavor = {}

def float_or_int(input_:str):
    '''This is really stupid but whatever. Input a string number, and if it's a whole number, it gets returned as int. If it's a decimal, it's returned as a float.'''
    try:
        number = float(input_)
        if number.is_integer():
            return int(number)
        return number
    except ValueError:
        log.debug("Bad number, BAD!!!")
        return None
    except TypeError:
        log.debug("Bad variable type was given - could not determine float or integer")
        return None
    except:
        return None

def load_flavor(path:str):
    global flavor
    try:
        with open(path, "r") as flavor_file:
            global flavor
            flavor = json.load(flavor_file)
            flavor_file.close()
            log.debug(f"Loaded JSON successfully")
    except FileNotFoundError:
        log.error(f"Could not open requested file path: {path}\nFile Not Found", exc_info=False)
    except PermissionError:
        log.error(f"Could not open requested file path: {path}\nPermission Error / Access Denied", exc_info=False)
    except json.JSONDecodeError:
        log.error(f"Could not open requested file path: {path}\nMalformatted JSON", exc_info=False)
    except Exception as e:
        log.error(f"Could not open requested file path: {path}\n{e}", exc_info=False)
    except:
        log.error(f"What tf happened")

def save_flavor(path:str):
    global flavor
    if flavor.get("init", None) == None:
        flavor["init"] = False
    try:
        with open(path, "w") as flavor_file:
            name = flavor.get("name")
            json.dump(flavor, flavor_file, indent=4)
            log.debug(f"Saved JSON successfully")
            log.info(f"Flavor '{name}' has been saved to: '{path}'")
    except PermissionError:
        log.error(f"Could not save to requested file path: {path}\nPermission Error / Access Denied", exc_info=False)
    except Exception as e:
        log.error(f"Could not save to requested file path: {path}\n{e}", exc_info=False)
    except:
        log.error(f"What tf happened")

def clear_flavor():
    global flavor
    flavor = {}
    log.debug(f"Cleared flavor dict")

def error_check():
    global flavor
    errors = []
    flavor_name = flavor.get("name", "")
    misc_order = flavor.get("misc", {}).get("order", [])
    product_count, product_duration_total = get_total_products()
    if bool(re.search(r'[^A-Z0-9]', flavor_name)):
        errors.append("Flavor name contains an invalid character.")
    elif len(flavor_name) == 0:
        errors.append("Flavor name must contain at least one character.")
    if len(misc_order) > 0:
        if misc_order[0].get("name") == "clock":
            # Check that there is an actual product count if the clock is enabled
            if product_count == 0:
                errors.append("Clock cannot be enabled if there are no products.")
        if float(misc_order[0].get("duration")) > float(product_duration_total):
            errors.append("Clock duration is longer than total product duration.")
    if product_count == 0:
        errors.append("You must have at least 1 product.")
    if product_count > 99:
        errors.append("Product count cannot be higher than 99!")

    #errors.append("Test error")
    return errors

def update_product(index:int | None, name:str, duration):
    global flavor
    if name and duration:
        if float_or_int(duration) == None:
            error = "Product duration must be a whole number or decimal."
            log.error(error)
            return error
        if not flavor.get("products"):
            flavor["products"] = {}
            log.debug("Initialized products dict")
        if not flavor.get("products", {}).get("order"):
            flavor["products"]["order"] = []
            log.debug("Initialized products order list")
        product = {
            "name": name,
            "duration": float_or_int(duration)
        }
        if index != None: # This is an existing product
            flavor["products"]["order"][index] = product
            log.info(f"Updated product {index}: '{name}' with duration of {duration} seconds.")
            return "OK"
        else: # No index means new product
            flavor["products"]["order"].append(product)
            log.info(f"Added product '{name}' with duration of {duration} seconds.")
            return "OK"
    if not name:
        error = "Product requires a name! (i.e. 'ex001a')"
        log.error(error, exc_info=False)
        return error
    if not duration:
        error = "Product requires a duration! (i.e. 15)"
        log.error(error, exc_info=False)
        return error
    return False

def remove_product(index:int):
    global flavor
    try:
        prod_name = flavor["products"]["order"][index]["name"]
        prod_duration = flavor["products"]["order"][index]["duration"]
        log.debug(f"Removing product {index}: '{prod_name}' with duration of {prod_duration} seconds.")
        flavor["products"]["order"].pop(index)
        return "OK"
    except KeyError:
        error = f"Error trying to remove product index {index}:\nKey Error"
        log.error(error)
        return error
    except Exception as e:
        error = f"Error trying to remove product index {index}:\n{e}"
        log.error(error)
        return error
    except:
        log.error(f"What tf happened")
        return None



def update_sensor(index:int | None, name:str, duration):
    global flavor
    if name and duration:
        if float_or_int(duration) == None:
            error = "sensor duration must be a whole number or decimal."
            log.error(error)
            return error
        if not flavor.get("sensors"):
            flavor["sensors"] = {}
            log.debug("Initialized sensors dict")
        if not flavor.get("sensors", {}).get("order"):
            flavor["sensors"]["order"] = []
            log.debug("Initialized sensors order list")
        sensor = {
            "name": name,
            "duration": float_or_int(duration)
        }
        if index != None: # This is an existing sensor
            flavor["sensors"]["order"][index] = sensor
            log.info(f"Updated sensor {index}: '{name}' with duration of {duration} seconds.")
            return "OK"
        else: # No index means new sensor
            flavor["sensors"]["order"].append(sensor)
            log.info(f"Added sensor '{name}' with duration of {duration} seconds.")
            return "OK"
    if not name:
        error = "Sensor requires a name! (i.e. 'par_hum001')"
        log.error(error, exc_info=False)
        return error
    if not duration:
        error = "Sensor requires a duration! (i.e. 7)"
        log.error(error, exc_info=False)
        return error
    return False

def remove_sensor(index:int):
    global flavor
    try:
        sens_name = flavor["sensors"]["order"][index]["name"]
        sens_duration = flavor["sensors"]["order"][index]["duration"]
        log.debug(f"Removing sensor {index}: '{sens_name}' with duration of {sens_duration} seconds.")
        flavor["sensors"]["order"].pop(index)
        return "OK"
    except KeyError:
        error = f"Error trying to remove sensor index {index}:\nKey Error"
        log.error(error)
        return error
    except Exception as e:
        error = f"Error trying to remove sensor index {index}:\n{e}"
        log.error(error)
        return error
    except:
        log.error(f"What tf happened")
        return None


def get_products():
    global flavor
    if not flavor.get("products"):
        flavor["products"] = {}
        log.debug("Initialized products dict")
    if not flavor.get("products", {}).get("order"):
        flavor["products"]["order"] = []
        log.debug("Initialized products order list")
    return flavor["products"]["order"]

def get_sensors():
    global flavor
    if not flavor.get("sensors"):
        flavor["sensors"] = {}
        log.debug("Initialized sensors dict")
    if not flavor.get("sensors", {}).get("order"):
        flavor["sensors"]["order"] = []
        log.debug("Initialized sensors order list")
    return flavor["sensors"]["order"]


def get_total_products():
    '''Updates the product count and defines the flavor duration.'''
    global flavor
    products = get_products()
    product_count = 0
    product_time = 0
    for product_dict in products:
        product_count += 1
        product_duration = product_dict.get("duration", 0)
        product_time += float_or_int(product_duration)
    flavor["products"]["count"] = product_count
    flavor["duration"] = f"{product_time} sec"
    return product_count, float_or_int(product_time) # we'll use this to set the clock

def get_total_sensors():
    '''Updates the sensor count and defines the flavor duration.'''
    global flavor
    sensors = get_sensors()
    sensor_count = 0
    sensor_time = 0
    for sensor in sensors:
        sensor_count += 1
        sensor_duration = sensor.get("duration", 0)
        sensor_time += float_or_int(sensor_duration)
    flavor["sensors"]["count"] = sensor_count
    #flavor["duration"] = f"{sensor_time} sec"
    return sensor_count, float_or_int(sensor_time)

def update_clock_setting(on:bool, duration:float):
    '''Updates the misc product order (clock) with the provided duration.
    on: If True, the misc layer becomes available.
    duration: Float value, should match the length of all products.'''
    global flavor

    duration

    if on == True:
        flavor["misc"] = {}
        flavor["misc"]["count"] = 1
        flavor["misc"]["order"] = [{"name": "clock", "duration": duration}]
    else:
        flavor["misc"] = {}
        flavor["misc"]["count"] = 0


def dif_string(key:str, data:str):
    l = f'"{key}",0,0,"{data}"\n'
    return l

def export_dif_txt(file_path:str):
    log.info("Building DIF import TXT...")
    flavor_name = flavor.get("name", None)
    get_total_products()
    dif = ''
    flavor_duration = flavor.get("duration", "NULL sec")
    flavor_str = f"c_flavor_{flavor_name}"
    flavor_init = flavor.get("init", False)
    flavor_mods = flavor.get("modifiers", "")
    flavor_products_order = flavor["products"].get("order", [])
    flavor_sensors_order = flavor["sensors"].get("order", [])
    flavor_misc_order = flavor["misc"].get("order", [])
    version_str = f"EXPORT_{int(time.time())}" # will add a version string manager later
    # Flavor Init
    if flavor_init:
        flavor_init_str = f"@Init({flavor_name})"
        if flavor_mods:
            flavor_init_str += flavor_mods
        dif += dif_string(flavor_str, flavor_init_str) # being under this condition makes sure the key is only created if init is true
    # Flavor Duration
    dif += dif_string(f"c_{flavor_name}_duration", flavor_duration)
    # PRODUCTS --------------------------------------------------------------
    dif += dif_string(f"c_{flavor_name}_product_num", flavor["products"]["count"]) # Product Count
    i = 0
    for item in flavor_products_order:
        item_type = "product"
        item_name = item["name"]
        item_duration = item["duration"]
        i_str = f"{i:02}"
        dif += dif_string(f"c_{flavor_name}_{item_type}_{i_str}", item_name)
        dif += dif_string(f"c_{flavor_name}_{item_type}_duration_{i_str}", item_duration)
        i += 1
    # SENSORS --------------------------------------------------------------
    dif += dif_string(f"c_{flavor_name}_sensor_num", flavor["sensors"]["count"]) # Product Count
    i = 0
    for item in flavor_sensors_order:
        item_type = "sensor"
        item_name = item["name"]
        item_duration = item["duration"]
        i_str = f"{i:02}"
        dif += dif_string(f"c_{flavor_name}_{item_type}_{i_str}", item_name)
        dif += dif_string(f"c_{flavor_name}_{item_type}_duration_{i_str}", item_duration)
        i += 1
    # MISC --------------------------------------------------------------
    dif += dif_string(f"c_{flavor_name}_misc_num", flavor["misc"]["count"]) # Product Count
    i = 0
    for item in flavor_misc_order:
        item_type = "misc"
        item_name = item["name"]
        item_duration = item["duration"]
        i_str = f"{i:02}"
        dif += dif_string(f"c_{flavor_name}_{item_type}_{i_str}", item_name)
        dif += dif_string(f"c_{flavor_name}_{item_type}_duration_{i_str}", item_duration)
        i += 1
    # Version Strings (still don't know if they're needed for load or not)
    dif += dif_string(f"c_{flavor_name}_product_version", version_str)
    dif += dif_string(f"c_{flavor_name}_sensor_version", version_str)
    dif += dif_string(f"c_{flavor_name}_misc_version", version_str)
    with open(file_path, "w") as out_f:
        out_f.write(dif)
        out_f.close()
    log.info(f"Wrote DIF to '{file_path}'!\nYou can import this to your XL by uploading the file via FTP, and then running the following command:\n/twc/bin/db_imp -d -r -s dif /twc/dif/wxl_dif /path/to/file.txt")