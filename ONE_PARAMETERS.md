# ONE Simulator Parameters Reference

This document maps ONE simulator configuration parameters to OppNDA GUI fields.

## Quick Navigation

- [Scenario Settings](#scenario-settings)
- [Interface Settings](#interface-settings)
- [Group Settings](#group-settings)
- [Event Settings](#event-settings)
- [Movement Model Settings](#movement-model-settings)
- [Report Settings](#report-settings)
- [Router-Specific Settings](#router-specific-settings)

---

## Scenario Settings

| ONE Parameter | OppNDA Field | Description | Default |
|---------------|--------------|-------------|---------|
| `Scenario.name` | Scenario Name | Unique name for the simulation | `default_scenario` |
| `Scenario.simulateConnections` | Simulate Connections | Enable/disable connection simulation | `true` |
| `Scenario.updateInterval` | Update Interval | Simulation update frequency (seconds) | `0.1` |
| `Scenario.endTime` | End Time | Total simulation duration (seconds) | `43200` (12 hours) |
| `Scenario.nrofHostGroups` | *Auto-calculated* | Number of host groups | *From group list* |

---

## Interface Settings

| ONE Parameter | OppNDA Field | Description | Example |
|---------------|--------------|-------------|---------|
| `[name].type` | Type | Interface class | `SimpleBroadcastInterface` |
| `[name].transmitSpeed` | Transmit Speed | Data transfer rate | `250k`, `10M` |
| `[name].transmitRange` | Transmit Range | Communication range (meters) | `10`, `1000` |

### Available Interface Types

- `SimpleBroadcastInterface` - Basic broadcast interface
- `InterferenceLimitedInterface` - Models radio interference
- `DistanceCapacityInterface` - Distance-based capacity
- `ConnectivityOptimizer` - Optimized connectivity
- `ConnectivityGrid` - Grid-based connectivity

---

## Group Settings

### Common Group Settings

| ONE Parameter | OppNDA Field | Description | Default |
|---------------|--------------|-------------|---------|
| `Group.movementModel` | Movement Model | How nodes move | `ShortestPathMapBasedMovement` |
| `Group.router` | Router | Routing protocol | `EpidemicRouter` |
| `Group.bufferSize` | Buffer Size | Node storage capacity | `5M` |
| `Group.waitTime` | Wait Time | Pause time at destinations | `0, 120` |
| `Group.speed` | Speed | Movement speed range (m/s) | `0.5, 1.5` |
| `Group.msgTtl` | TTL | Message Time-To-Live (minutes) | `300` |
| `Group.nrofHosts` | Number of Hosts | Nodes in group | `40` |
| `Group.nrofInterfaces` | Interface Number | Interfaces per node | `1` |
| `Group.interface1` | Interface | Interface to use | `btInterface` |

### Per-Group Settings

| ONE Parameter | OppNDA Field | Description |
|---------------|--------------|-------------|
| `Group[N].groupID` | Group ID | Group identifier prefix |
| `Group[N].numHosts` | Number of Hosts | Nodes in this group |
| `Group[N].movementModel` | Movement Model | Override common setting |
| `Group[N].routeFile` | Route File | Path file for MapRouteMovement |
| `Group[N].routeType` | Route Type | Route behavior type |
| `Group[N].router` | Router | Override common router |
| `Group[N].activeTimes` | Active Times | When nodes are active |
| `Group[N].msgTtl` | Message TTL | Message lifetime |

---

## Event Settings

| ONE Parameter | OppNDA Field | Description | Default |
|---------------|--------------|-------------|---------|
| `Events.nrof` | *Auto-calculated* | Number of event generators | *From list* |
| `Events[N].class` | Event Class | Event generator type | `MessageEventGenerator` |
| `Events[N].interval` | Creation Interval | Message creation rate (s) | `25, 35` |
| `Events[N].size` | Message Size | Message size range | `500k, 1M` |
| `Events[N].hosts` | Hosts | Source/destination range | `0, 126` |
| `Events[N].prefix` | Prefix | Message ID prefix | `M` |

---

## Movement Model Settings

| ONE Parameter | OppNDA Field | Description | Default |
|---------------|--------------|-------------|---------|
| `MovementModel.rngSeed` | RNG Seed | Random number seed | `1` |
| `MovementModel.worldSize` | World Size | Simulation area (m) | `4500, 3400` |
| `MovementModel.warmup` | Warmup Time | Pre-simulation time (s) | `1000` |

### Map-Based Movement

| ONE Parameter | OppNDA Field | Description |
|---------------|--------------|-------------|
| `MapBasedMovement.nrofMapFiles` | *Auto-calculated* | Number of map files |
| `MapBasedMovement.mapFile[N]` | Map Files | WKT map file paths |

### Available Movement Models

- `RandomWaypoint` - Random destination, random pause
- `RandomWalk` - Random direction changes
- `ShortestPathMapBasedMovement` - Follows map paths
- `MapRouteMovement` - Follows predefined routes
- `StationaryMovement` - Fixed location
- `BusMovement` / `BusTravellerMovement` - Bus system simulation
- `CarMovement` - Vehicle movement
- `WorkingDayMovement` - Daily activity patterns
- *...and more*

---

## Report Settings

| ONE Parameter | OppNDA Field | Description | Default |
|---------------|--------------|-------------|---------|
| `Report.nrofReports` | *Auto-calculated* | Number of reports | *From list* |
| `Report.warmup` | Report Warmup Time | Skip initial period (s) | `0` |
| `Report.reportDir` | Report Directory | Output location | `reports/` |
| `Report.report[N]` | Report Class | Report type to generate | - |

### Available Report Types

OppNDA supports all 36+ ONE simulator report types including:
- `MessageStatsReport` - Overall message statistics
- `MessageDeliveryReport` - Delivery details
- `MessageDelayReport` - Latency measurements
- `ContactTimesReport` - Contact duration analysis
- `BufferOccupancyReport` - Buffer usage over time
- `EnergyLevelReport` - Energy consumption
- *...and more*

---

## Router-Specific Settings

### ProphetRouter

| ONE Parameter | OppNDA Field | Default |
|---------------|--------------|---------|
| `ProphetRouter.secondsInTimeUnit` | Seconds in Time Unit | `30` |

### SprayAndWaitRouter

| ONE Parameter | OppNDA Field | Default |
|---------------|--------------|---------|
| `SprayAndWaitRouter.nrofCopies` | Number of Copies | `6` |
| `SprayAndWaitRouter.binaryMode` | Binary Mode | `true` |

### Available Routers

| Router | Description |
|--------|-------------|
| `EpidemicRouter` | Floods messages to all contacts |
| `ProphetRouter` | Probabilistic routing using delivery predictability |
| `ProphetV2Router` | Enhanced Prophet with aging |
| `SprayAndWaitRouter` | Limited copies with binary or source spray |
| `DirectDeliveryRouter` | Delivers only to final destination |
| `FirstContactRouter` | Forwards to first available contact |
| `MaxPropRouter` | Uses delivery likelihood estimations |
| `PassiveRouter` | Only receives, never forwards |
| `EpidemicOracleRouter` | Epidemic with oracle knowledge |
| `LifeRouter` | Lifetime-based routing |

---

## Optimization Settings

| ONE Parameter | OppNDA Field | Description | Default |
|---------------|--------------|-------------|---------|
| `Optimization.cellSizeMult` | Cell Size Multiplier | Spatial indexing factor | `5` |
| `Optimization.randomizeUpdateOrder` | Randomize Update Order | Random node update order | `true` |

---

## GUI Settings

| ONE Parameter | OppNDA Field | Description | Default |
|---------------|--------------|-------------|---------|
| `GUI.UnderlayImage.fileName` | Overlay Image | Background map image | `data/helsinki_underlay.png` |
| `GUI.UnderlayImage.offset` | Underlay Image Offset | Image position (pixels) | `64, 20` |
| `GUI.UnderlayImage.scale` | Underlay Image Scale | Zoom factor | `4.75` |
| `GUI.UnderlayImage.rotate` | Underlay Image Rotate | Rotation (radians) | `-0.015` |
| `GUI.EventLogPanel.nrofEvents` | Number of Events | Log panel size | `100` |

---

## Batch Run Syntax

ONE simulator supports parameter sweeps using semicolons:

```
Scenario.name = [sim1; sim2; sim3]
Group.router = [EpidemicRouter; ProphetRouter]
MovementModel.rngSeed = [1; 2; 3; 4; 5]
```

In OppNDA:
- **RNG Seed** field supports: `1; 2; 3; 4; 5` format
- **Message TTL** field supports: `100; 200; 300` format
- **Router** Tagify supports multiple selections

---

## Further Resources

- [ONE Simulator GitHub](https://github.com/akeranen/the-one)
- [ONE Simulator Documentation](https://akeranen.github.io/the-one/)
- [Default Settings Reference](https://github.com/akeranen/the-one/blob/master/default_settings.txt)
