#!/bin/bash
# 持续监控 GPU 显存频率变化，每 2 秒采样一次
# 用途：关闭视频播放器后运行此脚本，观察频率变化曲线
echo "=== GPU 频率监控 (Ctrl+C 停止) ==="
echo "时间        | Core(MHz) | Mem(MHz) | GPU活率(%)"
echo "------------|-----------|----------|----------"
while true; do
    # 从 ioreg 提取频率和活动率
    DATA=$(ioreg -l -c IOService -r -d 6 2>/dev/null | grep -oE "\"Core Clock\(MHz\)\"=[0-9]+|\"Memory Clock\(MHz\)\"=[0-9]+|\"GPU Activity\(%\)\"=[0-9]+" | head -3)
    CORE=$(echo "$DATA" | grep "Core Clock" | grep -oE "[0-9]+")
    MEM=$(echo "$DATA" | grep "Memory Clock" | grep -oE "[0-9]+")
    ACT=$(echo "$DATA" | grep "GPU Activity" | grep -oE "[0-9]+")
    echo "$(date '+%H:%M:%S')  | ${CORE:-?}       | ${MEM:-?}      | ${ACT:-?}"
    sleep 2
done
