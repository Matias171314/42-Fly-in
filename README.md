*This project has been created as part of the 42 curriculum by mvasquez.*

# Fly-in

## Description

A Python 3.10+ drone-routing simulator for the mandatory Fly-in subject v1.6.
It moves an entire fleet from a start hub to an end hub, respecting zone
occupancy, bidirectional connection capacities and two-turn restricted flights.
It includes a strict parser, an interactive map menu and a simple colored terminal
movement log. No graph or pathfinding libraries are used. The supplied
Challenger map can also be selected and uses the same Dijkstra planner.

## Instructions

```sh
make install
source .venv/bin/activate
python3 main.py /absolute/path/to/map.txt

make run                                      # choose a map interactively
make run MAP=maps/hard/02_capacity_hell.txt
make debug MAP=maps/easy/01_linear_path.txt
make lint
make lint-strict
make clean                                    # remove bytecode and caches
make clean-venv                               # delete the virtual environment
```

`make clean` removes project bytecode and caches while keeping `.venv`.
`make clean-venv` deletes `.venv`; recreate it with `make install`.
The lint targets explicitly exclude `.venv` from flake8. Additional command-line
options can be passed with `ARGS`, for example:

```sh
make run MAP=maps/easy/01_linear_path.txt ARGS="--visual"
```

After `make install`, activate the virtual environment with
`source .venv/bin/activate`. Then run from the repository root, using either
an absolute or a relative map path:

```sh
python3 main.py                      # menu, including custom map paths
python3 main.py maps/easy/01_linear_path.txt --visual
python3 main.py maps/hard/03_ultimate_challenge.txt
python3 main.py maps/medium/02_circular_loop.txt
```

The program uses one planner: Dijkstra with per-turn reservations. It finds an
earliest arrival for each drone given the routes already planned, then reserves
that route before planning the next drone. It does not guarantee a globally
minimum last-delivery turn. Ctrl+C cancels planning or playback cleanly.

The optional `--visual` flag enables colors for movements and the menu.
Without `--visual`, output stays in the plain subject format.
`parse_arguments()` defines the arguments,
while `main()` selects the map and coordinates the simulation. Menu prompts
and errors go to stderr, and stdout contains only
movement lines:

```sh
python3 main.py maps/easy/01_linear_path.txt > moves.txt
```

The menu works from any working directory. It lists the nine mandatory maps and the optional Challenger map,
accepts `p` for a custom path and `q` to quit. EOF also exits cleanly.

## Project structure

```text
main.py                         # main(), arguments and coordination
src/
  map_parser.py                 # syntax and network validation
  network.py                    # typed Zone, Link, Network and Step models
  planning/
    reservation_router.py       # Dijkstra with per-turn reservations
  presentation/
    color_palette.py            # CSS names and ANSI RGB colors
    map_menu.py                 # supplied-map and custom-path selection
    movement_renderer.py        # one movement line per turn
maps/                           # supplied input files
Makefile
requirements.txt
```

Classes that store data use explicit `__init__` constructors. Methods have
typed parameters on separate lines and short docstrings. The parser, models, routing and display classes
live in `src/`. The root
`main.py` defines `main()`, which reads arguments and coordinates the simulation.

## Parser

The parser uses string operations (`partition`, `split`, `startswith`,
`endswith` and digit checks), without regular expressions.

The first nonempty, noncomment definition must be `nb_drones: <positive_integer>`.
Exactly one start and end are required. Names are unique and cannot contain
dashes or whitespace; punctuation is supported. Coordinates
are signed decimal integers; the subject does not require unique coordinates.
Connections must reference previously declared zones, and `a-b` duplicates
`b-a`. Self-connections are accepted because the subject does not prohibit them.

Metadata order is arbitrary. Unknown tags, duplicate tags, malformed brackets,
invalid zone types and nonpositive regular-zone/link capacities are rejected.
Start/end `max_drones` metadata is ignored, as required by the subject. Arbitrary
single-word colors are accepted. `#` introduces comments. Blocked endpoints are
rejected because no valid delivery route can use a blocked zone.

