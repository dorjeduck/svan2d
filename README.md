# Svan2D

<img src="docs/images/logo_128.svg"
     alt="Svan2D Library Logo"
     style="max-width: 128px; display: block; margin: 10px auto;" />



Svan2D is a Python library for programmatically generating SVG graphics and animations. While Svan2D relies on the excellent [DrawSvg](https://github.com/cduck/drawsvg) for creating the base SVG elements, it features a specialized animation engine built around a clear state and visual element separation. This architecture enables detailed control over transitions, such as attribute-level easing.

The project is currently in alpha and undergoes frequent breaking changes. You’re very welcome to explore it, but please don’t build anything on top of it yet.

## Installation

### From Source (Development)


Clone the repository and install in editable mode:

```bash
git clone https://github.com/yourusername/svan2D.git
cd svan2D
pip install -e .
```

Install the required dependency [DrawSvg](https://github.com/cduck/drawsvg):

```bash
pip install drawsvg
```

### Rasterization

Svan2D offers multiple ways to convert SVG graphics to PNG and PDF formats. Each has different trade-offs in terms of quality, speed, and setup complexity.

* **ConverterType.CAIROSVG**
  - Install: `pip install cairosvg`
  - Fast rendering but may have font rendering limitations.

* **ConverterType.INKSCAPE**
  - Install: Download from [inkscape.org](https://inkscape.org) and ensure it's in your PATH
  - Moderate speed with good quality, though text-on-path features may have issues.

* **ConverterType.PLAYWRIGHT**
  - Install: `pip install playwright` then `playwright install chromium`
  - Most accurate rendering but slowest performance and largest installation size.

* **ConverterType.PLAYWRIGHT_HTTP** (Recommended for high-quality batch rendering)
  - Install: `pip install svan2D[playwright-server]` then `playwright install chromium`
  - Highest quality (same as PLAYWRIGHT), runs as background service
  - Start server: `svan2D playwright-server start`
  - Best for: batch rendering, long-running processes, production workflows
  - See **[PLAYWRIGHT_SERVER.md](docs/PLAYWRIGHT_SERVER.md)** for complete setup guide and features

**Performance Comparison:** See **[benchmark/README.md](benchmark/README.md)** for detailed performance comparisons between all converters. Run `python benchmark/run_benchmark.py` to generate fresh benchmark reports comparing speed, CPU usage, and memory consumption.
  
## 🚀 Quick Start

### 🖼️ Static Scene

In this example we arrange the numbers 1 to 9 in an elliptical layout. The core steps to achieve this are:

1. **Create a scene** - The canvas for your composition
2. **Define states** - Define each number's attributes (text, font, color)
3. **Apply layout** - Add position information to the states using a layout function
4. **Create renderer** - Create renderer for the states
5. **Create visual elements** - Associate each state with a renderer
6. **Add to scene** - Add all elements to the scene
7. **Export** - Export the scene (options: svg,png,pdf)

```python
# (1) Create scene with square dimensions and defined background color
scene = VScene(width=256, height=192, background=Color("#000017"))

# (2) Define text states for each number with consistent styling
states = [
    TextState(
        text=str(num),
        font_family="Courier New",
        font_size=20,
        fill_color=Color("#FDBE02"),
    )
    for num in range(1, 10)
]

# (3) Arrange numbers in an elliptical layout
states_layout = layout.ellipse(
    states,
    rx=96,
    ry=64,
)

# (4) Create a text renderer for all numbers
renderer = TextRenderer()

# (5) Create visual elements from states
elements = [
    VElement(
        renderer=renderer,
        state=state,
    )
    for state in states_layout
]

# (6) Add all elements to the scene
scene.add_elements(elements)

# (7) Export to PNG 
exporter = VSceneExporter(
    scene=scene,
    converter=ConverterType.PLAYWRIGHT,
    output_dir="output/",
)

# Export to SVG and PNG
exporter.export(
    filename="01_ellipse_layout", formats=["svg", "png"], png_width_px=1024
)
```

*Complete code*: [01_ellipse_layout.py](./examples/01_ellipse_layout.py)

![](docs/images/01_ellipse_layout.png)

Why the complexity? While this process may seem overly complicated for rendering a static image, the separation of state and visual representation is fundamental to Svan2D’s design. The following chapters explore the rationale behind this architecture.


### 🖌️ Custom renderer

Every `State` in Svan2D is associated with a default renderer and in regular use cases, you can omit specifying the renderer when creating `VElements`. In the previous example, the following implementation would have been sufficient, as `TextRenderer` is the default renderer for `TextState`:

```python
elements = [
    VElement(state=state)
    for state in states_layout
]
``` 

Nevertheless custom renderer for states open a wide range of possibilites. See the following code snippet for a basic custom renderer implementation which draws two circles for one circle state. 

```python
class CustomCircleRenderer(CircleRenderer):

    # renderer in Svan2D return drawsvg DrawingElements
    def render(
        self, state: "CircleState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Group:

        s1 = replace(state, x=state.x - state.radius)

        s2 = replace(
            state,
            x=state.x + state.radius,
            opacity=state.opacity / 2,
        )

        g = dw.Group()

        for s in [s1, s2]:
            g.append(super().render(s, drawing))

        return g
...

# create one circle state
circle_state = CircleState(radius=42, fill_color=Color("#FDBE02"))

# glue state to the custom circle renderer
custom_circle_element = VElement(renderer=CustomCircleRenderer(), state=circle_state)

# Add element to the scene
scene.add_element(custom_circle_element)

...
```
*Complete code*: [custom_renderer.py](./examples/custom_renderer.py)

![](docs/images/custom_renderer.png)


### 🎬 Animation: State Interpolation

Svan2D animations are driven by state interpolation (tweening), where every element transitions between defined sets of state.

To animate the scene of our initial example, we'll now define a transition of the numbers from a start state (centered in the scene) to an end state (its position on the previously defined elliptical layout).

The key distinction here is that each `VElement` is now defined as a combination of the `TextRenderer` and a pair of start and end states.

```python
# Create the scene 
scene = VScene(width=256, height=192, background=Color("#000017"))

# Create text states for each number with consistent styling
# These states will be the starting point of the animation
start_states = [
    TextState(
        center = Point2D(),
        text=str(num),
        font_family="Courier New",
        font_size=20,
        fill_color=Color("#FDBE02"),
    )
    for num in range(1, 10)
]

# Arrange the numbers in an elliptical layout for the end states
end_states = layout.ellipse(
    start_states,
    rx=96,
    ry=64,
)

# Create a text renderer for all numbers
renderer = TextRenderer()

# Create visual elements from states by
# pairing each start state with its corresponding end state
elements = [
    VElement(
        renderer=renderer,
        keystates=states,
    )
    for states in zip(start_states, end_states)
]

# Add all elements to the scene
scene.add_elements(elements)

# Export to MP4 
exporter = VSceneExporter(
    scene=scene,
    converter=ConverterType.PLAYWRIGHT,
    output_dir="output/",
)

exporter.to_mp4(
    filename="number_animation",
    total_frames=60,
    framerate=30,
    png_width_px=1024,
)
```

*Complete code*: [02_simple_animation.py](./examples/02_simple_animation.py)

![](docs/videos/02_simple_animation.gif)


### Advanced Animation Control

While this example uses a simple two-state interpolation, Svan2D's animation engine supports fine grained timing control:

* **Multi-keystate sequencing** — Control timing with explicit frame time values for detailed animation sequences. See [SVG Circus - timed keystates](https://svan2D.wectar.com/circus/timed-keystates/)

* **Per-attribute easing** — Apply different easing functions (ease-in, ease-out, bezier curves etc) to individual attributes for nuanced motion control. See [SVG Circus - Easing Variety](https://svan2D.wectar.com/circus/easing-variety/)

* **Segment Easing** - Customize easing between keystates. See [SVG Circus - Segment Easing](https://svan2D.wectar.com/circus/segment-easing/)

* **Attribute Keystates** - Apply attribute transitions beyond the main keystates - See [SVG Circus - Attribute Keystates](https://svan2D.wectar.com/circus/attribute-keystates/)

## 📓 Jupyter Notebook Support

Svan2D provides comprehensive support for Jupyter notebooks with static scene display, interactive animation preview (grid and navigator layouts), and MP4 export. Perfect for fast iteration and testing!

See **[docs/JUPYTER_SUPPORT.md](docs/JUPYTER_SUPPORT.md)** for complete documentation and examples.

## 🔧 Development Server

For rapid animation development outside Jupyter, Svan2D includes a development server with live browser preview and automatic hot-reload. Edit your Python animation code, save the file, and watch the browser update instantly—no manual refresh needed.

```bash
# Install dev server dependencies
pip install svan2D[devserver]

# Start server (defaults: 20 frames @ 10 FPS)
svan2D serve my_animation.py

# Smooth animation (60 frames @ 30 FPS)
svan2D serve my_animation.py --frames 60 --fps 30
```

The server watches your animation file for changes and automatically reloads the preview in your browser. Syntax and runtime errors are displayed gracefully without crashing the server.

**Export directly from the browser:**
- **MP4**: Professional video export with ffmpeg
- **GIF**: Lightweight animated format for web sharing
- **HTML**: Self-contained interactive file for website embedding

Just click the export button, configure settings, and download when ready - all while the server keeps running.

See **[DEVSERVER.md](docs/DEVSERVER.md)** for complete documentation, CLI options, and advanced features.

## ⚙️ Configuration

Svan2D supports TOML-based configuration for customizing default values. Create a `svan2D.toml` file in your project directory to set scene dimensions, colors, logging levels, and more. For a complete documentation, see **[CONFIG.md](docs/CONFIG.md)**.

## SVG Circus

Rather than writing full-fledged documentation for Svan2D at this early stage of development, we’re focusing on building an evolving collection of examples. SVG Circus is meant to highlight Svan2D’s capabilities and to give users a hands-on way to explore what it can do — complete with the Python source code used to generate and animate each SVG.
See [https://svan2D.wectar.com/](https://svan2D.wectar.com/).

<a href="https://svan2D.wectar.com/">
<img src="docs/images/svg_circus.png"
     alt="SVG Circus"
     style="width: 50%; margin: 10px auto;" />
</a>

## Contribution

Svan2D is still in an early stage and has so far been developed primarily to support the needs of a specific project. That said, it was always intended to evolve into a general-purpose library. We deeply appreciate your feedback and would love to hear your ideas for improving Svan2D — be it bug reports, feature requests, pull requests, or anything else you’d like to share.

## Changelog

See [CHANGELOG.md](docs/CHANGELOG.md) for version history.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
