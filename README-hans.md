# Enjoy-your-seat

简体中文/[English](README.md)

本应用旨在帮助 XJTLU 的学生找到附近可供栖身的自习空间。

该程序将结合校园地图与 [mrbs](https://mrbs.xjtlu.edu.cn/) 网站的数据，为用户筛选出距离最近的可用教室。用户只需在地图上点击自己所在的位置，算法便会为其推荐合适的自习地点。

## 目录

* [简介](#简介)
    * [效果预览](#效果预览)
    * [大致逻辑](#大致逻辑)
    * [使用演示（概念图）](#使用演示概念图)
    * [程序如何根据位置给出备选教室？](#程序如何根据位置给出备选教室)
    * [教室方案是如何生成的？](#教室方案是如何生成的)
* [该算法的优缺点](#该算法的优缺点)
* [如何使用](#如何使用)
* [待办事项](#待办事项)

### 效果预览

![](Schematic%20diagram.jpg)

## 简介

### 大致逻辑

```mermaid
flowchart TD
A[用户在地图上选中当前位置] --> B[应用识别并定位附近的建筑物*]
B --> C[拉取相关房间信息<br>（若部署在学校官方服务器上，则可直接使用内置数据）]
C --> D[用户选择开始、结束时间，以及额外的设施要求]
D --> E[呈现多种方案*<br>（不同方案各有优势，如设施丰富、座位多、举例近……但选择权留给用户）]
E --> F[附上相关的设施与服务信息]
```

### 使用演示（概念图）

![](concept-demo.png)

### 程序如何根据位置给出备选教室？

相关信息被硬编码在程序中。也就是说，一旦程序读取到用户输入的相对坐标，就会返回一组预设好的区域选择方案。

### 教室方案是如何生成的？

> 最初基于时间块的匹配逻辑已被弃用，你可以在 V0.0.0 版本中找到它。

```mermaid
flowchart TD
    %% ============= 核心算法流程图 ============= %%
    A([开始]) --> B[读取配置参数<br/>area_id, time_start, time_end,<br/>设施要求等]
    B --> C[读取 ready_data_xxx 目录的 JSON 向量数据]
    C --> D[过滤: 仅保留指定区域ID的向量]
    D --> E[设施过滤 facility_check]
    E --> F[覆盖性预检<br/>是否所有房间加在一起能覆盖所需时间段?]
    F -- 否 --> Z1([输出提示: 无法满足要求<br/>结束])
    F -- 是 --> G[剔除被完全包含的小chunk<br/>preprocess_2]

    G --> H[0_change: 是否存在单个chunk覆盖整个需求?]
    H -- 是 --> Z0([输出所有可行 0-change 向量<br/>一次满足需求 结束])
    H -- 否 --> I[1_change: 两头夹击选取<br/>左: 覆盖 start 的 chunk 中最晚结束的<br/>右: 覆盖 end 的 chunk 中最早开始的]
    I --> J{两段是否有重叠时段?}
    J -- 是 --> Z2([输出 1 次换房方案<br/>含切换窗口 结束])
    J -- 否 --> K[2_changes: 在左、右段之间的 gap 寻找中间段 coverage]
    
    K --> L{中间段是否存在单个chunk覆盖gap?}
    L -- 是 --> Z3([输出 2 次换房方案<br/>最大化切换窗口 结束])
    L -- 否 --> M{是否允许三次换房?}
    M -- 否 --> Z4([输出提示: 找不到方案<br/>结束])
    M -- 是 --> N[在gap区间内运行1_change<br/>得到middle_left 和 middle_right]
    N --> O{middle_left与middle_right有重叠?}
    O -- 是 --> Z5([输出 3 次换房方案 结束])
    O -- 否 --> Z4

    %% 样式美化
    style A fill:#3e8ef7,stroke:#fff,stroke-width:2px,color:#fff
    style Z1 fill:#ef476f,stroke:#fff,stroke-width:2px,color:#fff
    style Z0 fill:#06d6a0,stroke:#fff,stroke-width:2px,color:#fff
    style Z2 fill:#ffd166,stroke:#333,stroke-width:1px
    style Z3 fill:#ffd166,stroke:#333,stroke-width:1px
    style Z4 fill:#ef476f,stroke:#fff,stroke-width:2px,color:#fff
    style Z5 fill:#ffd166,stroke:#333,stroke-width:1px

```

## 该算法的优缺点

优点

  - 最少的教室更换次数
  - 最长的重叠时间（为用户提供更自由的更换教室时机）

缺点
  - 还没想好

## 如何使用

请参阅 [指南](quick-start-hans.md)

## 待办事项

  - [ ] 提供更细粒度的建议，不仅限于整个校园，例如可以精确到基础楼内部
  - [ ] 设施筛选功能
  - [ ] 创建区域ID (areaID) 与设施的映射表，以避免通过遍历和检查来完成用户的筛选要求。
