# Jupyter Notebook Support

```python
scene  # Auto-displays inline
```

## Animation Preview

```python
scene.preview_animation(num_frames=10, layout="grid")           # Grid of frames
scene.preview_animation(num_frames=10, layout="grid", scale=0.5) # Smaller
scene.preview_animation(num_frames=20, layout="navigator")       # Click through
```

## Video Export

```python
scene.export("animation.mp4", total_frames=60, framerate=30)
Video("animation.mp4", embed=True, width=400)  # from IPython.display
```
