# Enjoy-your-seat

> [!IMPORTANT]
> **Important Notice**
>
> This repository contains only Python scripts intended for algorithmic research and client-side tool development. **It does not host, store, or distribute any proprietary data or internal information from the university.**
>
> All data acquisition (e.g., room availability) is performed locally on the user's machine, using their own legitimate credentials. The resulting data files are explicitly excluded from this repository via `.gitignore`.
>
> This project is provided "AS IS" under the [MIT License](LICENSE). The developer assumes no responsibility for how you use these scripts or for the data you acquire. Please ensure that your use of this tool complies with all relevant local and university regulations.


<p align="center">English | <a href="./README-hans.md">中文</a></p>

## Introduction

Tired of wandering the XJTLU campus looking for an empty classroom? `Enjoy-your-seat` is a smart study room finder that automates the search for you.

Based on your location and desired study time, it scans the university's [booking system](https://mrbs.xjtlu.edu.cn/) to find the best available rooms. Its core algorithm is designed to create optimized plans with **zero or minimal room changes**, perfect for long, uninterrupted study sessions.

* **Find a room right now, right here:** Instantly see available classrooms in nearby buildings.
* **Plan for the whole day:** Get a schedule with the fewest possible room changes.
* **Filter for your needs:** Find rooms with specific equipment like large screens or online meeting setups.

Stop searching and start studying. Let the app find your next seat.


## Table of Contents

* [How it works?](#how-it-works)
    * [Effect Preview](#effect-preview)
    * [Rough logic](#rough-logic)
    * [Usage Demonstration (concept)](#usage-demonstration-concept)
    * [How the app determines the appropriate area?](#how-the-app-determines-the-appropriate-area)
    * [How are room plans generated?](#how-are-room-plans-generated)
* [Advantages and disadvantages of this algorithm](#advantages-and-disadvantages-of-this-algorithm)
* [How to Use](#how-to-use)
* [Todo list](#todo-list)

### Effect Preview
![](Schematic%20diagram.jpg)


## How it works

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

(arrows indicate user input field)
### How the app determines the appropriate area？

The relevant information is hardcoded into the program, that is, once the relative coordinates input by the user are read, a set of pre-made area selection solutions will be returned.

### How are room plans generated?

> the initial time-based matching logic has been deprecated, you can find it in V0.0.0 release.

_Simply put, when a time period cannot be covered in one go, the algorithm employs a recursive "meet-in-the-middle" strategy: using the beginning and end as anchor points, it finds the time block closest to the other endpoint. If there's still a gap, it tries again._

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

