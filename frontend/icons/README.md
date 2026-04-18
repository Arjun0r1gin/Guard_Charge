# Charger Icon Specifications

Please follow these guidelines when creating custom map icons for the chargers to ensure they look good on the map.

## Specifications

* **Dimensions:** 32x32 pixels (or 64x64 pixels scaled down to 32x32 for retina displays).
* **Format:** SVG (preferred for infinite scaling) or PNG (with a transparent background).
* **Anchor Point:** Ensure the bottom-center of the icon points exactly to the geographical location of the charger.

## Design Guidelines

* **Contrast:** The map uses a dark theme. Ensure your icons have high contrast and stand out against dark backgrounds (e.g., use white borders or bright colors).
* **Simplicity:** Keep designs clean and recognizable at small sizes. Avoid intricate details that will be lost at 32x32 resolution.
* **Consistency:** If creating multiple icons for different operators, maintain a consistent visual language (e.g., same stroke width, border radius).

## Current Temporary Implementation
The map currently uses CSS-generated circular markers displaying the first two letters of the charger's name as a temporary placeholder until final icon assets are provided in this folder.
