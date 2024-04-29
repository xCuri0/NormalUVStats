# Normal & UV Statistics

![statistics.png]()

Adds a new overlay that displays vertex normal and UV statistics while maintaining compatibility with Blender's statistics overlay. It can be useful when optimizing meshes for game engines that have normal/uv count limitations.

Based on [BetterStats](https://github.com/ssnd292/BetterStats) by [@ssnd292](https://github.com/ssnd292)

After installing, it can be activated and deactivated in the Viewport Overlays. You can also adjust the overlay color in add-on preferences.

![overlays.png]()

Fully compatible with DPI/resolution scaling and panel/window resizing. Enabling on startup and loading files has also been fixed.

Performance has been improved through use of a seperate thread for Normal and UV calculations. Total Normal and UV count is also displayed now and is calculated on startup or when selecting all objects, you can disable this in add-on preferences if it causes performance issues.

Edit Mode still won't show Normal & UV counts, same as in the original BetterStats.

**Performing complex operations such as changing Decimate slider quickly may cause Blender to crash. For this reason it's recommended to leave this overlay off unless required**
