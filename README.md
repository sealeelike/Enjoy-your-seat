# Enjoy-your-seat
This app helps XJTLU students find empty seats near them for self-study.

The program will integrate the campus map and the [mrbs](https://mrbs.xjtlu.edu.cn/) website to select the nearest available classroom for users. Users only need to click on their location on the map, and the algorithm will recommend a suitable place for users.

## Introduction

<!-- Use this if your README is long to help users navigate. -->

### Rough logic

```mermaid
flowchart TD
A[User marks current location on the map] --> B[App identifies and locates nearby buildings]
B --> C[Pull relevant room information]
C --> D[User selects length of stay]
D --> E{Is there a room that meets the requirements?}
E -- Yes --> F[Directly recommend a room]
E -- No --> G[Try room combination plan]
F--> H[Multiple plans are presented from near to far buildings and from low to high floors]
G --> H
H --> I[Attach relevant facilities and services]
```

### Core Matchmaking Mechanics

```mermaid
graph TD
subgraph preparation phase
A[Get all room information lists] --> B[Split the available time of each room into unit time blocks, such as 20 minutes] --> C[Merge the same time blocks] -- That is to say --> D[Each time block may wear several room number labels] --> E[Time blocks can be connected to cover a complete day]
end

subgraph processing phase
E --> F[Read the user's required time period] --> G[Select time blocks]
G --> H{Find available combinations?}
H -- Yes --> I[Calculate the 'room number difference' for each combination to find the optimal room switching path]
I --> J{The difference is 0}
J -- Yes --> K[The user does not need to change position midway]
J -- No --> L[The user needs to change position midway]
K --> O[The most ideal situation]
L --> M[Recommend the solution with the smallest 'difference' to the user]
H -- No --> N[Inform the user that there is no available solution😭😭😭]
end
```
### Solver for Room combination
- least room change
- longest overlapping period

## Effect Preview
![](Schematic%20diagram.jpg)
