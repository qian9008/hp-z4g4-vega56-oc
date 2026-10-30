# Radeon RX Vega PowerPlay Table 详细分析报告

本报告对从显卡 VBIOS 提取的 PowerPlay Table（[bios.pp_table](file:///D:/Users/Desktop/bios.pp_table)）进行了核心参数分析。该表格式为 **Vega 10 (SoftPP v8.1)**，适用于 RX Vega 56 / 64 核心。

---

## 1. 核心频率与电压依赖表 (Gfxclk & Vddc)
核心共有 8 个电源状态（P-State 0 ~ 7），频率与核心电压（Vddc）的映射关系如下：

| P-State | 原始频率 (GfxClk) | 修改后频率 | 电压索引 | 原始电压值 | 修改后电压值 | 说明 / 优化结果 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **D-State 0** | 852 MHz | **852 MHz** | Index 0 | 800 mV | **750 mV** | 极致降温静音锁频 |
| **D-State 1** | 991 MHz | **852 MHz** | Index 1 | 900 mV | **750 mV** | 极致降温静音锁频 |
| **D-State 2** | 1138 MHz | **852 MHz** | Index 2 | 950 mV | **750 mV** | 极致降温静音锁频 |
| **D-State 3** | 1269 MHz | **852 MHz** | Index 3 | 1000 mV | **750 mV** | 极致降温静音锁频 |
| **D-State 4** | 1312 MHz | **852 MHz** | Index 4 | 1050 mV | **750 mV** | 极致降温静音锁频 |
| **D-State 5** | 1474 MHz | **852 MHz** | Index 5 | 1100 mV | **750 mV** | 极致降温静音锁频 |
| **D-State 6** | 1538 MHz | **852 MHz** | Index 6 | 1150 mV | **750 mV** | 极致降温静音锁频 |
| **D-State 7** | 1590 MHz | **852 MHz** | Index 7 | 1200 mV | **750 mV** | 极致降温静音锁频 |





> [!NOTE]
> **关于您在管理器中看到的 26 MHz / 35 MHz 极低频率**：
> 这个依赖表列出的是**活跃状态（P-States）**下的基本映射关系，其中 P-State 0 (852 MHz) 是日常渲染的最基础活跃状态。
> 当显卡处于完全闲置（零负载或显示器无变化）时，GPU 会触发**硬件深睡眠机制（Deep Sleep / GFX Off）**。此时，SMU（电源管理协处理器）会通过时钟分频器（Clock Divider）将核心主频强行分频降低到 26 MHz 或 35 MHz 左右以极力省电。这属于底层的固件自主节能行为，不属于常规的可调 P-State 档位，因此不会写在 PowerPlay 依赖表中。

> [!TIP]
> **超频/降压优化建议**：
> Vega 10 核心的默认电压偏高（最大达 1.2V，发热大）。通过上述修改，我们已经成功屏蔽了 P5 - P7 对应的高热高耗状态，同时在所有状态下都实现了大幅度降压，能有效避免日常负载和轻度娱乐时显卡温度失控。

---

## 2. 显存频率与电压 (Mclk & Vddmem)
显存（HBM2）共有 4 个电源状态（P-State 0 ~ 3），我们优化了最高状态（State 3）的关联电压下限，以解除核心强制升压的限制：

| P-State | 原始显存频率 | 修改后显存频率 | 对应电压索引 (VddInd) | 原始电压下限 | 修改后电压下限 | HBM控制器物理电压 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **State 0** | 167 MHz | 167 MHz | Index 0 | 800 mV | 800 mV | 1250 mV (1.25V) |
| **State 1** | 500 MHz | 500 MHz | Index 0 | 800 mV | 800 mV | 1250 mV (1.25V) |
| **State 2** | 700 MHz | 700 MHz | Index 1 | 900 mV | 900 mV | 1250 mV (1.25V) |
| **State 3** | 800 MHz | **500 MHz** | Index 0 (修改后) | 950 mV | **800 mV** | 1250 mV (1.25V) |

- **显存降频节能**：已将 State 3 频率从原厂 800 MHz 限制在 **500 MHz**（等效 1000 Gbps），以最大化日常多屏和待机能效。
- **解锁核心电压地板 (Vddc Floor)**：已将 State 3 绑定的核心电压限制从原厂 950 mV 压回 **800 mV**。即便显存因多屏强制激活 State 3，GPU 核心也无需跟着升压，能省下数十瓦的静态漏电和发热。
- **显存控制器物理电压 (Vddmem)**：固定在 1250 mV (1.25V) 保持物理层稳定。

---

## 3. 功耗限制与温度目标 (PowerTune Table)
显卡的功耗控制与保护机制如下：

- **整卡默认功耗上限 (SocketPowerLimit)**：**82 W** *(已从原厂 165 W 限制降低了 50%)*
- **功耗调节范围 (PowerControlLimit)**：**±50%**
  - 这意味着在系统控制面板中，玩家可以将功耗墙拉高至多 50%（最大约 **123 W**）。
- **安全关机温度 (SoftwareShutdownTemp)**：**89 °C** （核心边缘温度达到 89°C 会触发硬件保护关机）。
- **热点最高温度限制 (TemperatureLimitHotSpot)**：**105 °C** （热点温度达到此上限时显卡会开始降频保护）。
- **HBM2 显存最高温度限制 (TemperatureLimitHBM)**：**95 °C**。
- **VRM 供电最高温度限制 (TemperatureLimitVrSoc / VrMem)**：**115 °C**。

---

## 4. 风扇控制 (Fan Table)
- **目标温度 (TargetTemperature)**：**75 °C**（风扇温控算法将尽量使核心温度维持在 75°C 以下）。
- **风扇噪音转速限制 (FanAcousticLimitRpm)**：**2400 RPM**（温控系统在非极度高温下，风扇转速不会超过 2400 转/分，以控制噪音）。
- **风扇物理转速最大上限 (FanMaxRPM / ThrottlingRPM)**：**2400 RPM**。
- **零转速低温起停 (EnableZeroRPM)**：**0 (已禁用)**。当前配置中，风扇在低温下不会完全停转。

---

## 5. 超频上限 (OD Limit)
- **最大核心超频频率上限 (MaxODEngineClock)**：**2400 MHz**（即使使用 Wattman 或三方工具，核心频率调节的软上限为 2400 MHz）。
- **最大显存超频频率上限 (MaxODMemoryClock)**：**1500 MHz**。
