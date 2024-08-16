import subprocess
import os
import logging


class ModelConfig:

    def __init__(self):
        home = os.path.expanduser("~/")
        printer_data_config = os.path.join(home, "printer_data", "config")
        self.moonraker_config_path = printer_data_config + "/moonraker.conf"
        self.klipperscreen_config_path = printer_data_config + "/KlipperScreen.conf"
        self.printer_config_path = printer_data_config + "/printer.cfg"

    def get_mac_address(self, interface):
        try:
            result = subprocess.run(
                ["ip", "link", "show", interface], capture_output=True, text=True
            )
            output = result.stdout

            for line in output.split("\n"):
                if "link/ether" in line:
                    mac_address = line.split()[1]
                    return mac_address

        except Exception as e:
            logging.error(f"get mac address error: {e}")
            return None

    def generate_machine_name(self, model):
        mac_address = self.get_mac_address("eth0")
        if mac_address:
            mac_address = mac_address.replace(":", "")
            last_four = mac_address[-4:]
            machine_name = f"{model}-{last_four.upper()}"
            return machine_name
        else:
            return None

    def write_mdns_config(self, device_name):
        if device_name:
            try:
                with open(self.moonraker_config_path, "r") as file:
                    lines = file.readlines()

                with open(self.moonraker_config_path, "w") as file:
                    found_zeroconf_section = False
                    modified = False

                    for line in lines:
                        if line.strip().startswith("[zeroconf]"):
                            found_zeroconf_section = True
                        elif found_zeroconf_section and line.strip().startswith(
                            "mdns_hostname"
                        ):
                            file.write(f"mdns_hostname:{device_name}\n")
                            found_zeroconf_section = False
                            modified = True
                            continue
                        elif found_zeroconf_section and line.strip().startswith(
                            "enable_ssdp"
                        ):
                            file.write("enable_ssdp: True")
                            found_zeroconf_section = False
                            modified = True
                            continue

                        file.write(line)

                    if not modified:
                        file.write("\n[zeroconf]\n")
                        file.write(f"mdns_hostname:{device_name}\n")
                        file.write("enable_ssdp: True")
                logging.info(f"Setting MDNS address to {device_name}")
            except FileNotFoundError:
                logging.error(
                    f"The configuration file {self.moonraker_config_path} not found"
                )

    def write_device_name_config(self, device_name):
        if device_name:
            try:
                with open(self.klipperscreen_config_path, "r+") as file:
                    lines = file.readlines()
                    file.seek(0)
                    found_printer_section = False
                    for i, line in enumerate(lines):
                        if line.strip().startswith("[printer"):
                            lines[i] = f"[printer {device_name}]\n"
                            found_printer_section = True
                            break
                    if not found_printer_section:
                        lines.insert(0, f"[printer {device_name}]\n")
                    file.truncate(0)
                    file.writelines(lines)
                logging.info(f"Setting device name to {device_name}")
            except FileNotFoundError:
                logging.error(
                    f"Configuration file {self.klipperscreen_config_path} not found."
                )

    def wirte_printer_config(self, device_name):
        if device_name:
            try:
                with open(self.printer_config_path, "r+") as file:
                    lines = file.readlines()
                    file.seek(0)
                    found_printer_section = False
                    for i, line in enumerate(lines):
                        if line.strip().startswith("[include ../../klipper/config/"):
                            lines[i] = f"[include ../../klipper/config/{device_name}.cfg]\n"
                            found_printer_section = True
                            break
                    if not found_printer_section:
                        lines.insert(0, f"[include ../../klipper/config/{device_name}.cfg]\n")
                    file.truncate(0)
                    file.writelines(lines)

                logging.info(f"Setting printer config to {device_name}")

            except FileNotFoundError:
                logging.error(
                    f"Configuration file {self.printer_config_path} not found."
                )

    def generate_config(self, model):
        model_name = model
        model_name = model_name.split("_")[1]
        device_name = self.generate_machine_name(model_name)
        self.write_mdns_config(device_name)
        self.write_device_name_config(device_name)
        self.wirte_printer_config(model)
        os.system("systemctl restart klipper.service")
        os.system("systemctl restart moonraker.service")
        os.system("systemctl restart KlipperScreen.service")
