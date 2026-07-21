#!/bin/bash
# 诊断脚本：关闭视频播放器后运行，收集 GPU 电源状态信息
# 用途：找出退出 UVD 后 MCLK 锁死 800MHz 的原因
echo "========================================"
echo "GPU 诊断 - 退出视频后状态"
echo "时间: $(date)"
echo "========================================"
echo ""

echo "=== 1. 当前频率 ==="
ioreg -l -c IOService -r -d 6 2>/dev/null | grep -oE "\"Core Clock\(MHz\)\"=[0-9]+|\"Memory Clock\(MHz\)\"=[0-9]+|\"GPU Activity\(%\)\"=[0-9]+"
echo ""

echo "=== 2. PP_ 电源管理属性 (运行时值) ==="
ioreg -l 2>/dev/null | grep -E "\"PP_(DisableULV|GfxOffControl|DisableDIDT|Falcon_QuickTransition|WorkLoadPolicyMask|EnableUploadFirmware)\""
echo ""

echo "=== 3. GPU PCI 电源状态 (D0=工作, D3=休眠) ==="
ioreg -l -c IOPCIDevice -r 2>/dev/null | grep -B3 "CurrentPowerState.*MaxPowerState" | grep -E "CurrentPowerState|MaxPowerState|ChildProxyPowerState|device-id"
echo ""

echo "=== 4. AGPM 当前状态 ==="
ioreg -l -c AGPM -r 2>/dev/null | grep -iE "CurrentPowerState|MinPower|MaxPower|Heuristic|control-id|GfxOff"
echo ""

echo "=== 5. UVD/VCE 相关进程 ==="
ps aux 2>/dev/null | grep -iE "VTDecoder|VideoToolbox|avplayer|VCE|UVD|hwdecode|mpv|IINA|VLC" | grep -v grep
echo ""

echo "=== 6. GPU 显存带宽/使用情况 ==="
ioreg -l -c ATYFramebuffer -r 2>/dev/null | grep -iE "Memory Clock|Core Clock|Bandwidth|MemClk|Sclk|Mclk" | head -10
echo ""

echo "=== 7. 显示器/显示管线状态 ==="
ioreg -l -c IOFramebuffer -r 2>/dev/null | grep -iE "DisplayMode|PixelClock|RefreshRate|Timing|Bandwidth|LinkRate|LaneCount" | head -10
echo ""

echo "=== 8. GPU DPM 相关 ==="
ioreg -l 2>/dev/null | grep -iE "\"ATY,MCLK\"|\"ATY,SCLK\"|\"ATY,MaxMClk|\"ATY,MaxSClk|DPMState|PowerState|perfstate" | head -10
echo ""

echo "=== 9. 完整 GPU 节点关键属性 ==="
ioreg -l -c IOService -r -d 4 2>/dev/null | grep -E "\"(ATY|MCLK|SCLK|Mem|Core|GPU|Power|DPM|Clock|Freq|State|Activity)\"" | grep -iv "class\|IOService\|IOPCIDevice\|IOACPI\|Apple" | head -20
echo ""

echo "=== 10. 是否有 VTBDecoder 进程持有 GPU ==="
ioreg -l 2>/dev/null | grep -i "VTBDecoder\|VideoToolbox\|IOSurface\|GPUPath\|OpenCL\|Metal" | head -10
echo ""

echo "========================================"
echo "诊断完成。请将以上输出发给我。"
echo "========================================"
