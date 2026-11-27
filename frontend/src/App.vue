<script setup>
// Day 11：从后端拉取技能 Top 榜单并显示
import { ref, onMounted } from 'vue'

const skills = ref([])
const loading = ref(false)
const error = ref('')

async function loadSkills() {
  loading.value = true
  error.value = ''
  try {
    // 本地后端地址；部署时（Day 14）会换成公网地址
    const res = await fetch('http://127.0.0.1:8000/skills/top?limit=10&tier=all')
    const json = await res.json()
    skills.value = json.data
  } catch (e) {
    error.value = '加载失败：' + e.message + '（后端起了吗？）'
  } finally {
    loading.value = false
  }
}

onMounted(loadSkills)
</script>

<template>
  <div class="container">
    <h1>AI 岗位技能雷达</h1>
    <p v-if="loading">加载中…</p>
    <p v-if="error" class="error">{{ error }}</p>
    <table v-if="skills.length">
      <thead>
        <tr>
          <th>排名</th>
          <th>技能</th>
          <th>出现岗位数</th>
          <th>出现率</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(s, i) in skills" :key="s.name">
          <td>{{ i + 1 }}</td>
          <td>{{ s.name }}</td>
          <td>{{ s.count }}</td>
          <td>{{ (s.rate * 100).toFixed(1) }}%</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style>
body {
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f6f8;
  margin: 0;
}
.container {
  max-width: 640px;
  margin: 40px auto;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
h1 {
  font-size: 22px;
  margin: 0 0 16px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
}
th {
  color: #888;
  font-weight: 500;
  font-size: 13px;
}
.error {
  color: #d33;
}
</style>
