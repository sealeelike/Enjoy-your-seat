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

### Core Algorithm

