# Normal & UV Statistics

![statistics](https://github.com/xCuri0/NormalUVStats/assets/29529557/32e0961b-7a19-4bc4-8d3f-a72607ca5ec0)

Adds a new overlay that displays vertex normal and UV statistics while maintaining compatibility with Blender's statistics overlay. It can be useful when optimizing meshes for game engines that have normal/uv count limitations.

Compatible with Blender 3.6+ and tested with Blender 4.1. Based on [BetterStats](https://github.com/ssnd292/BetterStats) by [@ssnd292](https://github.com/ssnd292)

Fully compatible with DPI/resolution scaling and panel/window resizing. Enabling on startup and loading files has also been fixed.

After installing, it can be activated and deactivated in the Viewport Overlays. You can also adjust the overlay color in add-on preferences.

![overlays](https://github.com/xCuri0/NormalUVStats/assets/29529557/6add4277-34c2-4ed6-a570-d5f088796a65)

Performance has been improved through use of a seperate thread for Normal and UV calculations. Total Normal and UV count is also displayed now and is calculated on startup or when selecting all objects, you can disable this in add-on preferences if it causes performance issues.

Edit Mode still won't show Normal & UV counts, same as in the original BetterStats.

**Performing complex operations such as changing Decimate slider quickly may cause Blender to crash. For this reason it's recommended to leave this overlay off unless required**
