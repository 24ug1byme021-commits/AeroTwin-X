# data/

- `synthetic/` — reserved for exported synthetic telemetry CSVs (e.g. recorded demo
  runs) and the SQLite database file (`aerotwinx.db`) once persistence is wired up.
  Currently the prototype keeps telemetry history in-memory only
  (`telemetry/streaming.py`'s bounded deque) — nothing is written here yet.
- `scenarios/` — reserved for named, pre-recorded scenario definitions (e.g. a fixed
  sequence of scenario switches for a scripted Demo Mode) if/when Demo Mode is
  extracted from manual scenario-controller clicks into a replayable script.

Nothing in this repository claims or contains real DRDO/UAV engine data. Any file
that appears here in the future must be clearly synthetic and labeled as such.
