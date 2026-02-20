# Olympic 100m Winners Race (1988–2024)

Fantasy race pitting all 10 Olympic 100m gold medalists against each other in a single scene.

## Runners

| Lane | Year | City | Winner | Country | Time | Rank |
|------|------|------|--------|---------|------|------|
| 1 | 1988 | Seoul | Carl Lewis | USA | 9.92 | #9 |
| 2 | 1992 | Barcelona | Linford Christie | GBR | 9.96 | #10 |
| 3 | 1996 | Atlanta | Donovan Bailey | CAN | 9.84 | #6 |
| 4 | 2000 | Sydney | Maurice Greene | USA | 9.87 | #8 |
| 5 | 2004 | Athens | Justin Gatlin | USA | 9.85 | #7 |
| 6 | 2008 | Beijing | Usain Bolt | JAM | 9.69 | #2 |
| 7 | 2012 | London | Usain Bolt | JAM | 9.63 | #1 |
| 8 | 2016 | Rio | Usain Bolt | JAM | 9.81 | #5 |
| 9 | 2020 | Tokyo | Marcell Jacobs | ITA | 9.80 | #4 |
| 10 | 2024 | Paris | Noah Lyles | USA | 9.79 | #3 |

## Run

```bash
python showcases/sprint_100m_winners/main.py
```

Output: `showcases/sprint_100m_winners/output/sprint_100m_winners.mp4`

## Architecture

- **Single scene** with 10 lanes (no VSceneComposite)
- **PCHIP interpolation** from real 10m split times via `interpolation_dict`
- **Real-time playback** — race portion matches actual race duration (~10s)
- **Placement display** — rank shown next to finish time after each runner crosses

## Dependencies

- scipy (PchipInterpolator)
- svan2d
- Playwright server for MP4 export (`svan2d playwright-server start`)
