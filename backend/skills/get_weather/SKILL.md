---
name: get_weather
description: 获取指定城市的实时天气信息
---

# 获取天气信息 (get_weather)

## 功能说明

获取指定城市的实时天气信息，包括温度、湿度、天气状况等。

## 使用步骤

### 方法一：使用 wttr.in API（推荐，无需 API Key）

1. 使用 `fetch_url` 工具访问 wttr.in 的 API：

```
fetch_url("https://wttr.in/{城市名}?format=j1&lang=zh")
```

2. 解析返回的 JSON 数据，提取关键天气信息。

### 方法二：使用 Python 脚本

1. 使用 `python_repl` 工具执行以下代码模板：

```python
import json
import urllib.request

city = "北京"  # 替换为目标城市
url = f"https://wttr.in/{city}?format=j1&lang=zh"
req = urllib.request.Request(url, headers={"User-Agent": "MiniOpenClaw/1.0"})
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read().decode())

current = data["current_condition"][0]
print(f"城市: {city}")
print(f"温度: {current['temp_C']}°C (体感 {current['FeelsLikeC']}°C)")
print(f"天气: {current['lang_zh'][0]['value']}")
print(f"湿度: {current['humidity']}%")
print(f"风速: {current['windspeedKmph']} km/h")
```

## 输出格式

请以友好的自然语言格式向用户展示天气信息，例如：

> 🌤️ **北京当前天气**
> - 温度：25°C（体感 27°C）
> - 天气：晴
> - 湿度：45%
> - 风速：12 km/h

## 注意事项

- 城市名支持中文和英文
- 如果 wttr.in 访问失败，告知用户可能是网络问题
- 不要缓存天气数据，每次都应获取最新信息
