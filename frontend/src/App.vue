<script setup>
// Day 13：页面四个模块 —— Top10 榜单、大厂/小厂对比、门槛分布、数据来源脚注
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const API = 'http://127.0.0.1:8000'

const top = ref([])
const big = ref([])
const small = ref([])
const levelDist = ref([])
const meta = ref(null)
const loading = ref(true)
const error = ref('')

const topEl = ref(null)
const bigEl = ref(null)
const smallEl = ref(null)
const levelEl = ref(null)

function init(el) {
  if (!el) return null
  return echarts.getInstanceByDom(el) || echarts.init(el)
}

// 横向柱状图
function hbar(el, names, values, color, xName, unit = '') {
  const c = init(el)
  if (!c) return
  c.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 130, right: 56, top: 10, bottom: 30 },
    xAxis: { type: 'value', name: xName },
    yAxis: { type: 'category', data: names, inverse: true },
    series: [
      {
        type: 'bar',
        data: values,
        barMaxWidth: 18,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', formatter: `{c}${unit}` },
      },
    ],
  })
}

function render() {
  hbar(topEl.value, top.value.map((s) => s.name), top.value.map((s) => s.count), '#409eff', '出现岗位数')
  hbar(bigEl.value, big.value.map((s) => s.name), big.value.map((s) => +(s.rate * 100).toFixed(1)), '#f56c6c', '出现率', '%')
  hbar(smallEl.value, small.value.map((s) => s.name), small.value.map((s) => +(s.rate * 100).toFixed(1)), '#67c23a', '出现率', '%')

  const c = init(levelEl.value)
  if (c) {
    c.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c}（{d}%）' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['40%', '65%'],
          data: levelDist.value.map((d) => ({ name: d.level, value: d.count })),
        },
      ],
    })
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [t, c, l, m] = await Promise.all([
      fetch(`${API}/skills/top?limit=10&tier=all`),
      fetch(`${API}/skills/compare?limit=10`),
      fetch(`${API}/skills/level`),
      fetch(`${API}/meta`),
    ])
    top.value = (await t.json()).data
    const cmp = (await c.json()).data
    big.value = cmp['大厂'] || []
    small.value = cmp['小厂'] || []
    levelDist.value = (await l.json()).data.distribution || []
    meta.value = (await m.json()).data
    await nextTick()
    render()
  } catch (e) {
    error.value = '加载失败：' + e.message + '（后端起了吗？）'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="container">
    <h1>AI 岗位技能雷达</h1>
    <p v-if="loading">加载中…</p>
    <p v-if="error" class="error">{{ error }}</p>

    <section v-show="top.length">
      <h2>技能 Top 10</h2>
      <div ref="topEl" class="chart"></div>
      <table>
        <thead>
          <tr><th>排名</th><th>技能</th><th>出现岗位数</th><th>出现率</th></tr>
        </thead>
        <tbody>
          <tr v-for="(s, i) in top" :key="s.name">
            <td>{{ i + 1 }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.count }}</td>
            <td>{{ (s.rate * 100).toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-show="big.length || small.length">
      <h2>大厂 vs 小厂</h2>
      <div class="grid">
        <div>
          <h3>大厂 Top 10</h3>
          <div ref="bigEl" class="chart"></div>
        </div>
        <div>
          <h3>小厂 Top 10</h3>
          <div ref="smallEl" class="chart"></div>
        </div>
      </div>
    </section>

    <section v-show="levelDist.length">
      <h2>门槛分布</h2>
      <div ref="levelEl" class="chart pie"></div>
    </section>

    <footer v-if="meta">
      <p>
        数据来源：{{ meta.source }} ｜ 样本：{{ meta.jobs_count }} 条 JD / {{ meta.skills_count }} 条技能
        ｜ 数据时点：{{ (meta.crawled_at || '').slice(0, 10) }}
      </p>
    </footer>
  </div>
</template>

<style>
body {
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f6f8;
  margin: 0;
}
.container {
  max-width: 960px;
  margin: 40px auto;
  padding: 24px 32px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
h1 {
  font-size: 24px;
  margin: 0 0 8px;
}
h2 {
  font-size: 18px;
  margin: 28px 0 8px;
  border-left: 4px solid #409eff;
  padding-left: 8px;
}
h3 {
  font-size: 14px;
  color: #666;
  margin: 0 0 4px;
}
.chart {
  width: 100%;
  height: 400px;
}
.pie {
  height: 320px;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
@media (max-width: 700px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}
th,
td {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
}
th {
  color: #888;
  font-weight: 500;
  font-size: 13px;
}
footer {
  margin-top: 32px;
  padding-top: 12px;
  border-top: 1px solid #eee;
  color: #999;
  font-size: 13px;
}
.error {
  color: #d33;
}
</style>