Parsing errors report a line and cause; missing definitions report end of file.
I/O errors and disconnected endpoints produce a clear error
without a traceback. The entry point calls `main()` directly, so its returned
numbers are not used as process exit codes. Invalid CLI arguments use exit
status 2; Ctrl+C displays an interruption message. There is no artificial fleet-count limit, although available
memory and computation time remain practical limits.

## Algorithm and implementation strategy

### Dijkstra with reservations

Dijkstra explores routes in increasing travel time. Here a state is `(zone,
turn)`, because a zone may be occupied now and free later. A Python `heapq`
priority queue always extracts the state with the earliest arrival time.

For every drone:

1. Begin at `(start, 0)`.
2. Extract the earliest state from the queue.
3. Try each adjacent zone and the option of waiting in the current zone.
4. Normal and priority destinations cost one turn; restricted destinations
   cost two. Blocked zones are never considered.
5. Check the destination's free capacity at the arrival turn and the shared
   connection capacity throughout the movement.
6. Once the end is reached, reconstruct the route and reserve its zone and
   connection slots before planning the next drone.

Although routes are planned one drone at a time, they execute concurrently.
A reservation is just a counter: for example, `(roof, 3) = 1` means one drone
occupies `roof` after turn 3. Connections use an undirected key so both directions
share their capacity. Departures free zone capacity during the same turn.
Restricted moves reserve both connection turns and their destination arrival;
a drone cannot wait on a connection. A drone may wait at a zone if needed.

When arrival times tie, the planner prefers routes with fewer entries into
non-priority zones. Priority never changes the actual one-turn travel duration.
The parser checks reachability first. The search horizon extends beyond the
last scheduled arrival by twice the zone count, leaving enough time to wait at
start until earlier drones finish and then follow a simple accessible path.

This is a greedy fleet strategy: earlier routes are not changed for later
drones. Dijkstra finds the earliest individual arrival given the reservations,
but that does not imply the fewest turns for the fleet as a whole. It meets the
supplied mandatory map performance targets using only standard-library
containers and a priority queue.

For N drones, V zones, E connections and horizon H, worst-case time is
O(N H (V + E) log(V H)); temporary search storage is O(V H), plus stored routes
and sparse reservations. Routes are computed once before visual playback.
There are no graph libraries, flow solvers or heuristic distance functions.

## Visual representation

Each turn prints exactly one line of space-separated `D<ID>-destination` tokens.
Colors use the destination zone's map color; a token naming a connection is cyan.
Output contains only movement tokens, with one line per turn.
`color_palette.py` uses `webcolors` to convert CSS color names to RGB values
and ANSI RGB escape codes to display them in terminals with true color support.
Each colored token ends with `\033[0m` to reset the terminal.
`rainbow` cycles through seven colors, one per character. Other unknown
single-word names remain valid and use white.
Colors never affect routing.

The Makefile excludes `.venv` from flake8 directly; no separate configuration
file is needed. `webcolors` is the runtime dependency; `flake8` and `mypy`
are development tools required by the subject. The strict mypy target disables
only `import-untyped` because `webcolors` does not ship type annotations;
project code is still checked in strict mode.

### External browser visualizer

