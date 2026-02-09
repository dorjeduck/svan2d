# Fourier Epicycles

Draws a shape using rotating circles (epicycles) derived from the Discrete Fourier Transform. Each circle's radius and speed correspond to a frequency component. A trail traces the tip of the outermost circle, progressively drawing the target shape over one full revolution.

## Run

```bash
python showcases/fourier/epicycles/main.py
```

## Config

Edit `config.toml` to change the shape (`heart`, `star`, `circle`, `square`, `infinity`), number of epicycles, colors, and export settings.
