# Enjoy-your-seat
This app helps XJTLU students find empty seats near them for self-study.

The program will integrate the campus map and the [mrbs](https://mrbs.xjtlu.edu.cn/) website to select the nearest available classroom for users. Users only need to click on their location on the map, and the algorithm will recommend a suitable place for users.

### Effect Preview
![](Schematic%20diagram.jpg)


## Introduction

<!-- Use this if your README is long to help users navigate. -->

### Rough logic

```mermaid
flowchart TD
A[User marks current location on the map] --> B[App identifies and locates nearby buildings*]
B --> C[Pull relevant room information <br> #40;if not deployed on the school's official server, or it could directly use the built-in data#41;]
C --> D[Users submit start and end times and even additional requests for facilities]
D --> E[Multiple plans are presentedDifferent options are presented.* <br> #40;They may have different advantages, such as rich facilities, large capacity, proximity to the starting point...but the choice is left to the user#41;]
E --> F[Attach relevant facilities and services]
```
### Usage Demonstration (concept)
![](concept-demo.png)

### How the app determines the appropriate area？

The relevant information is hardcoded into the program, that is, once the relative coordinates input by the user are read, a set of pre-made area selection solutions will be returned.

### How are room plans generated?

> the initial time-based matching logic has been deprecated, you can find it in V0.0.0 release.

```mermaid
flowchart TD
    %% ============= Core Algorithm Flow ============= %%
    A([Start]) --> B[Read config parameters<br/>area_id, time_start, time_end,<br/>facility requirements etc.]
    B --> C[Read JSON vector data from ready_data_xxx directory]
    C --> D[Filter: keep only vectors with given area_id]
    D --> E[Facility filter]
    E --> F[Coverage pre-check<br/>Can all rooms combined cover the requested period?]
    F -- No --> Z1([Output: Cannot satisfy requirement<br/>End])
    F -- Yes --> G[Remove chunks completely contained in another<br/>preprocess_2]

    G --> H[0_change: Is there a single chunk covering the whole request?]
    H -- Yes --> Z0([Output all feasible 0-change vectors<br/>One room only, End])
    H -- No --> I[1_change: Two-end attack selection<br/>Left: covers start with latest ending<br/>Right: covers end with earliest starting]
    I --> J{Do the two segments have any overlap in time?}
    J -- Yes --> Z2([Output 1-change solution<br/>with switching window, End])
    J -- No --> K[2_changes: Search middle chunk covering the gap between left and right]
    
    K --> L{Is there a single middle chunk covering the entire gap?}
    L -- Yes --> Z3([Output 2-change solution<br/>Maximize switch overlap, End])
    L -- No --> M{Allow three changes?}
    M -- No --> Z4([Output: No feasible plan<br/>End])
    M -- Yes --> N[Run 1_change within the gap<br/>get middle_left and middle_right]
    N --> O{Do middle_left and middle_right have overlap?}
    O -- Yes --> Z5([Output 3-change solution, End])
    O -- No --> Z4

    %% Styles for clarity
    style A fill:#3e8ef7,stroke:#fff,stroke-width:2px,color:#fff
    style Z1 fill:#ef476f,stroke:#fff,stroke-width:2px,color:#fff
    style Z0 fill:#06d6a0,stroke:#fff,stroke-width:2px,color:#fff
    style Z2 fill:#ffd166,stroke:#333,stroke-width:1px
    style Z3 fill:#ffd166,stroke:#333,stroke-width:1px
    style Z4 fill:#ef476f,stroke:#fff,stroke-width:2px,color:#fff
    style Z5 fill:#ffd166,stroke:#333,stroke-width:1px
```
## Advantages and disadvantages of this algorithm
advantages
- least room change
- longest overlapping period (give users more freedom to decide when to switch)

disadvantages
- ?

## How to Use

please see [this guide](quick-start.md)

## Todo list
- [ ] Provide more granular advice, not just on campus, such as within the Fundation Building
- [ ] facility filter
- [ ] Create a mapping table of areaID and facility to avoid the need to traverse and check to complete user filtering requirements.