[Fly-in Visualizer 42](https://fly-in-visualizer-42.vercel.app/) by
[Youssefelhaouil](https://github.com/Youssefelhaouil/FLY_IN_VISUALIZER_42) is an
external replay tool for maps and movement logs. To inspect this program's output:

```sh
python3 main.py maps/medium/02_circular_loop.txt > /tmp/fly-in-moves.txt
```

1. Open the linked visualizer and expand its configuration inputs.
2. Paste the original map into the map input and `/tmp/fly-in-moves.txt` into
   the movement-log input.
3. Apply the inputs, then use playback or single-step controls.

The tool recognizes both zone arrivals (`D1-goal`) and restricted transit
(`D1-source-target`). It is a separate project and is not part of this submission.
Its parser is more permissive and its replay skips empty lines, so it should not
be used as the reference for parser correctness or idle-turn timing. The
project's independent validation preserves every turn.

## Example input and expected output

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: middle 1 0 [color=blue]
end_hub: goal 2 0 [color=yellow]
connection: start-middle
connection: middle-goal
```

```text
D1-middle
D1-goal D2-middle
D2-goal
```

Each stdout line is one turn. Waiting drones are omitted. For a restricted
arrival, `D1-source-target` denotes the first transit turn; `D1-target` must
follow on the next turn. Empty lines represent turns with no movements.

## Validation

The review used an independent replay checker for the actual emitted movement
log, checking adjacency, occupancy, shared link capacities, exact restricted
arrival timing and complete delivery. The following table compares the subject
v1.6 reference targets with the current program's actual stdout line counts.
Each line represents one simulation turn, including any idle turns.

| Level | Map | Subject target (turns) | My output (turns) |
| --- | --- | ---: | ---: |
| Easy | Linear path | ≤ 6 | 4 |
| Easy | Simple fork | ≤ 8 | 4 |
| Easy | Basic capacity | ≤ 6 | 4 |
| Medium | Dead end trap | ≤ 12 | 8 |
| Medium | Circular loop | ≤ 15 | 15 |
| Medium | Priority puzzle | ≤ 12 | 7 |
| Hard | Maze nightmare | ≤ 30 | 13 |
| Hard | Capacity hell | ≤ 35 | 16 |
| Hard | Ultimate challenge | ≤ 45 | 26 |
| Challenger | The impossible dream | < 45 (optional) | 43 |

All nine mandatory maps meet their individual reference targets. The optional
Challenger reference record is 45 turns; the same Dijkstra planner finishes in
43 turns. These results describe the supplied maps and do not establish global
optimality for arbitrary networks.

To reproduce a count:

```sh
python3 main.py maps/challenger/01_the_impossible_dream.txt | wc -l
# 43
```

The scheduler was also replayed on 70 seeded small random networks, including
restricted end zones. An independent exhaustive joint-state BFS supplies an
optimal lower bound for comparison; single-drone routes match it. Multi-drone
schedules are checked for validity without claiming global optimality. A known
three-drone example takes 5 turns with this scheduler versus an optimum of 4,
which illustrates the tradeoff of keeping the algorithm simple.
Additional cases exercise parser
acceptance/rejection, congestion, two-turn restricted arrivals, repeated
planning, menu input, EOF, invalid paths, colors and CLI arguments.

The parser and output review also checked:

- All 1,296 combinations in a bounded three-zone family: link absence/capacity,
  internal-zone type/capacity, normal/restricted goal and fleet sizes 1–3.
  Exactly 1,008 cases produced valid schedules; 288
  unreachable maps were rejected during parsing.
- 39 comment, whitespace and metadata-order combinations. Commented definitions
  cannot supply a missing real definition. Invalid text inside comments is ignored.
- 45 malformed or inconsistent maps through the actual CLI. Each returned status
  0 with the direct `main()` entry point, an explanatory error on stderr,
  no traceback and no partial movement output.
- 2,000 deterministic mutation inputs: 47 coherent accepted maps and 1,953 clear
  rejections, with no unexpected exceptions. Accepted practical fleets were replayed.

This is exhaustive within the stated finite families, not a claim to enumerate
all possible map files. Dead ends, cycles, isolated optional zones and repeated
coordinates are valid when an accessible start-to-end route still exists. A
missing route or a route available only through blocked zones is rejected.

`make lint` and `make lint-strict` check flake8 and mypy. Review programs are
kept outside the submission, following the subject's testing guidance. These
checks are based on the supplied subject; no unavailable correction sheet is
assumed.

## Resources

- [Python heap queues](https://docs.python.org/3/library/heapq.html)
- [Python classes](https://docs.python.org/3/tutorial/classes.html)
- Dijkstra, E. W. (1959), *A note on two problems in connexion with graphs*.
- Silver, D. (2005), *Cooperative Pathfinding*, AIIDE.
- Supplied Fly-in subject v1.6 and map archive.

AI was used to interpret requirements, implement and review the parser, models,
planners, terminal menu and movement renderer, build configuration and documentation, and create
independent validation programs.
