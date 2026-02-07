# Svan2D

<img src="docs/images/logo_128.svg"
     alt="Svan2D Library Logo"
     style="max-width: 128px; display: block; margin: 10px auto;" />



Svan2D is a Python library for programmatically generating SVG graphics and animations. While Svan2D relies on the excellent [DrawSvg](https://github.com/cduck/drawsvg) for creating the base SVG elements, it features a specialized animation engine built around a clear state and visual element separation. This architecture enables detailed control over transitions, such as attribute-level easing.

> ⚠️ **Alpha Status:** This project undergoes frequent breaking changes. You're welcome to explore, but please don't build anything on top of it yet.

## Installation

```bash
git clone https://github.com/yourusername/svan2d.git
cd svan2d
pip install -e .
```

### Rasterization

| Converter | Install | Notes |
|-----------|---------|-------|
| `PLAYWRIGHT_HTTP` ⭐ | `pip install svan2d[playwright-server]` + `playwright install chromium` | Best quality, fast |
| `CAIROSVG` | `pip install cairosvg` | Fastest |
| `INKSCAPE` | [inkscape.org](https://inkscape.org) | Good quality |
| `PLAYWRIGHT` | `pip install playwright` | Slow, use HTTP instead |

See [PLAYWRIGHT_SERVER.md](docs/PLAYWRIGHT_SERVER.md) for setup.
  
## 🚀 Quick Start

### 🖼️ Static Scene

Numbers arranged in an elliptical layout:

```python
...

scene = VScene(width=256, height=192, background=Color("#000017"))

# Create text states
states = [
    TextState(text=str(n), font_family="Courier New", font_size=20, fill_color=Color("#FDBE02"))
    for n in range(1, 10)
]

# Apply ellipse layout
states = layout.ellipse(states, rx=96, ry=64)

# Create elements and add to scene
elements = [VElement(renderer=TextRenderer(), state=s) for s in states]
scene = scene.add_elements(elements)

# Export
exporter = VSceneExporter(scene, converter=ConverterType.PLAYWRIGHT, output_dir="output/")
exporter.export(filename="01_ellipse_layout", formats=["svg", "png"], png_width_px=1024)
```

*Full example*: [01_ellipse_layout.py](./examples/01_ellipse_layout.py)

![](docs/images/01_ellipse_layout.png)


### 🖌️ Custom renderer

Every `State` in Svan2D is associated with a default renderer and in regular use cases, you can omit specifying the renderer when creating `VElements`. Nevertheless custom renderer for states open a wide range of possibilites. See the following code snippet for a basic custom renderer implementation which draws two circles for one circle state. 

```python
class CustomCircleRenderer(CircleRenderer):

    # renderer in Svan2D return drawsvg DrawingElements
    def render(
        self, state: "CircleState", drawing: Optional[dw.Drawing] = None
    ) -> dw.Group:

        s1 = replace(
            state,
            pos=Point2D(
                state.pos.x - state.radius,
                state.pos.y
            )
        )

        s2 = replace(
            state,
            pos=Point2D(
                state.pos.x + state.radius, 
                state.pos.y
            ),
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

In Svan2D, animation is defined via states which are interpolated. Here the numbers transition from center to their ellipse positions:

```python
...

scene = VScene(width=256, height=192, background=Color("#000017"))

# Start states (centered)
start_states = [
    TextState(
            pos=Point2D(0, 0),  # centered 
            text=str(num),
            font_family="Courier New",
            font_size=20,
            fill_color=Color("#FDBE02"),
        )
    for n in range(1, 10)
]

# End states (ellipse layout, changes pos)
end_states = layout.ellipse(start_states, rx=96, ry=64)

# Create a text renderer for all numbers
renderer = TextRenderer()

# Create elements with start→end keystates
elements = [
        VElement().renderer(renderer).keystates(states)
        for states in zip(start_states, end_states)
    ]

scene = scene.add_elements(elements)

# Export to MP4
exporter = VSceneExporter(scene, converter=ConverterType.PLAYWRIGHT, output_dir="output/")
exporter.to_mp4(filename="number_animation", total_frames=60, framerate=30, png_width_px=1024)
```

*Full example*: [02_simple_animation.py](./examples/02_simple_animation.py)

![](docs/videos/02_simple_animation.gif)


### Advanced Animation Control

Svan2D offers fine-grained control over animation behavior. See examples at [SVG Circus](https://svan2d.org/).

## 📓 Jupyter Notebook Support

Svan2D provides comprehensive support for Jupyter notebooks with static scene display, interactive animation preview (grid and navigator layouts), and MP4 export. Perfect for fast iteration and testing!

See **[docs/JUPYTER_SUPPORT.md](docs/JUPYTER_SUPPORT.md)** for complete documentation and examples.

## 🔧 Development Server

Live browser preview with hot-reload for rapid animation development.

```bash
pip install svan2d[devserver]
svan2d serve my_animation.py --frames 60 --fps 30
```

See [DEVSERVER.md](docs/DEVSERVER.md) for details.

## ⚙️ Configuration

Svan2D supports TOML-based configuration for customizing default values. Create a `svan2d.toml` file in your project directory to set scene dimensions, colors, logging levels, and more. For a complete documentation, see **[CONFIG.md](docs/CONFIG.md)**.

## SVG Circus

Rather than writing full-fledged documentation for Svan2D at this early stage of development, we’re focusing on building an evolving collection of examples. SVG Circus is meant to highlight Svan2D’s capabilities and to give users a hands-on way to explore what it can do — complete with the Python source code used to generate and animate each SVG.
See [https://svan2d.org/](https://svan2d.org/).

<a href="https://svan2d.org/">
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
