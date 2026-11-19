# 排球比赛观测数据

主子方向为数据分析与数据应用。俱乐部分析员用记分事件、换人记录、录像标注和球场落点理解比赛。数据仓把官方记分和观察员编码保留为不同证据，产出可复算的回合事实与战术分析结果。可以用完全虚构的一场比赛和几段人工编码样例启动。

这是可运行的最小数据基线，只实现下表列明的能力。观察标注已经转成稳定事件编号和已对齐坐标；不自动分析视频。

| 数据链 | 基线能力 | 离线样例 | 可核验结果 |
|---|---|---|---|
| `touch-evidence` | 保留官方得分，独立判断同一回合的最后触球标注是否一致。 | [输入](examples/touch-evidence.json) | [结果](tests/expected/touch-evidence.json) |
| `lineup-spells` | 将已核对换人记录应用到各次开球，输出被换球员及替补的在场事实。 | [输入](examples/lineup-spells.json) | [结果](tests/expected/lineup-spells.json) |
| `receive-zones` | 用归一化单侧球场横坐标汇总一名接球队员的来球分区，单列未知落点。 | [输入](examples/receive-zones.json) | [结果](tests/expected/receive-zones.json) |
| `setter-choices` | 按预标注接球质量统计二传直接过网、传球和未知的基本计数。 | [输入](examples/setter-choices.json) | [结果](tests/expected/setter-choices.json) |
| `annotation-agreement` | 比对一对观察员按稳定动作编号提供的标注，区分漏标、类别和边界分歧。 | [输入](examples/annotation-agreement.json) | [结果](tests/expected/annotation-agreement.json) |

## 运行

在仓库根目录使用 Python 3.11 及以上版本，无需安装运行依赖：

```sh
python3 -m volleyball_match_observatory touch-evidence examples/touch-evidence.json
python3 -m volleyball_match_observatory touch-evidence examples/touch-evidence.json --sqlite facts.sqlite
python3 -m unittest discover -s tests -v
```

每个输入文件包含 `records` 数组，记录的 `id` 在批内唯一。各数据链校验自己的业务字段，输出按 `fact_id` 标识的事实。起止范围若无另行说明均为左闭右开；日期、深度、金额和持续时间等单位由字段标明。

加上 `--sqlite` 时，`runs` 表保存规范化的来源 JSON 与 SHA-256，`facts` 表保存同一批次的事实。原样重放不新增事实；写入失败回滚整批。既有数据库不会被自动改写为不同版本的处理结果。JSON 接口和入库只是数据处理的运行入口，不是仓库的业务主体。
