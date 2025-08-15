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
