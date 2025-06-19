# Jullix Home Assistant Integration

[![Buy Me a Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&slug=stevengoossens&button_colour=FFDD00&font_colour=000000&font_family=Arial&outline_colour=000000&coffee_colour=ffffff)](https://coff.ee/stevengoossens)

[Jullix](https://jullix.com) is an energy management system that collects detailed information about your household energy usage. It can read information from your electricity meter, solar inverter and battery setup, and makes this data available over a local API.

This custom integration brings that data into Home Assistant. Sensors are created for the different energy categories (meter, solar, battery, charger and plug) by polling the Jullix device via its REST endpoints. Each sensor exposes values such as power, energy usage, voltage and more. The default host for the device is `http://jullix.local`, but this can be changed when configuring the integration.

## Installation

### Using HACS

1. In HACS, add [stevengoossensB/jullix](https://github.com/stevengoossensB/jullix) as a **Custom Repository** with category `integration`.
2. Install the **Jullix Home Assistant Integration** from the HACS store.
3. Restart Home Assistant.
4. Add the Jullix integration via the Home Assistant integrations page, specifying the correct host if different from the default.

### Manual

1. Copy this repository into the `config/custom_components/jullix` directory of your Home Assistant installation.
2. Restart Home Assistant.
3. Add the integration from the integrations page.

After setup, the sensors provided by your Jullix system will be available in Home Assistant so you can monitor energy consumption and production directly from your dashboard.
