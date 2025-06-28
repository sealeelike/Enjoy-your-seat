# Enjoy-your-seat
This app helps XJTLU students find empty seats near them for self-study.

The program will integrate the campus map and the [mrbs](https://mrbs.xjtlu.edu.cn/) website to select the nearest available classroom for users. Users only need to click on their location on the map, and the algorithm will recommend a suitable place for users.

## Table of Contents (Optional)

<!-- Use this if your README is long to help users navigate. -->

以下分别为中文与英文两份 Mermaid 流程图代码。  
将代码复制到支持 Mermaid 的编辑器/Markdown 环境中即可渲染可视化流程图。



```mermaid
flowchart TD
    A[Start] --> B[Select desired stay time]
    B --> C[Mark current location on map]
    C --> D[Identify nearby buildings]
    D --> E[Fetch classroom information from website]
    E --> F{Is user inside a building?}
    F -- Yes --> G[Fetch room list of current building only]
    F -- No  --> H[Fetch room lists of nearby buildings]
    G --> I[Aggregate all room data]
    H --> I
    I --> J[Filter rooms that fit selected time slot]
    J --> K[Sort: buildings near→far, floors low→high]
    K --> L[Display recommendations to user<br/>(facilities & services optional)]
    L --> M[End]
```



## Technologies Used (Optional)

<!-- List the main technologies, languages, and frameworks used in your project. -->

- [Technology 1] - [Version]
- [Technology 2] - [Version]
- [Technology 3] - [Version]

## Requirements

<!-- Specify any software or hardware prerequisites needed to run your project. -->

- [Requirement 1]
- [Requirement 2]

## Installation

<!-- Provide step-by-step instructions on how to install and set up the project locally. Include code snippets where helpful. -->

```bash
# Example installation command
npm install [your-package]
