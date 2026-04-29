from mermaid import Mermaid

mermaid_code = """
flowchart TD
    A([开始]) --> B[识别数据源与增量范围]
    B --> C[抽取原始数据到 ODS]
    C --> D[执行字段映射与类型转换]
    D --> E[去重、空值处理、编码统一]
    E --> F{质量校验通过？}
    F -- 否 --> G[记录异常并触发重试]
    G --> Z([结束])
    F -- 是 --> H[加载到 DWD 明细层]
    H --> I[按主题聚合形成 DWS]
    I --> J[生成 ADS 报表数据集]
    J --> K[刷新报表与 AI 问数底座]
    K --> L[写入执行日志与监控指标]
    L --> Z([结束])
"""

m = Mermaid(mermaid_code)
m.to_png('/Users/huangqiang/projects/erp-bi-system/docs/figures/chapter4/图 4-4-ETL 流程图.png')
print("流程图已生成！")
