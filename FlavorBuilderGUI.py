import sys, logging, coloredlogs, os
from PySide6.QtWidgets import (
    QApplication, QWidget, QScrollArea, QHBoxLayout,
    QVBoxLayout, QPushButton, QFrame, QFileDialog, QToolButton,
    QLabel, QLineEdit, QDialog, QMessageBox, QCheckBox, QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
import FlavorManagement as FM
import FlavorExtractor as FE

log = logging.getLogger("FlavorBuilderGUI")
coloredlogs.install("INFO")

if not os.path.exists("flavor-data"):
    os.makedirs("flavor-data")
if not os.path.exists("product-data"):
    os.makedirs("product-data")
if not os.path.exists("sensor-data"):
    os.makedirs("sensor-data")

class FoundFlavorsWindow(QDialog):
    def __init__(self, flavors:dict):
        super().__init__()
        self.resize(350,350)
        self.flavors = flavors
        layout = QVBoxLayout()
        self.setWindowTitle("DIF Flavor Manager")
        found_label = QLabel("Flavors extracted from database:")
        
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.MultiSelection)
        
        flavor_list = []
        for flavor in self.flavors:
            flavor_list.append(flavor)
        flavor_list.sort()
        self.list.addItems(flavor_list)
        
        options_row = QHBoxLayout()
        load_flavor_btn = QPushButton("Load Selected")
        load_flavor_btn.clicked.connect(self.load_flavor)
        save_flavor_btn = QPushButton("Save Selected")
        save_flavor_btn.clicked.connect(self.save_selected_flavors)
        save_all_btn = QPushButton("Save All")
        save_all_btn.clicked.connect(self.save_all_flavors)
        options_row.addWidget(load_flavor_btn)
        options_row.addWidget(save_flavor_btn)
        options_row.addWidget(save_all_btn)
        options_widget = QWidget()
        options_widget.setLayout(options_row)

        layout.addWidget(found_label)
        layout.addWidget(self.list)
        layout.addWidget(options_widget)
        self.setLayout(layout)
    
    def load_flavor(self):
        selection = self.list.selectedItems()
        if len(selection) > 1:
            warning = (f"Only one flavor may be loaded into the editor at a time.")
            log.error(warning)
            QApplication.beep()  # Plays default system alert sound
            QMessageBox.warning(self, "Warning", warning)
        else:
            selected = selection[0].text()
            selected_flavor = self.flavors.get(selected)
            FM.flavor = selected_flavor
            log.info(f"Loaded flavor '{FM.flavor.get('name', 'Untitled')}'")
            self.accept()
            self.close()

    def save_selected_flavors(self):
        tmp_flavor_cache = FM.flavor # CONTEXT: i'm too lazy to add logic or write a new save function, so i'm just going to load each flavor to the FlavorManagement global and then run the save function. 
        # once the saves are complete, i'll reload the cached flavor as to not lose the user's progress, should they cancel loading a flavor from the list.
        selections = self.list.selectedItems()
        for selection in selections:
            flavor_name = selection.text()
            flavor = self.flavors.get(flavor_name)
            FM.flavor = flavor
            log.debug(f"Prompting save for flavor '{flavor_name}'")
            flavor_name_path = os.path.join("flavor-data", f"{flavor_name}.json")
            file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Saving Flavor '{flavor_name}' to JSON File",
            flavor_name_path,
            "JSON Files (*.json);;All Files (*)"
            )
            if file_path:
                self.save_flavor(output_path=file_path)
        FM.flavor = tmp_flavor_cache # return the active flavor back to what it was before saving the discovered flavors

    def save_all_flavors(self):
        tmp_flavor_cache = FM.flavor
        #flavor_name_path = os.path.join("flavor-data", f"{flavor_name}.json")
        folder_path = QFileDialog.getExistingDirectory(
        self,
        f"Save All Flavors to Folder",
        "flavor-data", 
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        for flavor_name in self.flavors:
            flavor = self.flavors.get(flavor_name)
            FM.flavor = flavor
            file_path = os.path.join(folder_path, f"{flavor_name}.json")
            self.save_flavor(output_path=file_path)
        FM.flavor = tmp_flavor_cache

    def save_flavor(self, output_path):
        FM.save_flavor(output_path)
        ## ERROR CHECK BEFORE SAVE ##
        self.ErrorList = FM.error_check()
        ErrorString = ""
        for error in self.ErrorList:
            ErrorString += f"{error}\n"
        #self.ErrorMessageLabel.setText(ErrorString)
        #############################
        if len(self.ErrorList) > 0:
            warning = (f"You have saved a flavor with configuration errors. You will not be able to export this flavor to DIF until you resolve the following errors:\n"
            + ", ".join(f"\n! {err}" for err in self.ErrorList)          
            )
            log.warning(warning)
            QApplication.beep()  # Plays default system alert sound
            QMessageBox.warning(self, "Warning", warning)
    




class SensorWindow(QDialog):
    def __init__(self, index):
        self.index = index
        super().__init__()
        self.resize(350, 100)
        layout = QVBoxLayout()
        if index == None: # have to do this because 0 is otherwise interpreted as "not" 
            log.debug("New sensor?")
            self.sensor_name = None
            self.sensor_duration = None
        else:
            log.debug("Existing sensor?")
            self.sensor_name = FM.flavor["sensors"]["order"][index]["name"]
            self.sensor_duration = FM.flavor["sensors"]["order"][index]["duration"]
        self.setWindowTitle("Sensor Editor")

        ## SENSOR NAME FIELD
        sensorNameRow = QHBoxLayout()
        sensorNameLabel = QLabel("Name: ")
        self.sensorNameEditBox = QLineEdit()
        self.sensorNameEditBox.setPlaceholderText("Enter sensor name... (i.e. 'par_tmp001')")
        sensorNameRow.addWidget(sensorNameLabel)
        sensorNameRow.addWidget(self.sensorNameEditBox)
        sensorNameWidget = QWidget()
        sensorNameWidget.setLayout(sensorNameRow)

        ## SENSOR DURATION FIELD
        sensorDurationRow = QHBoxLayout()
        sensorDurationLabel = QLabel("Duration: ")
        self.sensorDurEditBox = QLineEdit()
        self.sensorDurEditBox.setPlaceholderText("Enter sensor duration in seconds... (i.e. 5)")
        sensorDurationRow.addWidget(sensorDurationLabel)
        sensorDurationRow.addWidget(self.sensorDurEditBox)
        sensorDurWidget = QWidget()
        sensorDurWidget.setLayout(sensorDurationRow)

        ## SET THE EXISTING DATA IN THE FIELDS IF INDEXED
        if self.sensor_name and self.sensor_duration:
            self.sensorNameEditBox.setText(str(self.sensor_name))
            self.sensorDurEditBox.setText(str(self.sensor_duration))

        ## ADD / DELETE BUTTONS
        sensorOptionsRow = QHBoxLayout()
        self.sensorAddBtn = QPushButton("Confirm")
        self.sensorAddBtn.clicked.connect(self.confirm_sensor)
        sensorOptionsRow.addWidget(self.sensorAddBtn)
        
        self.sensorDeleteBtn = QPushButton("Delete") 
        if index == None:
            self.sensorDeleteBtn.setEnabled(False) # Make grayed out if sensor does not yet exist 
        else:
            self.sensorDeleteBtn.setEnabled(True)
        self.sensorDeleteBtn.clicked.connect(self.delete_sensor)
        sensorOptionsRow.addWidget(self.sensorDeleteBtn)
        sensorOptionsWidget = QWidget()
        sensorOptionsWidget.setLayout(sensorOptionsRow)
        
        ## ERROR
        self.ErrorMessageLabel = QLabel("")
        self.ErrorMessageLabel.setStyleSheet("color: red;")

        layout.addWidget(sensorNameWidget)
        layout.addWidget(sensorDurWidget)
        layout.addWidget(self.ErrorMessageLabel)
        layout.addWidget(sensorOptionsWidget)

        self.setLayout(layout)


    def confirm_sensor(self):
        if self.index == None:
            log.debug(f"Attempting to add new sensor")
            sensor_name = self.sensorNameEditBox.text()
            sensor_duration = self.sensorDurEditBox.text()
            response = FM.update_sensor(None, sensor_name, sensor_duration)
            if response == "OK":
                self.accept()
                self.close()
            else:
                self.ErrorMessageLabel.setText(response)
        else:
            log.debug(f"Attempting to update existing sensor")
            sensor_name = self.sensorNameEditBox.text()
            sensor_duration = self.sensorDurEditBox.text()
            response = FM.update_sensor(self.index, sensor_name, sensor_duration)
            if response == "OK":
                self.accept()
                self.close()
            else:
                self.ErrorMessageLabel.setText(response)

    def delete_sensor(self):
        if self.index != None:
            log.debug(f"Attempting to delete existing sensor")
            response = FM.remove_sensor(self.index)
            if response == "OK":
                self.accept()
                self.close()
            else:
                self.ErrorMessageLabel.setText(response)
        else:
            error = f"You cannot delete a sensor with a null index. How did you get here?"
            self.ErrorMessageLabel.setText(error)

class ProductWindow(QDialog):
    def __init__(self, index):
        self.index = index
        super().__init__()
        self.resize(350, 100)
        layout = QVBoxLayout()
        if index == None: # have to do this because 0 is otherwise interpreted as "not" 
            log.debug("New product?")
            self.product_name = None
            self.product_duration = None
        else:
            log.debug("Existing product?")
            self.product_name = FM.flavor["products"]["order"][index]["name"]
            self.product_duration = FM.flavor["products"]["order"][index]["duration"]
        self.setWindowTitle("Product Editor")

        ## PRODUCT NAME FIELD
        productNameRow = QHBoxLayout()
        productNameLabel = QLabel("Name: ")
        self.productNameEditBox = QLineEdit()
        self.productNameEditBox.setPlaceholderText("Enter product name... (i.e. 'cc001a')")
        #self.productNameEditBox.textChanged.connect(self.update_flavor_name)
        productNameRow.addWidget(productNameLabel)
        productNameRow.addWidget(self.productNameEditBox)
        productNameWidget = QWidget()
        productNameWidget.setLayout(productNameRow)

        ## PRODUCT DURATION FIELD
        productDurationRow = QHBoxLayout()
        productDurationLabel = QLabel("Duration: ")
        self.productDurEditBox = QLineEdit()
        self.productDurEditBox.setPlaceholderText("Enter product duration in seconds... (i.e. 10)")
        productDurationRow.addWidget(productDurationLabel)
        productDurationRow.addWidget(self.productDurEditBox)
        productDurWidget = QWidget()
        productDurWidget.setLayout(productDurationRow)

        ## SET THE EXISTING DATA IN THE FIELDS IF INDEXED
        if self.product_name and self.product_duration:
            self.productNameEditBox.setText(str(self.product_name))
            self.productDurEditBox.setText(str(self.product_duration))

        ## ADD / DELETE BUTTONS
        productOptionsRow = QHBoxLayout()
        self.productAddBtn = QPushButton("Confirm")
        self.productAddBtn.clicked.connect(self.confirm_product)
        productOptionsRow.addWidget(self.productAddBtn)
        
        self.productDeleteBtn = QPushButton("Delete") 
        if index == None:
            self.productDeleteBtn.setEnabled(False) # Make grayed out if product does not yet exist 
        else:
            self.productDeleteBtn.setEnabled(True)
        self.productDeleteBtn.clicked.connect(self.delete_product)
        productOptionsRow.addWidget(self.productDeleteBtn)
        productOptionsWidget = QWidget()
        productOptionsWidget.setLayout(productOptionsRow)
        
        ## ERROR
        self.ErrorMessageLabel = QLabel("")
        self.ErrorMessageLabel.setStyleSheet("color: red;")

        layout.addWidget(productNameWidget)
        layout.addWidget(productDurWidget)
        layout.addWidget(self.ErrorMessageLabel)
        layout.addWidget(productOptionsWidget)

        self.setLayout(layout)

    def confirm_product(self):
        if self.index == None:
            log.debug(f"Attempting to add new product")
            product_name = self.productNameEditBox.text()
            product_duration = self.productDurEditBox.text()
            #response = FM.add_product(product_name, product_duration)
            response = FM.update_product(None, product_name, product_duration)
            if response == "OK":
                self.accept()
                self.close()
            else:
                self.ErrorMessageLabel.setText(response)
        else:
            log.debug(f"Attempting to update existing product")
            product_name = self.productNameEditBox.text()
            product_duration = self.productDurEditBox.text()
            response = FM.update_product(self.index, product_name, product_duration)
            if response == "OK":
                self.accept()
                self.close()
            else:
                self.ErrorMessageLabel.setText(response)

    def delete_product(self):
        if self.index != None:
            log.debug(f"Attempting to delete existing product")
            response = FM.remove_product(self.index)
            if response == "OK":
                self.accept()
                self.close()
            else:
                self.ErrorMessageLabel.setText(response)
        else:
            error = f"You cannot delete a product with a null index. How did you get here?"
            self.ErrorMessageLabel.setText(error)



class MainWindow(QWidget):
    def __init__(self):
        ## SETUP
        super().__init__()
        self.flavor_length = 0
        self.total_product_count = 0
        self.total_product_length = 0
        self.total_sensor_length = 0
        self.product_window = None
        self.flavor_name = None
        self.products = []
        self.setWindowTitle(f"WeatherSTAR XL Flavor Builder | Editing Flavor: {self.flavor_name}")
        self.resize(800, 600)
        self.selected_file = None
        self.ErrorList = []

        main_layout = QVBoxLayout()

        # LOAD/SAVE/RESET/EXPORT BUTTONS
        self.resetbtn = QPushButton("Reset Flavor")
        self.resetbtn.clicked.connect(self.reset_everything)
        main_layout.addWidget(self.resetbtn)
        self.loadJSONbtn = QPushButton("Load Flavor from JSON")
        self.loadJSONbtn.clicked.connect(self.load_json_file)
        main_layout.addWidget(self.loadJSONbtn)
        self.saveJSONbtn = QPushButton("Save Flavor to JSON")
        self.saveJSONbtn.clicked.connect(self.save_json_file)
        main_layout.addWidget(self.saveJSONbtn)
        self.loadDIFbtn = QPushButton("Load Flavors from DIF")
        self.loadDIFbtn.clicked.connect(self.load_dif_flavors)
        main_layout.addWidget(self.loadDIFbtn)
        self.exportDIFbtn = QPushButton("Export Flavor to DIF")
        self.exportDIFbtn.clicked.connect(self.export_dif_txt)
        main_layout.addWidget(self.exportDIFbtn)

        # FLAVOR ERROR WIDGET
        self.ErrorMessageLabel = QLabel("")
        self.ErrorMessageLabel.setStyleSheet("color: red;")
        main_layout.addWidget(self.ErrorMessageLabel)
        
        # FLAVOR NAME WIDGET SETUP
        flavorNameRow = QHBoxLayout()
        flavorNameLabel = QLabel("Flavor Name: ")
        self.flavorNameEditBox = QLineEdit()
        self.flavorNameEditBox.setPlaceholderText("Enter flavor name... (i.e. 'D')")
        self.flavorNameEditBox.textChanged.connect(self.update_flavor_name)
        flavorNameRow.addWidget(flavorNameLabel)
        flavorNameRow.addWidget(self.flavorNameEditBox)
        flavorNameWidget = QWidget()
        flavorNameWidget.setLayout(flavorNameRow)
        main_layout.addWidget(flavorNameWidget)

        # FLAVOR INIT WIDGET SETUP
        flavorInitRow = QHBoxLayout()
        flavorInitLabel = QLabel("Init Flavor: ")
        self.flavorInitBox = QCheckBox()
        self.flavorInitBox.stateChanged.connect(self.init_flavor)
        self.flavorInitMod = QLineEdit()
        self.flavorInitMod.textChanged.connect(self.update_flavor_mods)
        self.flavorInitMod.setPlaceholderText("Enter flavor modifiers... (i.e. 'IfValidAppend(l_nws001a_valid c_flavmod_nws1)')")
        self.flavorInitMod.setEnabled(False)
        flavorInitRow.addWidget(flavorInitLabel)
        flavorInitRow.addWidget(self.flavorInitBox)
        flavorInitRow.addWidget(self.flavorInitMod)
        flavorInitWidget = QWidget()
        flavorInitWidget.setLayout(flavorInitRow)
        main_layout.addWidget(flavorInitWidget)


        clockRow = QHBoxLayout()
        clockLabel = QLabel("Clock Enabled: ")
        self.clockBox = QCheckBox()
        self.clockBox.setChecked(True)
        self.clockBox.stateChanged.connect(self.clock_toggle)
        clockRow.addWidget(clockLabel)
        clockRow.addWidget(self.clockBox)
        clockWidget = QWidget()
        clockWidget.setLayout(clockRow)
        main_layout.addWidget(clockWidget)

        # PRODUCT ORDER CONTAINER
        self.product_duration_label = QLabel(f"Products Length: 0 seconds")
        self.product_area = QScrollArea()
        self.product_area.setWidgetResizable(True)
        self.product_area.setFixedHeight(160)
        container_products = QFrame()
        self.products_layout_root = QVBoxLayout(container_products)
        self.products_layout_root.addWidget(self.product_duration_label)
        self.products_layout = QHBoxLayout()
        self.products_layout.setSpacing(10)
        self.product_area.setWidget(container_products)
        self.products_layout_root.addLayout(self.products_layout)
        main_layout.addWidget(self.product_area)
        
        # SENSOR ORDER CONTAINER
        self.sensor_duration_label = QLabel(f"Sensors Length: 0 seconds")
        self.sensor_area = QScrollArea()
        self.sensor_area.setWidgetResizable(True)
        self.sensor_area.setFixedHeight(95)
        container_sensors = QFrame()
        self.sensors_layout_root = QVBoxLayout(container_sensors)
        self.sensors_layout_root.addWidget(self.sensor_duration_label)
        self.sensors_layout = QHBoxLayout()
        self.sensors_layout.setSpacing(10)
        self.sensors_layout_root.addLayout(self.sensors_layout)
        self.sensor_area.setWidget(container_sensors)
        main_layout.addWidget(self.sensor_area)

        self.lf_length_label = QLabel(f"Total Forecast Length: 0 seconds")

        # PRODUCTS AND SENSORS (NONE BY DEFAULT)
        self.get_products()
        self.get_sensors()


        main_layout.addWidget(self.lf_length_label)

        self.setLayout(main_layout)


    def clock_toggle(self, state):
        if state == Qt.CheckState.Checked.value: # compares int to int, resolving issue #1
            FM.update_clock_setting(True, self.total_product_length)
            log.info(f"On-screen clock enabled")
        else:
            FM.update_clock_setting(False, self.total_product_length)
            log.info(f"On-screen clock disabled")
         ## ERROR CHECK UPON UPDATE ##
        self.ErrorList = FM.error_check()
        ErrorString = ""
        for error in self.ErrorList:
            ErrorString += f"{error}\n"
        self.ErrorMessageLabel.setText(ErrorString)

    def init_flavor(self, state):
        if state == Qt.CheckState.Checked.value: # compares int to int, resolving issue #1
            self.flavorInitMod.setEnabled(True)
            FM.flavor["init"] = True
        else:
            self.flavorInitMod.setEnabled(False)
            FM.flavor["init"] = False
            FM.flavor["modifiers"] = None

    def reset_everything(self):
        QApplication.beep()
        response = QMessageBox.question(
            self,
            "RESET EVERYTHING???",
            "The active flavor configuration will be nulled. Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if response == QMessageBox.Yes:
            log.debug("Attempting to reset flavor config")
            FM.flavor = {} # reset! LOL
            self.flavorNameEditBox.setText("")
            self.clockBox.setChecked(False)
            self.flavorInitBox.setChecked(False)
            self.flavorInitMod.setText("")
            self.get_products()
            self.get_sensors()

    def load_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Flavor from JSON File",
            "flavor-data",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.selected_file = file_path
            FM.load_flavor(file_path)
            self.refresh_flavor()
    
    def save_json_file(self):
        suggested_path = os.path.join("flavor-data", f"{FM.flavor.get('name', 'flavor')}.json")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Flavor to JSON File",
            suggested_path,
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.selected_file = file_path
            FM.save_flavor(file_path)
            ## ERROR CHECK BEFORE SAVE ##
            self.ErrorList = FM.error_check()
            ErrorString = ""
            for error in self.ErrorList:
                ErrorString += f"{error}\n"
            self.ErrorMessageLabel.setText(ErrorString)
            #############################
            if len(self.ErrorList) > 0:
                warning = (f"You have saved a flavor with configuration errors. You will not be able to export this flavor to DIF until you resolve the following errors:\n"
                 + ", ".join(f"\n! {err}" for err in self.ErrorList)          
                )
                log.warning(warning)
                QApplication.beep()  # Plays default system alert sound
                QMessageBox.warning(self, "Warning", warning)

    def refresh_flavor(self):
        '''Refreshes all of the editor elements to reflect the current state of FM.flavor'''
        self.flavor_name = FM.flavor.get("name")
        self.setWindowTitle(f"WeatherSTAR XL Flavor Builder | Editing Flavor: {self.flavor_name}")
        self.flavorNameEditBox.setText(self.flavor_name)
        ## LOAD INTO EDITOR:
        self.get_products() # Get the products to show in the list
        self.get_sensors()
        misc_order = FM.flavor.get("misc", {}).get("order", None)
        if misc_order:
            # Clock might be enabled but let's check
            if isinstance(misc_order, list) and len(misc_order) > 0:
                for obj in misc_order:
                    if obj.get("name", None) == "clock":
                        log.debug("Clock is enabled for this flavor")
                        self.clockBox.setChecked(True)
        else:
            # If no misc order then there's no clock
            log.debug("Clock is disabled for this flavor")
            self.clockBox.setChecked(False)
        flavor_init = FM.flavor.get("init", False)
        self.flavorInitBox.setChecked(flavor_init)
        flavor_mods = FM.flavor.get("modifiers", None)
        if flavor_mods:
            self.flavorInitMod.setText(flavor_mods)
        else:
            self.flavorInitMod.setText("")
        ## ERROR CHECK UPON UPDATE ##
        self.ErrorList = FM.error_check()
        ErrorString = ""
        for error in self.ErrorList:
            ErrorString += f"{error}\n"
        self.ErrorMessageLabel.setText(ErrorString)

    def load_dif_flavors(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Flavors from DIF File",
            None,
            "WXL DIF Files (*.dat *.txt);;All Files (*)"
        )
        if file_path:
            extracted_flavors = FE.extract_flavors_from_file(file_path=file_path)
            dialog = FoundFlavorsWindow(extracted_flavors)
            if dialog.exec() == QDialog.Accepted:
                log.debug(f"Flavor loaded from list.")
                self.refresh_flavor()


    def export_dif_txt(self):
        ## ERROR CHECK UPON UPDATE ##
        self.ErrorList = FM.error_check()
        ErrorString = ""
        for error in self.ErrorList:
            ErrorString += f"{error}\n"
        self.ErrorMessageLabel.setText(ErrorString)
        if len(self.ErrorList) < 1:
            suggested_path = os.path.join("exported", f"{self.flavor_name}.txt")
            if not os.path.exists("exported"):
                os.makedirs("exported")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Flavor to DIF TXT File",
                suggested_path,
                "TXT File (*.txt)"
            )
            if file_path:
                FM.export_dif_txt(file_path)
            else:
                log.debug(f"Export aborted.")
        else:
            warning = (f"You cannot export this DIF until conflicts are resolved.")
            log.error(warning)
            QApplication.beep()  # Plays default system alert sound
            QMessageBox.warning(self, "Warning", warning)

    def update_flavor_name(self, new_name):
        self.flavor_name = new_name
        FM.flavor["name"] = self.flavor_name
        self.setWindowTitle(f"WeatherSTAR XL Flavor Builder | Editing Flavor: {self.flavor_name}")
        ## ERROR CHECK UPON UPDATE ##
        self.ErrorList = FM.error_check()
        ErrorString = ""
        for error in self.ErrorList:
            ErrorString += f"{error}\n"
        self.ErrorMessageLabel.setText(ErrorString)
    
    def update_flavor_mods(self, modifiers):
        if modifiers != "":
            FM.flavor["modifiers"] = modifiers
            ## ERROR CHECK UPON UPDATE ##
            self.ErrorList = FM.error_check()
            ErrorString = ""
            for error in self.ErrorList:
                ErrorString += f"{error}\n"
            self.ErrorMessageLabel.setText(ErrorString)
        else:
            FM.flavor["modifiers"] = None

    def update_product_order(self):
        log.warning(f"To do")

    def edit_product(self, index):
        dialog = ProductWindow(index)
        if dialog.exec() == QDialog.Accepted:
            log.debug(f"Product edits confirmed.")
        else:
            log.debug(f"Product edits aborted.")
        self.get_products()
        ## ERROR CHECK UPON UPDATE ##
        self.ErrorList = FM.error_check()
        ErrorString = ""
        for error in self.ErrorList:
            ErrorString += f"{error}\n"
        self.ErrorMessageLabel.setText(ErrorString)

    def edit_sensor(self, index):
        dialog = SensorWindow(index)
        if dialog.exec() == QDialog.Accepted:
            log.debug(f"Sensor edits confirmed.")
        else:
            log.debug(f"Sensor edits aborted.")
        self.get_sensors()
        ## ERROR CHECK UPON UPDATE ##
        self.ErrorList = FM.error_check()
        ErrorString = ""
        for error in self.ErrorList:
            ErrorString += f"{error}\n"
        self.ErrorMessageLabel.setText(ErrorString)

    def add_product(self):
        self.edit_product(None) # No index if non-existing product
        #self.get_products()
    def add_sensor(self):
        self.edit_sensor(None) # No index if new

    def get_products(self):
        container_products = QFrame()
        self.products_layout_root = QVBoxLayout(container_products)
        self.products_layout_root.addWidget(self.product_duration_label)
        self.products_layout = QHBoxLayout()
        self.products_layout.setSpacing(10)
        self.products_layout_root.addLayout(self.products_layout)
        self.product_area.setWidget(container_products)
        products_list = FM.get_products()
        i = 0
        for product_dict in products_list:
            prod_name = product_dict.get("name", None)
            prod_dur = product_dict.get("duration", None)
            if prod_name and prod_dur:
                btn = QToolButton()
                ico_path = os.path.join("product-data", prod_name, "thumb.jpg")
                if os.path.exists(ico_path):
                    log.debug(f"Found thumbnail for product '{prod_name}'")
                    btn.setIcon(QIcon(ico_path))
                    btn.setIconSize(QSize(100, 100))
                btn.setFixedSize(110, 110)
                #btn.setStyleSheet("border: none;")
                btn.setText(prod_name)
                btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
                #btn.clicked.connect(lambda n=i: self.edit_product(n))
                btn.setCheckable(False)
                btn.clicked.connect(lambda *args, n=i: self.edit_product(n))
                self.products_layout.addWidget(btn)
                i += 1 # up the index AFTER adding product to list
            else:
                i += 1
                log.warning(f"Invalid product found in JSON - deleting.")
                FM.remove_product(i)
                i -= 1
        self.total_product_count, self.total_product_length = FM.get_total_products()
        if self.clockBox.isChecked():
            FM.update_clock_setting(True, self.total_product_length)
        self.product_duration_label.setText(f"Products Length: {self.total_product_length} seconds")
        self.lf_length_label.setText(f"Total Forecast Length: {self.total_product_length} seconds")

        # ADD PRODUCT BUTTON AT THE END
        addproductbtn = QToolButton()
        addproductbtn.setIcon(QIcon("app/add.png"))
        addproductbtn.setIconSize(QSize(100, 100))
        addproductbtn.setFixedSize(110, 110)
        addproductbtn.setText("Add Product")
        addproductbtn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        addproductbtn.clicked.connect(self.add_product)
        self.products_layout.addWidget(addproductbtn)

    def get_sensors(self):
        container_sensors = QFrame()
        self.sensors_layout_root = QVBoxLayout(container_sensors)
        self.sensors_layout_root.addWidget(self.sensor_duration_label)
        self.sensors_layout = QHBoxLayout()
        self.sensors_layout.setSpacing(10)
        self.sensors_layout_root.addLayout(self.sensors_layout)
        self.sensor_area.setWidget(container_sensors)
        sensors_list = FM.get_sensors()
        i = 0
        for sensors_dict in sensors_list:
            sens_name = sensors_dict.get("name", None)
            sens_dur = sensors_dict.get("duration", None)
            if sens_name and sens_dur:
                btn = QToolButton()
                ico_path = os.path.join("sensor-data", sens_name, "thumb.png")
                if os.path.exists(ico_path):
                    log.debug(f"Found thumbnail for sensor '{sens_name}'")
                    btn.setIcon(QIcon(ico_path))
                    btn.setIconSize(QSize(100, 50))
                btn.setFixedSize(110, 50)
                btn.setText(sens_name)
                btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
                btn.setCheckable(False)
                btn.clicked.connect(lambda *args, n=i: self.edit_sensor(n))
                self.sensors_layout.addWidget(btn)
                i += 1
            else:
                i += 1
                log.warning(f"Invalid sensor found in JSON - deleting.")
                FM.remove_product(i)
                i -= 1
        self.total_sensor_count, self.total_sensor_length = FM.get_total_sensors()
        self.sensor_duration_label.setText(f"Sensors Length: {self.total_sensor_length} seconds")

        btn = QToolButton()
        btn.setIcon(QIcon("app/add_sens.png"))
        btn.setIconSize(QSize(100, 50))
        btn.setFixedSize(110, 50)
        btn.setText("Add Sensor")
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.clicked.connect(self.add_sensor)
        self.sensors_layout.addWidget(btn)

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()